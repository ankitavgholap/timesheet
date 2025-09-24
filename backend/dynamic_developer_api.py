# backend/dynamic_developer_api.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
import os
import logging
from database import get_db
from models import DiscoveredDeveloper, ActivityRecord
from config import Config
from developer_discovery import DeveloperDiscovery
from dynamic_activitywatch_client import DynamicActivityWatchClient
import socket

logger = logging.getLogger(__name__)
router = APIRouter()

class EnvironmentBasedDeveloperService:
    """Service to handle developer list based on environment"""
    
    def __init__(self, db: Session):
        self.db = db
        self.discovery = DeveloperDiscovery(db)
        
    def get_developers_list(self, scan_network: bool = False, 
                           scan_local: bool = True, 
                           scan_database: bool = True,
                           force_refresh: bool = False) -> Dict:
        """Get developers list based on environment (local vs production)"""
        
        if Config.is_local():
            return self._get_local_developer_only()
        else:
            return self._get_all_developers(scan_network, scan_local, scan_database, force_refresh)
    
    def _get_local_developer_only(self) -> Dict:
        """Return only the current local developer"""
        try:
            # Get local machine info
            local_hostname = socket.gethostname()
            local_developer_name = Config.LOCAL_DEVELOPER_NAME or local_hostname
            
            # Check if ActivityWatch is running locally
            local_instances = self.discovery.discover_local_instances()
            
            developers = []
            
            if local_instances:
                # ActivityWatch is running - use live data
                for instance in local_instances:
                    developers.append({
                        "id": f"local_{instance['port']}",
                        "name": local_developer_name,
                        "hostname": local_hostname,
                        "host": instance['host'],
                        "port": instance['port'],
                        "status": "online",
                        "source": "local",
                        "description": f"Local ActivityWatch instance",
                        "device_id": instance.get('device_id', f"{local_hostname}_{instance['port']}"),
                        "activity_count": self._get_activity_count(local_developer_name),
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                        "version": instance.get('version', 'unknown'),
                        "bucket_count": instance.get('bucket_count', 0)
                    })
            else:
                # No ActivityWatch running - check database for historical data
                db_activity_count = self._get_activity_count(local_developer_name)
                
                if db_activity_count > 0:
                    # Has historical data
                    last_activity = self._get_last_activity_time(local_developer_name)
                    developers.append({
                        "id": f"local_db_{local_hostname}",
                        "name": local_developer_name,
                        "hostname": local_hostname,
                        "host": "localhost",
                        "port": 5600,
                        "status": "database_only",
                        "source": "database",
                        "description": f"Historical data for {local_developer_name}",
                        "device_id": local_hostname,
                        "activity_count": db_activity_count,
                        "last_seen": last_activity.isoformat() if last_activity else None,
                        "version": "database",
                        "bucket_count": 0
                    })
                else:
                    # No data at all - create placeholder
                    developers.append({
                        "id": f"local_new_{local_hostname}",
                        "name": local_developer_name,
                        "hostname": local_hostname,
                        "host": "localhost",
                        "port": 5600,
                        "status": "offline",
                        "source": "local",
                        "description": f"Local developer (no data yet)",
                        "device_id": local_hostname,
                        "activity_count": 0,
                        "last_seen": None,
                        "version": "unknown",
                        "bucket_count": 0
                    })
            
            return {
                "developers": developers,
                "environment": "local",
                "total_count": len(developers),
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "local_developer": local_developer_name
            }
            
        except Exception as e:
            logger.error(f"Error getting local developer: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting local developer: {str(e)}")
    
    def _get_all_developers(self, scan_network: bool, scan_local: bool, 
                           scan_database: bool, force_refresh: bool) -> Dict:
        """Get all developers from all sources (production mode)"""
        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_developers = self._get_cached_developers()
                if cached_developers:
                    # Refresh status for cached developers
                    updated_developers = self.discovery.refresh_developer_status(cached_developers)
                    self._update_developer_cache(updated_developers)
                    
                    return {
                        "developers": updated_developers,
                        "environment": "production", 
                        "total_count": len(updated_developers),
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "from_cache": True
                    }
            
            # Full discovery
            logger.info("Performing full developer discovery...")
            discovered_developers = self.discovery.discover_all_developers(
                scan_network=scan_network,
                scan_local=scan_local, 
                scan_database=scan_database
            )
            
            # Enhance with activity counts
            for dev in discovered_developers:
                dev['activity_count'] = self._get_activity_count(dev.get('name') or dev['id'])
                if not dev.get('last_seen'):
                    dev['last_seen'] = self._get_last_activity_time(dev.get('name') or dev['id'])
                    if dev['last_seen']:
                        dev['last_seen'] = dev['last_seen'].isoformat()
            
            # Cache the results
            self._update_developer_cache(discovered_developers)
            
            return {
                "developers": discovered_developers,
                "environment": "production",
                "total_count": len(discovered_developers),
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "from_cache": False
            }
            
        except Exception as e:
            logger.error(f"Error discovering all developers: {e}")
            raise HTTPException(status_code=500, detail=f"Error discovering developers: {str(e)}")
    
    def _get_activity_count(self, developer_name: str) -> int:
        """Get activity count for a developer"""
        try:
            from sqlalchemy import func, or_
            
            count = self.db.query(func.count(ActivityRecord.id)).filter(
                or_(
                    ActivityRecord.developer_name == developer_name,
                    ActivityRecord.developer_id == developer_name
                )
            ).scalar()
            
            return count or 0
        except Exception as e:
            logger.warning(f"Error getting activity count for {developer_name}: {e}")
            return 0
    
    def _get_last_activity_time(self, developer_name: str) -> Optional[datetime]:
        """Get last activity time for a developer"""
        try:
            from sqlalchemy import or_, desc
            
            last_record = self.db.query(ActivityRecord.created_at).filter(
                or_(
                    ActivityRecord.developer_name == developer_name,
                    ActivityRecord.developer_id == developer_name
                )
            ).order_by(desc(ActivityRecord.created_at)).first()
            
            return last_record[0] if last_record else None
        except Exception as e:
            logger.warning(f"Error getting last activity time for {developer_name}: {e}")
            return None
    
    def _get_cached_developers(self) -> List[Dict]:
        """Get cached developers from database"""
        try:
            cached = self.db.query(DiscoveredDeveloper).filter(
                DiscoveredDeveloper.is_active == True,
                DiscoveredDeveloper.discovered_at > datetime.now() - timedelta(hours=1)  # Cache for 1 hour
            ).all()
            
            return [{
                "id": dev.id,
                "name": dev.name,
                "hostname": dev.hostname,
                "host": dev.host,
                "port": dev.port,
                "status": dev.status,
                "source": dev.source,
                "description": dev.description,
                "device_id": dev.device_id,
                "activity_count": dev.activity_count,
                "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
                "version": dev.version,
                "bucket_count": dev.bucket_count
            } for dev in cached]
            
        except Exception as e:
            logger.warning(f"Error getting cached developers: {e}")
            return []
    
    def _update_developer_cache(self, developers: List[Dict]):
        """Update developer cache in database"""
        try:
            # Mark all as inactive first
            self.db.query(DiscoveredDeveloper).update({
                DiscoveredDeveloper.is_active: False
            })
            
            # Insert or update discovered developers
            for dev in developers:
                existing = self.db.query(DiscoveredDeveloper).filter_by(id=dev['id']).first()
                
                if existing:
                    # Update existing
                    existing.name = dev['name']
                    existing.hostname = dev['hostname']
                    existing.host = dev['host']
                    existing.port = dev['port']
                    existing.status = dev['status']
                    existing.description = dev['description']
                    existing.activity_count = dev['activity_count']
                    existing.last_seen = datetime.fromisoformat(dev['last_seen'].replace('Z', '+00:00')) if dev['last_seen'] else None
                    existing.is_active = True
                    existing.updated_at = datetime.now()
                else:
                    # Create new
                    new_dev = DiscoveredDeveloper(
                        id=dev['id'],
                        name=dev['name'],
                        hostname=dev['hostname'],
                        host=dev['host'],
                        port=dev['port'],
                        device_id=dev.get('device_id', dev['id']),
                        status=dev['status'],
                        source=dev['source'],
                        description=dev['description'],
                        version=dev.get('version', 'unknown'),
                        bucket_count=dev.get('bucket_count', 0),
                        activity_count=dev['activity_count'],
                        last_seen=datetime.fromisoformat(dev['last_seen'].replace('Z', '+00:00')) if dev['last_seen'] else None,
                        is_active=True
                    )
                    self.db.add(new_dev)
            
            self.db.commit()
            logger.info(f"Updated cache with {len(developers)} developers")
            
        except Exception as e:
            logger.error(f"Error updating developer cache: {e}")
            self.db.rollback()

# API Endpoints
@router.get("/developers")
async def get_developers_list(
    scan_network: bool = False,
    scan_local: bool = True,
    scan_database: bool = True,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """Get developers list based on environment"""
    service = EnvironmentBasedDeveloperService(db)
    return service.get_developers_list(scan_network, scan_local, scan_database, force_refresh)

@router.get("/discover-developers")  
async def discover_developers(
    scan_network: bool = False,
    scan_local: bool = True,
    scan_database: bool = True,
    force_refresh: bool = True,
    db: Session = Depends(get_db)
):
    """Discover developers (force refresh)"""
    service = EnvironmentBasedDeveloperService(db)
    return service.get_developers_list(scan_network, scan_local, scan_database, force_refresh)

@router.get("/developers-status")
async def refresh_developers_status(db: Session = Depends(get_db)):
    """Refresh status of all cached developers"""
    service = EnvironmentBasedDeveloperService(db)
    
    # Get cached developers and refresh their status
    cached_devs = service._get_cached_developers()
    if not cached_devs:
        # No cache, return current environment-based list
        return service.get_developers_list()
    
    # Refresh status
    discovery = DeveloperDiscovery(db)
    updated_devs = discovery.refresh_developer_status(cached_devs)
    service._update_developer_cache(updated_devs)
    
    return {
        "developers_status": updated_devs,
        "environment": "local" if Config.is_local() else "production",
        "total_count": len(updated_devs),
        "refreshed_at": datetime.now(timezone.utc).isoformat()
    }

@router.get("/activity-data/{developer_id}")
async def get_developer_activity_data(
    developer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get activity data for a specific developer"""
    try:
        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        # Get developer info
        service = EnvironmentBasedDeveloperService(db)
        developers_result = service.get_developers_list()
        
        developer = next((d for d in developers_result['developers'] if d['id'] == developer_id), None)
        if not developer:
            raise HTTPException(status_code=404, detail="Developer not found")
        
        activity_data = []
        data_source = "database"
        
        # Try to get live data if developer is online
        if developer['status'] == 'online':
            try:
                client = DynamicActivityWatchClient(developer)
                if client.test_connection():
                    activity_data = client.get_activity_data(start, end)
                    data_source = "activitywatch"
                    logger.info(f"Retrieved live data for {developer['name']}: {len(activity_data)} activities")
                    
                    # Store in database for caching
                    from safe_activity_caching import safe_create_activity_record
                    for activity in activity_data:
                        try:
                            safe_create_activity_record(db, activity, user_id=1)  # Default user
                        except Exception as e:
                            logger.warning(f"Failed to cache activity: {e}")
                            
            except Exception as e:
                logger.warning(f"Failed to get live data for {developer['name']}: {e}")
        
        # Fallback to database if no live data
        if not activity_data:
            from sqlalchemy import and_, or_
            
            db_records = db.query(ActivityRecord).filter(
                and_(
                    or_(
                        ActivityRecord.developer_id == developer_id,
                        ActivityRecord.developer_name == developer['name'],
                        ActivityRecord.device_id == developer.get('device_id')
                    ),
                    ActivityRecord.activity_timestamp >= start,
                    ActivityRecord.activity_timestamp <= end
                )
            ).order_by(ActivityRecord.duration.desc()).limit(1000).all()
            
            activity_data = [{
                "developer_id": record.developer_id,
                "developer_name": record.developer_name,
                "application_name": record.application_name,
                "window_title": record.window_title,
                "duration": record.duration,
                "timestamp": record.activity_timestamp.isoformat() if record.activity_timestamp else None,
                "category": record.category,
                "detailed_activity": record.detailed_activity,
                "url": record.url,
                "file_path": record.file_path
            } for record in db_records]
            
            data_source = "database"
            logger.info(f"Retrieved database data for {developer['name']}: {len(activity_data)} activities")
        
        return {
            "data": activity_data,
            "developer": developer,
            "data_source": data_source,
            "total_time": sum(item["duration"] for item in activity_data),
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "activity_count": len(activity_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting activity data for {developer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting activity data: {str(e)}")
