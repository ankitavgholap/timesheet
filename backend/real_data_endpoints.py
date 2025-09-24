# Add this to the end of your backend/main.py (before if __name__ == "__main__":)

from config import Config
from activitywatch_sync import ActivityWatchSync

@app.get("/api/sync-activitywatch")
async def sync_activitywatch_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Manually sync data from ActivityWatch"""
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
        
        sync = ActivityWatchSync()
        success = sync.sync_activitywatch_data(start, end)
        
        if success:
            summary = sync.get_summary(start, end)
            return {
                "success": True,
                "message": f"Synced data for {Config.LOCAL_DEVELOPER_NAME}",
                "summary": summary
            }
        else:
            return {
                "success": False,
                "message": "Failed to sync data from ActivityWatch"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@app.get("/api/developers/real-summary")
async def get_real_developers_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get REAL summary of developers based on environment"""
    try:
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import text
        
        # Parse dates or use defaults (today)
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date)  
        else:
            end = datetime.now(timezone.utc)
        
        # Different behavior based on environment
        if Config.is_local():
            # LOCAL: Show only local developer, sync if no data
            developers_query = text("""
                SELECT 
                    ar.developer_id,
                    COUNT(*) as activity_count,
                    SUM(ar.duration) as total_duration,
                    MAX(ar.timestamp) as last_activity
                FROM activity_records ar
                WHERE ar.developer_id = :local_dev
                AND ar.timestamp >= :start_date
                AND ar.timestamp <= :end_date
                GROUP BY ar.developer_id
            """)
            
            developers_result = db.execute(developers_query, {
                "local_dev": Config.LOCAL_DEVELOPER_NAME,
                "start_date": start,
                "end_date": end
            }).fetchall()
            
            # If no data, try to sync from ActivityWatch
            if not developers_result:
                print(f"No data found for {Config.LOCAL_DEVELOPER_NAME}, attempting sync...")
                sync = ActivityWatchSync()
                success = sync.sync_activitywatch_data(start, end)
                
                if success:
                    # Re-query after sync
                    developers_result = db.execute(developers_query, {
                        "local_dev": Config.LOCAL_DEVELOPER_NAME,
                        "start_date": start, 
                        "end_date": end
                    }).fetchall()
        else:
            # PRODUCTION: Show all developers
            developers_query = text("""
                SELECT 
                    ar.developer_id,
                    COUNT(*) as activity_count,
                    SUM(ar.duration) as total_duration,
                    MAX(ar.timestamp) as last_activity
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
        active_count = 0
        
        for dev_row in developers_result:
            developer_id = dev_row[0]
            activity_count = dev_row[1]
            duration_seconds = dev_row[2] or 0
            last_activity = dev_row[3]
            
            # Convert to hours
            hours_today = duration_seconds / 3600.0
            total_hours += hours_today
            
            # Check if active (activity in last 30 minutes)
            is_active = False
            if last_activity:
                time_diff = datetime.now(timezone.utc) - last_activity.replace(tzinfo=timezone.utc)
                is_active = time_diff.total_seconds() < 1800  # 30 minutes
                if is_active:
                    active_count += 1
            
            # Calculate productivity estimate
            productivity = min(95, max(0, int(hours_today * 12))) if hours_today > 0 else 0
            
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
                "last_seen": last_seen
            })
        
        # Calculate overview stats
        avg_productivity = sum(dev["productivity"] for dev in developers) / len(developers) if developers else 0
        
        overview = {
            "total_developers": len(developers),
            "active_developers": active_count,
            "total_hours": total_hours,
            "avg_productivity": avg_productivity,
            "environment": Config.ENVIRONMENT
        }
        
        return {
            "overview": overview,
            "developers": developers
        }
        
    except Exception as e:
        print(f"Error in get_real_developers_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting developers summary: {str(e)}")

@app.get("/api/developer/{developer_id}/real-activity")
async def get_real_developer_activity(
    developer_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get REAL activity data for specific developer"""
    try:
        from datetime import datetime, timezone
        from sqlalchemy import text
        
        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now(timezone.utc)
        
        # If local environment and no data, try to sync
        if Config.is_local() and developer_id == Config.LOCAL_DEVELOPER_NAME:
            # Check if we have data
            check_query = text("""
                SELECT COUNT(*) FROM activity_records
                WHERE developer_id = :dev_id
                AND timestamp >= :start_date
                AND timestamp <= :end_date
            """)
            
            count_result = db.execute(check_query, {
                "dev_id": developer_id,
                "start_date": start,
                "end_date": end
            }).fetchone()
            
            if not count_result[0]:
                print(f"No data found for {developer_id}, syncing from ActivityWatch...")
                sync = ActivityWatchSync()
                success = sync.sync_activitywatch_data(start, end)
                if success:
                    print("✅ Sync completed successfully")
        
        # Get activity data grouped by category
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
        
        # Format for pie chart
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
            SELECT COUNT(DISTINCT application_name) as project_count
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
        print(f"Error in get_real_developer_activity: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting activity data: {str(e)}")
