from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import json
import hashlib
import os
from pydantic import BaseModel
from database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ActivityWatchEvent(BaseModel):
    timestamp: str
    duration: float
    data: Dict[str, Any]

def validate_stateless_token(developer_id: str, provided_token: str) -> bool:
    """Validate token without database lookup - uses master secret"""
    master_secret = os.getenv("MASTER_SECRET", "your-master-secret-for-token-generation")
    
    # Recreate the expected token using same algorithm as generator
    token_input = f"{developer_id}:{master_secret}:{datetime.now().year}"
    token_hash = hashlib.sha256(token_input.encode()).hexdigest()
    
    # Convert to URL-safe format
    import base64
    token_bytes = bytes.fromhex(token_hash[:48])
    expected_token = base64.urlsafe_b64encode(token_bytes).decode().rstrip('=')
    
    return expected_token == provided_token

def categorize_application(app_name: str, window_title: str = "") -> str:
    """Categorize application based on name and window title"""
    if not app_name:
        return 'other'
    
    app_name_lower = app_name.lower()
    window_title_lower = window_title.lower() if window_title else ""
    
    # Browsers
    if any(browser in app_name_lower for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']):
        return 'browser'
    
    # IDEs and Code Editors
    if any(ide in app_name_lower for ide in ['vscode', 'visual studio', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs', 'notepad++', 'cursor', 'code']):
        return 'development'
    
    # Database Tools
    if any(db in app_name_lower for db in ['datagrip', 'pgadmin', 'mysql', 'dbeaver', 'navicat', 'sqlserver', 'oracle']):
        return 'database'
    
    # Productivity
    if any(prod in app_name_lower for prod in ['word', 'excel', 'powerpoint', 'outlook', 'teams', 'slack', 'discord', 'zoom', 'notion', 'obsidian', 'postman']):
        return 'productivity'
    
    # Media
    if any(media in app_name_lower for media in ['spotify', 'youtube', 'vlc', 'media player', 'netflix', 'twitch']):
        return 'entertainment'
    
    # System processes
    if any(system in app_name_lower for system in ['explorer', 'finder', 'terminal', 'cmd', 'powershell', 'task manager', 'lock', 'dwm', 'winlogon']):
        return 'system'
    
    return 'other'

def extract_project_info(window_title: str, app_name: str, url: str = None) -> dict:
    """Extract project information from window title, app name, and URL"""
    project_info = {
        'project_name': None,
        'project_type': 'Work',
        'file_path': None,
        'url': url,
        'detailed_activity': None
    }
    
    if not window_title and not app_name:
        return project_info
    
    app_name_lower = app_name.lower() if app_name else ""
    window_title_lower = window_title.lower() if window_title else ""
    
    # IDE Project Detection
    if any(ide in app_name_lower for ide in ['cursor', 'vscode', 'code', 'pycharm', 'intellij']):
        if ' - ' in window_title:
            parts = window_title.split(' - ')
            if len(parts) >= 2:
                filename = parts[0].strip()
                project = parts[1].strip()
                
                project_info.update({
                    'project_name': project,
                    'project_type': 'Development',
                    'file_path': f"{project}/{filename}" if '.' in filename else project,
                    'detailed_activity': f"Coding: {filename} in {project}"
                })
                return project_info
    
    # Browser Project Detection
    elif any(browser in app_name_lower for browser in ['chrome', 'firefox', 'edge', 'safari']):
        if url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                
                # Localhost development
                if 'localhost' in domain or '127.0.0.1' in domain:
                    project_info.update({
                        'project_name': f"localhost:{parsed.port or '3000'}",
                        'project_type': 'Web Development',
                        'detailed_activity': f"Local Development: {window_title}"
                    })
                    return project_info
                
                # Work-related domains
                work_domains = ['github.com', 'stackoverflow.com', 'docs.', 'api.', 'developer.', 'console.']
                if any(work_domain in domain for work_domain in work_domains):
                    project_info.update({
                        'project_name': domain,
                        'project_type': 'Web Research',
                        'detailed_activity': f"Research: {window_title}"
                    })
                    return project_info
                
            except Exception:
                pass
        
        # Fallback to window title
        if ' - ' in window_title:
            page_title = window_title.split(' - ')[0].strip()
            project_info.update({
                'project_name': page_title,
                'project_type': 'Web Browsing',
                'detailed_activity': f"Browsing: {page_title}"
            })
            return project_info
    
    # Default fallback
    clean_app_name = app_name.replace('.exe', '') if app_name else 'Unknown'
    project_info.update({
        'project_name': clean_app_name,
        'project_type': 'Work',
        'detailed_activity': f"{clean_app_name}: {window_title}" if window_title else clean_app_name
    })
    
    return project_info

@router.post("/activitywatch/webhook")
async def receive_activitywatch_webhook_stateless(
    request: Request,
    developer_id: str = Header(..., alias="Developer-ID"),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Receive ActivityWatch data via webhook - stateless token validation"""
    
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    # Validate token using stateless method (no database lookup)
    if not validate_stateless_token(developer_id, token):
        logger.warning(f"Invalid token for developer {developer_id}")
        raise HTTPException(status_code=401, detail="Invalid developer or token")
    
    logger.info(f"Received ActivityWatch webhook from {developer_id}")
    
    try:
        # Get raw JSON data
        webhook_data = await request.json()
        
        processed_activities = 0
        
        # Process each bucket
        for bucket_name, bucket_data in webhook_data.items():
            if isinstance(bucket_data, list):
                # Process events
                for event in bucket_data:
                    if not isinstance(event, dict):
                        continue
                    
                    # Extract event data
                    timestamp_str = event.get('timestamp')
                    duration = event.get('duration', 0)
                    data = event.get('data', {})
                    
                    if not timestamp_str or duration < 5:  # Skip very short activities
                        continue
                    
                    try:
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        # Extract activity information
                        app_name = data.get('app') or data.get('application', 'Unknown')
                        window_title = data.get('title', '')
                        url = data.get('url', None)
                        
                        # Skip if no meaningful data
                        if not app_name or app_name == 'Unknown':
                            continue
                        
                        # Categorize and extract project info
                        category = categorize_application(app_name, window_title)
                        project_info = extract_project_info(window_title, app_name, url)
                        
                        # Check for duplicates to avoid storing same activity twice
                        from models import ActivityRecord
                        existing = db.query(ActivityRecord).filter(
                            ActivityRecord.developer_id == developer_id,
                            ActivityRecord.timestamp == timestamp,
                            ActivityRecord.application_name == app_name,
                            ActivityRecord.duration == duration
                        ).first()
                        
                        if existing:
                            continue  # Skip duplicates
                        
                        # Create activity record (store developer_id as string, no FK)
                        activity_record = ActivityRecord(
                            developer_id=developer_id,  # Store as string identifier
                            application_name=app_name,
                            window_title=window_title,
                            url=url,
                            file_path=project_info['file_path'],
                            category=category,
                            duration=duration,
                            timestamp=timestamp,
                            project_name=project_info['project_name'],
                            project_type=project_info['project_type'],
                            detailed_activity=project_info['detailed_activity']
                        )
                        
                        db.add(activity_record)
                        processed_activities += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Successfully processed {processed_activities} activities from {developer_id}")
        
        return {
            "status": "success",
            "message": f"Processed {processed_activities} activities",
            "developer_id": developer_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing ActivityWatch webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@router.get("/activitywatch/validate-token")
async def validate_token_endpoint(
    developer_id: str,
    token: str
):
    """Test endpoint to validate a token (for debugging)"""
    is_valid = validate_stateless_token(developer_id, token)
    
    return {
        "developer_id": developer_id,
        "token_valid": is_valid,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/activitywatch/developer-summary/{developer_id}")
async def get_developer_summary_stateless(
    developer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get activity summary for a developer (no user authentication required)"""
    
    # Parse dates
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end = datetime.now(timezone.utc)
    
    # Get activities for this developer (by string ID, not FK)
    from models import ActivityRecord
    activities = db.query(ActivityRecord).filter(
        ActivityRecord.developer_id == developer_id,
        ActivityRecord.timestamp >= start,
        ActivityRecord.timestamp <= end
    ).all()
    
    if not activities:
        return {
            "developer_id": developer_id,
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": {"total_activities": 0, "total_time": 0, "categories": {}, "projects": {}}
        }
    
    # Process activities into summary
    summary = process_developer_activities(activities)
    
    return {
        "developer_id": developer_id,
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "summary": summary
    }

@router.get("/activitywatch/team-summary")
async def get_team_summary_stateless(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get team-wide summary without requiring user authentication"""
    
    # Parse dates
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end = datetime.now(timezone.utc)
    
    # Get all unique developer IDs from activities
    from sqlalchemy import distinct
    from models import ActivityRecord
    developer_ids = db.query(distinct(ActivityRecord.developer_id)).filter(
        ActivityRecord.developer_id.isnot(None),
        ActivityRecord.timestamp >= start,
        ActivityRecord.timestamp <= end
    ).all()
    
    team_data = []
    total_team_time = 0
    total_team_activities = 0
    
    for (dev_id,) in developer_ids:
        if not dev_id:
            continue
        
        # Get activities for this developer
        activities = db.query(ActivityRecord).filter(
            ActivityRecord.developer_id == dev_id,
            ActivityRecord.timestamp >= start,
            ActivityRecord.timestamp <= end
        ).all()
        
        summary = process_developer_activities(activities)
        total_team_time += summary['total_time']
        total_team_activities += summary['total_activities']
        
        # Extract developer name from ID (reverse engineer from developer_id format)
        developer_name = dev_id.replace('_', ' ').title()
        if '_' in dev_id:
            # Remove hash/year suffix for display
            name_parts = dev_id.split('_')[:-1]  # Remove last part (hash/year)
            developer_name = ' '.join(name_parts).title()
        
        team_data.append({
            "developer_id": dev_id,
            "name": developer_name,
            "summary": summary
        })
    
    return {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "team_data": team_data,
        "total_developers": len(team_data),
        "team_totals": {
            "total_time": total_team_time,
            "total_time_formatted": f"{total_team_time / 3600:.2f}h",
            "total_activities": total_team_activities
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "mode": "stateless",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "ActivityWatch webhook endpoint is running (stateless mode)"
    }

def process_developer_activities(activities: List) -> Dict:
    """Process activities into summary statistics"""
    if not activities:
        return {
            "total_activities": 0,
            "total_time": 0,
            "categories": {},
            "projects": {},
            "working_hours": 0,
            "productivity_percentage": 0
        }
    
    total_time = sum(activity.duration for activity in activities)
    categories = {}
    projects = {}
    working_hours = 0
    
    for activity in activities:
        category = activity.category or 'other'
        project = activity.project_name or 'Unknown'
        duration = activity.duration
        
        # Category processing
        if category not in categories:
            categories[category] = {"count": 0, "duration": 0}
        categories[category]["count"] += 1
        categories[category]["duration"] += duration
        
        # Project processing
        if project not in projects:
            projects[project] = {"count": 0, "duration": 0, "type": activity.project_type or 'Work'}
        projects[project]["count"] += 1
        projects[project]["duration"] += duration
        
        # Calculate working hours with category weights
        category_weights = {
            'development': 1.0,
            'database': 1.0,
            'productivity': 1.0,
            'browser': 0.85,
            'other': 0.5,
            'system': 0.1,
            'entertainment': 0.0
        }
        
        weight = category_weights.get(category, 0.5)
        working_hours += duration * weight
    
    productivity_percentage = (working_hours / total_time * 100) if total_time > 0 else 0
    
    # Format for frontend
    for category_data in categories.values():
        category_data["duration_formatted"] = f"{category_data['duration'] / 3600:.2f}h"
    
    for project_data in projects.values():
        project_data["duration_formatted"] = f"{project_data['duration'] / 3600:.2f}h"
    
    return {
        "total_activities": len(activities),
        "total_time": total_time,
        "total_time_formatted": f"{total_time / 3600:.2f}h",
        "working_hours": working_hours,
        "working_hours_formatted": f"{working_hours / 3600:.2f}h",
        "productivity_percentage": round(productivity_percentage, 1),
        "categories": categories,
        "projects": projects
    }
