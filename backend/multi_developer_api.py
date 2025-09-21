from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import secrets
import hashlib
from pydantic import BaseModel
import models, schemas, crud
from database import get_db
from auth import get_current_user
import re
from urllib.parse import urlparse

router = APIRouter()

# Pydantic models for multi-developer support
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

class DeveloperRegistration(BaseModel):
    developer_id: Optional[str] = None  # Auto-generated if not provided
    name: str
    email: Optional[str] = None
    active: bool = True

class DeveloperInfo(BaseModel):
    developer_id: str
    name: str
    email: Optional[str] = None
    active: bool
    last_sync: Optional[datetime] = None
    recent_activities: Optional[int] = 0

# Helper functions for activity processing
def categorize_application(app_name: str, window_title: str = "") -> str:
    """Categorize application based on name and window title"""
    app_name_lower = app_name.lower()
    window_title_lower = window_title.lower()
    
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
    if (any(system in app_name_lower for system in ['explorer', 'finder', 'terminal', 'cmd', 'powershell', 'task manager', 'lock', 'dwm', 'winlogon', 'csrss', 'lsass', 'services', 'svchost', 'searchhost', 'notepad']) 
        or app_name_lower.endswith('.exe') and any(sys_exe in app_name_lower for sys_exe in ['lock', 'explorer', 'dwm', 'winlogon', 'searchhost', 'notepad'])):
        return 'system'
    
    return 'other'

def extract_detailed_info(window_title: str, app_name: str) -> dict:
    """Extract detailed information from window title and app name"""
    info = {
        'url': None,
        'file_path': None,
        'database_connection': None,
        'specific_process': None,
        'detailed_activity': None,
        'project_name': None,
        'project_type': None
    }
    
    app_name_lower = app_name.lower()
    window_title_lower = window_title.lower()
    
    # Browser URL extraction
    if any(browser in app_name_lower for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']):
        info['url'] = extract_url_from_browser_title(window_title)
        if ' - ' in window_title:
            page_title = window_title.split(' - ')[0].strip()
            info['detailed_activity'] = f"Browsing: {page_title}"
            if info['url']:
                info['detailed_activity'] += f" ({info['url']})"
        else:
            info['detailed_activity'] = f"Browsing: {window_title}"
        
        # Extract project info for browsers
        project_info = extract_project_from_browser(window_title)
        info['project_name'] = project_info['project_name']
        info['project_type'] = project_info['project_type']
    
    # IDE and Code Editor details
    elif any(ide in app_name_lower for ide in ['vscode', 'visual studio', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs', 'notepad++', 'cursor']):
        info['file_path'] = extract_file_path(window_title)
        if info['file_path']:
            if '/' in info['file_path']:
                project, filename = info['file_path'].rsplit('/', 1)
                info['detailed_activity'] = f"Coding: {filename} in {project}"
                info['project_name'] = project
            else:
                info['detailed_activity'] = f"Coding: {info['file_path']}"
                info['project_name'] = info['file_path']
        else:
            info['detailed_activity'] = f"Coding: {window_title}"
            info['project_name'] = extract_project_from_ide_title(window_title)
        
        info['project_type'] = 'Development'
    
    # Database tools
    elif any(db_tool in app_name_lower for db_tool in ['datagrip', 'pgadmin', 'mysql', 'dbeaver', 'navicat', 'sqlserver', 'oracle']):
        info['database_connection'] = extract_database_info(window_title)
        if info['database_connection']:
            info['detailed_activity'] = f"Database: Connected to {info['database_connection']}"
            info['project_name'] = f"DB: {info['database_connection']}"
        else:
            clean_app_name = app_name.replace('.exe', '').replace('64', '')
            info['detailed_activity'] = f"Database: {clean_app_name} - {window_title}"
            info['project_name'] = clean_app_name
        
        info['project_type'] = 'Database'
    
    # System processes
    elif (categorize_application(app_name, window_title) == 'system' or 
          app_name_lower.endswith('.exe')):
        info['specific_process'] = app_name
        clean_app_name = app_name.replace('.exe', '') if app_name.endswith('.exe') else app_name
        if window_title and window_title != app_name and len(window_title.strip()) > 0:
            info['detailed_activity'] = f"System: {clean_app_name} - {window_title}"
        else:
            info['detailed_activity'] = f"System: {clean_app_name}"
        
        info['project_name'] = clean_app_name
        info['project_type'] = 'System'
    
    # Office applications
    elif any(office in app_name_lower for office in ['word', 'excel', 'powerpoint', 'outlook']):
        info['file_path'] = extract_office_document(window_title)
        if info['file_path']:
            info['detailed_activity'] = f"Office: {info['file_path']}"
            info['project_name'] = info['file_path']
        else:
            info['detailed_activity'] = f"Office: {window_title}"
            info['project_name'] = window_title
        
        info['project_type'] = 'Productivity'
    
    # Communication apps
    elif any(comm in app_name_lower for comm in ['teams', 'slack', 'discord', 'zoom', 'skype']):
        info['detailed_activity'] = f"Communication: {window_title}"
        info['project_name'] = app_name.replace('.exe', '')
        info['project_type'] = 'Communication'
    
    # Media applications
    elif any(media in app_name_lower for media in ['spotify', 'youtube', 'vlc', 'media player', 'netflix']):
        info['detailed_activity'] = f"Media: {window_title}"
        info['project_name'] = app_name.replace('.exe', '')
        info['project_type'] = 'Entertainment'
    
    # Default detailed activity
    if not info['detailed_activity']:
        info['detailed_activity'] = f"{app_name}: {window_title}"
        info['project_name'] = app_name.replace('.exe', '')
        info['project_type'] = 'Work'
    
    return info

def extract_url_from_browser_title(window_title: str) -> Optional[str]:
    """Enhanced URL extraction from browser window title"""
    browser_patterns = [
        r'^(.+?)\s*-\s*(Google Chrome|Mozilla Firefox|Microsoft Edge|Safari|Opera|Brave)',
        r'https?://[^\s\)]+',
        r'www\.[^\s\)]+',
    ]
    
    for pattern in browser_patterns:
        match = re.search(pattern, window_title, re.IGNORECASE)
        if match:
            if 'http' in match.group() or 'www' in match.group():
                url = match.group()
                if not url.startswith('http'):
                    url = 'https://' + url
                try:
                    parsed = urlparse(url)
                    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                except:
                    return url
            else:
                page_title = match.group(1).strip()
                
                # Map common page titles to URLs
                title_to_url = {
                    'claude': 'https://claude.ai',
                    'chatgpt': 'https://chat.openai.com',
                    'github': 'https://github.com',
                    'stackoverflow': 'https://stackoverflow.com',
                    'google': 'https://google.com',
                    'youtube': 'https://youtube.com',
                    'gmail': 'https://gmail.com',
                    'linkedin': 'https://linkedin.com',
                }
                
                page_lower = page_title.lower()
                for key, url in title_to_url.items():
                    if key in page_lower:
                        return url
    
    return None

def extract_file_path(window_title: str) -> Optional[str]:
    """Extract file path from IDE window title"""
    patterns = [
        r'([A-Za-z]:\\[^|<>:*?"]+\.[a-zA-Z0-9]+)',
        r'(/[^|<>:*?"]+\.[a-zA-Z0-9]+)',
        r'^([^-]+\.[a-zA-Z0-9]+)\s*-\s*([^-]+)\s*-\s*(Cursor|Code|Visual Studio)',
        r'^([^-]+\.[a-zA-Z0-9]+)\s*-\s*(Cursor|Code|Visual Studio|PyCharm|IntelliJ)',
        r'^([^-]+)\s*-\s*(Cursor|Code|Visual Studio|PyCharm|IntelliJ)$',
        r'^([^\\/:*?"<>|]+\.[a-zA-Z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, window_title, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 2:
                first_part = match.group(1).strip()
                second_part = match.group(2).strip() if len(match.groups()) > 1 else ""
                
                if second_part.lower() in ['cursor', 'code', 'visual studio', 'pycharm', 'intellij']:
                    return first_part
                elif '.' in first_part and len(first_part.split('.')) == 2:
                    return f"{second_part}/{first_part}"
                else:
                    return first_part
            else:
                return match.group(1).strip()
    
    return None

def extract_project_from_ide_title(window_title: str) -> Optional[str]:
    """Extract project name from IDE window title"""
    ide_pattern = r'^(.+?)\s*-\s*(Cursor|Code|Visual Studio|PyCharm|IntelliJ)$'
    match = re.search(ide_pattern, window_title, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def extract_project_from_browser(window_title: str) -> dict:
    """Extract project information from browser window title"""
    if ' - ' in window_title:
        page_title = window_title.split(' - ')[0].strip()
        
        # Check for localhost development
        if 'localhost:' in window_title:
            port_match = re.search(r'localhost:(\d+)', window_title)
            port = port_match.group(1) if port_match else 'unknown'
            return {
                'project_name': f'localhost:{port}',
                'project_type': 'Web Development'
            }
        
        # Check for known domains
        url_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', window_title)
        if url_match:
            return {
                'project_name': url_match.group(1),
                'project_type': 'Web Research'
            }
        
        return {
            'project_name': page_title,
            'project_type': 'Web Browsing'
        }
    
    return {
        'project_name': 'Browser',
        'project_type': 'Web Browsing'
    }

def extract_database_info(window_title: str) -> Optional[str]:
    """Extract database connection info"""
    db_patterns = [
        r'@([^@\s]+)',
        r'([a-zA-Z0-9_]+@[a-zA-Z0-9.-]+)',
        r'([a-zA-Z0-9_]+)\s*-\s*([a-zA-Z0-9.-]+)',
    ]
    
    for pattern in db_patterns:
        match = re.search(pattern, window_title)
        if match:
            return match.group()
    
    return None

def extract_office_document(window_title: str) -> Optional[str]:
    """Extract document name from Office application title"""
    office_suffixes = [' - Word', ' - Excel', ' - PowerPoint', ' - Microsoft Word', ' - Microsoft Excel', ' - Microsoft PowerPoint']
    
    title = window_title
    for suffix in office_suffixes:
        if suffix in title:
            title = title.replace(suffix, '')
            break
    
    return title.strip() if title.strip() else None

def generate_unique_developer_id(name: str, email: Optional[str], db: Session) -> str:
    """Generate a unique developer ID from name and email"""
    import hashlib
    from datetime import datetime
    
    # Clean and normalize name
    clean_name = name.lower().strip()
    clean_name = ''.join(c if c.isalnum() or c.isspace() else '' for c in clean_name)
    clean_name = '_'.join(clean_name.split())
    
    # Create base ID
    if email:
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:4]
        base_id = f"{clean_name}_{email_hash}"
    else:
        year = datetime.now().year
        base_id = f"{clean_name}_{year}"
    
    # Ensure uniqueness
    original_id = base_id
    counter = 1
    
    while db.query(models.Developer).filter(models.Developer.developer_id == base_id).first():
        base_id = f"{original_id}_{counter}"
        counter += 1
    
    return base_id

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
            
            # Extract detailed information
            detailed_info = extract_detailed_info(activity.window_title, activity.application_name)
            
            # Create activity record
            activity_record = models.ActivityRecord(
                developer_id=developer.developer_id,
                application_name=activity.application_name,
                window_title=activity.window_title,
                duration=activity.duration,
                timestamp=timestamp,
                category=categorize_application(activity.application_name, activity.window_title),
                url=detailed_info['url'],
                file_path=detailed_info['file_path'],
                database_connection=detailed_info['database_connection'],
                specific_process=detailed_info['specific_process'],
                detailed_activity=detailed_info['detailed_activity'],
                project_name=detailed_info['project_name'],
                project_type=detailed_info['project_type']
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
    developer_info: DeveloperRegistration,
    admin_token: str = Header(..., alias="Admin-Token"),
    db: Session = Depends(get_db)
):
    """Register a new developer (admin only)"""
    
    # Verify admin token from environment
    import os
    expected_admin_token = os.getenv("ADMIN_TOKEN", "timesheet-admin-2025-secure-token")
    if admin_token != expected_admin_token:
        raise HTTPException(status_code=401, detail="Admin access required")
    
    # Check if developer already exists
    existing = db.query(models.Developer).filter(
        models.Developer.developer_id == developer_info.developer_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Developer already registered")
    
    # Generate unique developer ID if not provided
    if not developer_info.developer_id:
        developer_info.developer_id = generate_unique_developer_id(developer_info.name, developer_info.email, db)
    
    # Generate API token
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
    
    # Verify admin token from environment
    import os
    expected_admin_token = os.getenv("ADMIN_TOKEN", "timesheet-admin-2025-secure-token")
    if admin_token != expected_admin_token:
        raise HTTPException(status_code=401, detail="Admin access required")
    
    developers = db.query(models.Developer).all()
    
    result = []
    for dev in developers:
        # Get recent activity count (last 24 hours)
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
            "recent_activities": recent_activities,
            "api_token": dev.api_token  # Include for admin reference
        })
    
    return {"developers": result, "total_count": len(result)}

@router.get("/developer-summary/{developer_id}")
async def get_developer_summary(
    developer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
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
    
    # Get developer info
    developer = db.query(models.Developer).filter(
        models.Developer.developer_id == developer_id
    ).first()
    
    if not developer:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    # Get developer activities
    activities = db.query(models.ActivityRecord).filter(
        models.ActivityRecord.developer_id == developer_id,
        models.ActivityRecord.timestamp >= start,
        models.ActivityRecord.timestamp <= end
    ).all()
    
    if not activities:
        return {
            "developer_id": developer_id,
            "developer_name": developer.name,
            "date_range": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": {"total_activities": 0, "total_time": 0, "categories": {}, "projects": {}}
        }
    
    # Process activities into summary
    summary = process_developer_activities(activities)
    
    return {
        "developer_id": developer_id,
        "developer_name": developer.name,
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
    total_team_time = 0
    total_team_activities = 0
    
    for developer in developers:
        # Get activities for this developer
        activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.developer_id == developer.developer_id,
            models.ActivityRecord.timestamp >= start,
            models.ActivityRecord.timestamp <= end
        ).all()
        
        summary = process_developer_activities(activities)
        total_team_time += summary['total_time']
        total_team_activities += summary['total_activities']
        
        team_data.append({
            "developer_id": developer.developer_id,
            "name": developer.name,
            "email": developer.email,
            "last_sync": developer.last_sync,
            "summary": summary
        })
    
    return {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "team_data": team_data,
        "total_developers": len(developers),
        "team_totals": {
            "total_time": total_team_time,
            "total_time_formatted": f"{total_team_time / 3600:.2f}h",
            "total_activities": total_team_activities
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for developer systems"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Timesheet server is running"
    }

def process_developer_activities(activities: List[models.ActivityRecord]) -> Dict:
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
    
    # Format categories and projects for frontend
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
