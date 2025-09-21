from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timezone
import models, schemas, crud
from database import get_db
from pydantic import BaseModel

router = APIRouter()

# New Pydantic models for multi-developer support
class DeveloperActivity(BaseModel):
    application_name: str
    window_title: str
    duration: float
    timestamp: str
    bucket_name: str
    developer_id: str

class ActivityDataPayload(BaseModel):
    developer_id: str
    activities: List[DeveloperActivity]
    timestamp: str

class DeveloperInfo(BaseModel):
    developer_id: str
    name: str
    email: Optional[str] = None
    active: bool = True
    last_sync: Optional[datetime] = None

# Add developer model to your models.py
class Developer(Base):
    __tablename__ = "developers"
    
    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(String, unique=True, index=True)  # Unique identifier
    name = Column(String)
    email = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    api_token = Column(String, unique=True)  # For authentication
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    activities = relationship("ActivityRecord", back_populates="developer")

# Update ActivityRecord model to include developer relationship
# Add this to your existing ActivityRecord model:
# developer_id = Column(String, ForeignKey("developers.developer_id"), nullable=True)
# developer = relationship("Developer", back_populates="activities")

@router.post("/receive-activity-data")
async def receive_activity_data(
    payload: ActivityDataPayload,
    developer_id: str = Header(..., alias="Developer-ID"),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Receive activity data from remote developer systems"""
    
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    # Verify developer and token
    developer = db.query(models.Developer).filter(
        models.Developer.developer_id == developer_id,
        models.Developer.api_token == token,
        models.Developer.active == True
    ).first()
    
    if not developer:
        raise HTTPException(status_code=401, detail="Invalid developer or token")
    
    # Process and store activities
    stored_activities = []
    
    for activity in payload.activities:
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(activity.timestamp.replace('Z', '+00:00'))
            
            # Create activity record
            activity_record = models.ActivityRecord(
                developer_id=developer.developer_id,
                application_name=activity.application_name,
                window_title=activity.window_title,
                duration=activity.duration,
                timestamp=timestamp,
                category=categorize_application(activity.application_name, activity.window_title),
                # Extract additional details
                **extract_detailed_info(activity.window_title, activity.application_name)
            )
            
            db.add(activity_record)
            stored_activities.append(activity_record)
            
        except Exception as e:
            print(f"Error processing activity: {e}")
            continue
    
    # Update developer last sync time
    developer.last_sync = datetime.now(timezone.utc)
    
    try:
        db.commit()
        
        return {
            "status": "success",
            "message": f"Stored {len(stored_activities)} activities for {developer.name}",
            "activities_count": len(stored_activities),
            "developer_id": developer_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/register-developer")
async def register_developer(
    developer_info: DeveloperInfo,
    admin_token: str = Header(..., alias="Admin-Token"),
    db: Session = Depends(get_db)
):
    """Register a new developer (admin only)"""
    
    # Verify admin token (implement your admin authentication)
    if admin_token != "your-admin-token":  # Replace with proper admin auth
        raise HTTPException(status_code=401, detail="Admin access required")
    
    # Check if developer already exists
    existing = db.query(models.Developer).filter(
        models.Developer.developer_id == developer_info.developer_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Developer already registered")
    
    # Generate API token
    import secrets
    api_token = secrets.token_urlsafe(32)
    
    # Create developer record
    developer = models.Developer(
        developer_id=developer_info.developer_id,
        name=developer_info.name,
        email=developer_info.email,
        api_token=api_token,
        active=True
    )
    
    db.add(developer)
    db.commit()
    db.refresh(developer)
    
    return {
        "status": "success",
        "developer_id": developer.developer_id,
        "api_token": api_token,
        "message": f"Developer {developer.name} registered successfully"
    }

@router.get("/developers")
async def list_developers(
    admin_token: str = Header(..., alias="Admin-Token"),
    db: Session = Depends(get_db)
):
    """List all registered developers (admin only)"""
    
    if admin_token != "your-admin-token":
        raise HTTPException(status_code=401, detail="Admin access required")
    
    developers = db.query(models.Developer).all()
    
    result = []
    for dev in developers:
        # Get recent activity count
        recent_activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.developer_id == dev.developer_id,
            models.ActivityRecord.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()
        
        result.append({
            "developer_id": dev.developer_id,
            "name": dev.name,
            "email": dev.email,
            "active": dev.active,
            "last_sync": dev.last_sync,
            "recent_activities": recent_activities
        })
    
    return {"developers": result, "total_count": len(result)}

@router.get("/developer-summary/{developer_id}")
async def get_developer_summary(
    developer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),  # Add authentication
    db: Session = Depends(get_db)
):
    """Get activity summary for a specific developer"""
    
    # Parse dates
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end = datetime.now(timezone.utc)
    
    # Get developer activities
    activities = db.query(models.ActivityRecord).filter(
        models.ActivityRecord.developer_id == developer_id,
        models.ActivityRecord.timestamp >= start,
        models.ActivityRecord.timestamp <= end
    ).all()
    
    if not activities:
        return {
            "developer_id": developer_id,
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": {"total_activities": 0, "total_time": 0, "categories": {}}
        }
    
    # Process activities into summary
    summary = process_developer_activities(activities)
    
    return {
        "developer_id": developer_id,
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "summary": summary
    }

@router.get("/team-dashboard")
async def get_team_dashboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team-wide dashboard data"""
    
    # Parse dates
    if start_date:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
    if end_date:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end = datetime.now(timezone.utc)
    
    # Get all active developers
    developers = db.query(models.Developer).filter(models.Developer.active == True).all()
    
    team_data = []
    
    for developer in developers:
        # Get activities for this developer
        activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.developer_id == developer.developer_id,
            models.ActivityRecord.timestamp >= start,
            models.ActivityRecord.timestamp <= end
        ).all()
        
        summary = process_developer_activities(activities)
        
        team_data.append({
            "developer_id": developer.developer_id,
            "name": developer.name,
            "last_sync": developer.last_sync,
            "summary": summary
        })
    
    return {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "team_data": team_data,
        "total_developers": len(developers)
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for developer systems"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Timesheet server is running"
    }

def categorize_application(app_name: str, window_title: str = "") -> str:
    """Categorize application based on name and window title"""
    # Use your existing categorization logic
    # This should be the same as in activitywatch_client.py
    pass

def extract_detailed_info(window_title: str, app_name: str) -> dict:
    """Extract detailed information from window title and app name"""
    # Use your existing extraction logic
    # This should be the same as in activitywatch_client.py
    pass

def process_developer_activities(activities: List[models.ActivityRecord]) -> Dict:
    """Process activities into summary statistics"""
    if not activities:
        return {"total_activities": 0, "total_time": 0, "categories": {}}
    
    total_time = sum(activity.duration for activity in activities)
    categories = {}
    
    for activity in activities:
        category = activity.category
        if category not in categories:
            categories[category] = {"count": 0, "duration": 0}
        
        categories[category]["count"] += 1
        categories[category]["duration"] += activity.duration
    
    return {
        "total_activities": len(activities),
        "total_time": total_time,
        "total_time_formatted": f"{total_time / 3600:.2f}h",
        "categories": categories
    }
