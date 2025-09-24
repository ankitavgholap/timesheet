# simple_multi_dev_api.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from database import get_db
import json

router = APIRouter(prefix="/api/multi-dev", tags=["multi-developer"])


def validate_token(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.replace("Bearer ", "")
    
    result = db.execute(
        text("SELECT developer_id FROM developer_api_tokens WHERE api_token = :token AND is_active = true"),
        {"token": token}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return result[0]

@router.post("/activity/upload")
def upload_activities(
    activities: list,
    developer_id: str = Depends(validate_token),
    db: Session = Depends(get_db)
):
    count = 0
    for activity in activities:
        # Insert into your existing activity_records table
        db.execute(
            text("""
                INSERT INTO activity_records 
                (developer_id, application_name, window_title, duration, timestamp, category)
                VALUES (:dev_id, :app, :title, :duration, :timestamp, :category)
            """),
            {
                "dev_id": developer_id,
                "app": activity.get("application_name", "Unknown"),
                "title": activity.get("window_title", ""),
                "duration": activity.get("duration", 0),
                "timestamp": activity.get("timestamp"),
                "category": activity.get("category", "other")
            }
        )
        count += 1
    
    db.commit()
    return {"status": "success", "processed": count}

@router.get("/health")
def health_check():
    return {"status": "healthy"}

@router.get("/developers-summary")
def get_developers_summary(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Get summary of all developers' activities"""
    try:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import text, func
        
        # Parse dates or use defaults (today)
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now(timezone.utc)
        
        # Get all developers with their activity data
        developers_query = text("""
            SELECT 
                ar.developer_id,
                COUNT(*) as activity_count,
                SUM(ar.duration) as total_duration,
                MAX(ar.timestamp) as last_activity,
                COUNT(DISTINCT ar.application_name) as unique_apps
            FROM activity_records ar
            WHERE ar.developer_id IS NOT NULL
            AND ar.timestamp >= :start_date
            AND ar.timestamp <= :end_date
            GROUP BY ar.developer_id
            ORDER BY total_duration DESC
        """)
        
        developers_result = db.execute(developers_query, {
            "start_date": start,
            "end_date": end
        }).fetchall()
        
        developers = []
        total_hours = 0
        total_activities = 0
        active_count = 0
        
        for dev_row in developers_result:
            developer_id = dev_row[0]
            activity_count = dev_row[1]
            duration_seconds = dev_row[2] or 0
            last_activity = dev_row[3]
            unique_apps = dev_row[4]
            
            # Convert to hours
            hours_today = duration_seconds / 3600.0
            total_hours += hours_today
            total_activities += activity_count
            
            # Check if active (activity in last 30 minutes)
            is_active = False
            if last_activity:
                time_diff = datetime.now(timezone.utc) - last_activity.replace(tzinfo=timezone.utc)
                is_active = time_diff.total_seconds() < 1800  # 30 minutes
                if is_active:
                    active_count += 1
            
            # Get recent activities for this developer
            recent_activities_query = text("""
                SELECT 
                    ar.application_name,
                    SUM(ar.duration) as total_duration
                FROM activity_records ar
                WHERE ar.developer_id = :dev_id
                AND ar.timestamp >= :start_date
                AND ar.timestamp <= :end_date
                GROUP BY ar.application_name
                ORDER BY total_duration DESC
                LIMIT 3
            """)
            
            recent_result = db.execute(recent_activities_query, {
                "dev_id": developer_id,
                "start_date": start,
                "end_date": end
            }).fetchall()
            
            recent_activities = []
            for activity in recent_result:
                app_name = activity[0]
                app_duration = activity[1] / 3600.0  # Convert to hours
                recent_activities.append({
                    "app": app_name,
                    "duration": f"{app_duration:.1f}h"
                })
            
            # Calculate productivity (simplified - can use your existing logic)
            productivity = min(95, max(0, int(hours_today * 12)))  # Rough estimate
            
            # Format last seen
            if last_activity:
                time_diff = datetime.now(timezone.utc) - last_activity.replace(tzinfo=timezone.utc)
                if time_diff.total_seconds() < 3600:  # Less than 1 hour
                    last_seen = f"{int(time_diff.total_seconds() / 60)} min ago"
                elif time_diff.total_seconds() < 86400:  # Less than 1 day
                    last_seen = f"{int(time_diff.total_seconds() / 3600)}h ago"
                else:
                    last_seen = last_activity.strftime('%Y-%m-%d')
            else:
                last_seen = "Never"
            
            developers.append({
                "name": developer_id,
                "is_active": is_active,
                "hours_today": hours_today,
                "productivity": productivity,
                "activities_count": activity_count,
                "last_seen": last_seen,
                "recent_activities": recent_activities
            })
        
        # Calculate overview stats
        avg_productivity = sum(dev["productivity"] for dev in developers) / len(developers) if developers else 0
        
        overview = {
            "active_developers": active_count,
            "total_hours": total_hours,
            "total_activities": total_activities,
            "avg_productivity": avg_productivity,
            "total_developers": len(developers)
        }
        
        return {
            "overview": overview,
            "developers": developers,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting developers summary: {str(e)}")

@router.get("/developer/{developer_id}/activity-summary")
def get_developer_activity_summary(
    developer_id: str,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Get activity summary for a specific developer (like your dashboard screenshot)"""
    try:
        from datetime import datetime, timezone
        from sqlalchemy import text, func
        
        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now(timezone.utc)
        
        # Get activity data grouped by category (like your pie chart)
        activity_query = text("""
            SELECT 
                COALESCE(ar.category, 'Unknown') as category,
                SUM(ar.duration) as total_duration,
                COUNT(*) as activity_count
            FROM activity_records ar
            WHERE ar.developer_id = :dev_id
            AND ar.timestamp >= :start_date
            AND ar.timestamp <= :end_date
            GROUP BY ar.category
            ORDER BY total_duration DESC
        """)
        
        activities_result = db.execute(activity_query, {
            "dev_id": developer_id,
            "start_date": start,
            "end_date": end
        }).fetchall()
        
        # Format for pie chart (like your screenshot)
        activity_data = []
        total_time = 0
        colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0']
        
        for i, activity in enumerate(activities_result):
            category = activity[0]
            duration_hours = activity[1] / 3600.0  # Convert to hours
            total_time += duration_hours
            
            activity_data.append({
                "category": category,
                "duration": duration_hours,
                "count": activity[2],
                "color": colors[i % len(colors)]
            })
        
        # Get unique projects count
        projects_query = text("""
            SELECT COUNT(DISTINCT 
                CASE 
                    WHEN ar.window_title IS NOT NULL THEN ar.window_title
                    ELSE ar.application_name
                END
            ) as project_count
            FROM activity_records ar
            WHERE ar.developer_id = :dev_id
            AND ar.timestamp >= :start_date
            AND ar.timestamp <= :end_date
        """)
        
        project_result = db.execute(projects_query, {
            "dev_id": developer_id,
            "start_date": start,
            "end_date": end
        }).fetchone()
        
        active_projects = project_result[0] if project_result else 0
        
        return {
            "data": activity_data,
            "total_time": total_time,
            "active_projects": active_projects,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting activity summary: {str(e)}")

@router.get("/developer/{developer_id}/detailed")
def get_developer_detailed(
    developer_id: str,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """Get detailed activity data for a specific developer"""
    try:
        from datetime import datetime, timezone
        
        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now(timezone.utc)
        
        # Get detailed activities
        activities_query = text("""
            SELECT 
                application_name,
                window_title,
                category,
                duration,
                timestamp
            FROM activity_records
            WHERE developer_id = :dev_id
            AND timestamp >= :start_date
            AND timestamp <= :end_date
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        activities_result = db.execute(activities_query, {
            "dev_id": developer_id,
            "start_date": start,
            "end_date": end
        }).fetchall()
        
        activities = []
        for activity in activities_result:
            activities.append({
                "application_name": activity[0],
                "window_title": activity[1],
                "category": activity[2],
                "duration": activity[3],
                "timestamp": activity[4].isoformat()
            })
        
        return {
            "developer_id": developer_id,
            "activities": activities,
            "total_activities": len(activities),
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting developer details: {str(e)}")

@router.get("/developers-list")
def get_developers_list(db: Session = Depends(get_db)):
    """Get list of all known developers"""
    try:
        # Get from activity records
        developers_query = text("""
            SELECT DISTINCT 
                ar.developer_id,
                COUNT(*) as activity_count,
                MAX(ar.timestamp) as last_activity
            FROM activity_records ar
            WHERE ar.developer_id IS NOT NULL
            GROUP BY ar.developer_id
            ORDER BY last_activity DESC
        """)
        
        result = db.execute(developers_query).fetchall()
        
        developers = []
        for row in result:
            developers.append({
                "developer_id": row[0],
                "activity_count": row[1],
                "last_activity": row[2].isoformat() if row[2] else None
            })
        
        return {"developers": developers}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting developers list: {str(e)}")
