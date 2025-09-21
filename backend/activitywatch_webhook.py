from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import json
from pydantic import BaseModel
import models, schemas, crud
from database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ActivityWatchEvent(BaseModel):
    timestamp: str
    duration: float
    data: Dict[str, Any]

class ActivityWatchBucket(BaseModel):
    id: str
    type: str
    hostname: str
    events: List[ActivityWatchEvent]

class ActivityWatchWebhook(BaseModel):
    buckets: List[ActivityWatchBucket]
    timeperiod: Dict[str, str]
    hostname: str

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
        # Pattern: "filename.ext - project - IDE"
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
            # Extract domain from URL
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
async def receive_activitywatch_webhook(
    request: Request,
    developer_id: str = Header(..., alias="Developer-ID"),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Receive ActivityWatch data via webhook"""
    
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
    
    try:
        # Get raw JSON data
        webhook_data = await request.json()
        logger.info(f"Received ActivityWatch webhook from {developer_id}")
        
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
                        
                        # Check for duplicates (avoid storing same activity twice)
                        existing = db.query(models.ActivityRecord).filter(
                            models.ActivityRecord.developer_id == developer_id,
                            models.ActivityRecord.timestamp == timestamp,
                            models.ActivityRecord.application_name == app_name,
                            models.ActivityRecord.duration == duration
                        ).first()
                        
                        if existing:
                            continue  # Skip duplicates
                        
                        # Create activity record
                        activity_record = models.ActivityRecord(
                            developer_id=developer_id,
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
        
        # Update developer last sync time
        developer.last_sync = datetime.now(timezone.utc)
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Successfully processed {processed_activities} activities from {developer.name}")
        
        return {
            "status": "success",
            "message": f"Processed {processed_activities} activities",
            "developer_id": developer_id,
            "developer_name": developer.name
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing ActivityWatch webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@router.post("/activitywatch/sync")
async def receive_activitywatch_sync(
    request: Request,
    developer_id: str = Header(..., alias="Developer-ID"),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Alternative sync endpoint for ActivityWatch data"""
    
    # This can handle different formats that ActivityWatch might send
    return await receive_activitywatch_webhook(request, developer_id, authorization, db)

@router.get("/activitywatch/config/{developer_id}")
async def get_activitywatch_config(
    developer_id: str,
    admin_token: str = Header(..., alias="Admin-Token"),
    db: Session = Depends(get_db)
):
    """Generate ActivityWatch config.toml for a developer"""
    
    # Verify admin token from environment
    import os
    expected_admin_token = os.getenv("ADMIN_TOKEN", "timesheet-admin-2025-secure-token")
    if admin_token != expected_admin_token:
        raise HTTPException(status_code=401, detail="Admin access required")
    
    # Get developer info
    developer = db.query(models.Developer).filter(
        models.Developer.developer_id == developer_id,
        models.Developer.active == True
    ).first()
    
    if not developer:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    # Get server URL from environment
    import os
    server_url = os.getenv("SERVER_URL", os.getenv("FRONTEND_URL", "https://your-timesheet-server.com"))
    
    # Generate TOML configuration
    config_toml = f"""# ActivityWatch Configuration for {developer.name}
# Place this file in your ActivityWatch config directory
# Windows: %APPDATA%\\activitywatch\\aw-server\\config.toml
# Linux: ~/.config/activitywatch/aw-server/config.toml
# macOS: ~/Library/Application Support/activitywatch/aw-server/config.toml

[server]
host = "127.0.0.1"
port = 5600

# Team timesheet integration
[integrations.timesheet]
enabled = true
webhook_url = "{server_url}/api/v1/activitywatch/webhook"
developer_id = "{developer.developer_id}"
api_token = "{developer.api_token}"
sync_interval = 1800  # 30 minutes in seconds

# Webhook configuration
[webhooks]
enabled = true

[[webhooks.endpoints]]
url = "{server_url}/api/v1/activitywatch/webhook"
method = "POST"
interval = 1800  # 30 minutes
headers = {{
    "Developer-ID" = "{developer.developer_id}",
    "Authorization" = "Bearer {developer.api_token}",
    "Content-Type" = "application/json"
}}

# Include these buckets in sync
include_buckets = [
    "aw-watcher-window",
    "aw-watcher-web-chrome", 
    "aw-watcher-web-firefox",
    "aw-watcher-afk"
]

# Privacy settings
[privacy]
include_window_titles = true
include_urls = true
exclude_patterns = [
    "*password*",
    "*login*", 
    "*private*",
    "*confidential*"
]

# Logging
[logging]
level = "INFO"
"""
    
    return {
        "developer_id": developer_id,
        "developer_name": developer.name,
        "config_toml": config_toml,
        "installation_instructions": {
            "windows": "%APPDATA%\\activitywatch\\aw-server\\config.toml",
            "linux": "~/.config/activitywatch/aw-server/config.toml", 
            "macos": "~/Library/Application Support/activitywatch/aw-server/config.toml"
        }
    }

@router.get("/activitywatch/test-webhook")
async def test_webhook_endpoint():
    """Test endpoint for ActivityWatch webhook"""
    return {
        "status": "healthy",
        "message": "ActivityWatch webhook endpoint is working",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
