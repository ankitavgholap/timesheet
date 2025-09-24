# Fix for your /top-window-titles endpoint
# Replace the existing @app.get("/top-window-titles") in your main.py with this:

@app.get("/top-window-titles")
def get_top_window_titles(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top window titles by duration from database"""
    try:
        from sqlalchemy import text
        
        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        # Get top window titles from database
        query = text("""
            SELECT 
                ar.application_name,
                ar.window_title,
                ar.developer_id,
                ar.category,
                SUM(ar.duration) as total_duration,
                COUNT(*) as activity_count,
                MAX(ar.timestamp) as last_seen,
                -- Extract project information
                CASE 
                    WHEN ar.window_title ILIKE '%localhost:%' THEN 'Web Development'
                    WHEN ar.application_name ILIKE '%cursor%' OR ar.application_name ILIKE '%vscode%' THEN 'Development'
                    WHEN ar.application_name ILIKE '%chrome%' OR ar.application_name ILIKE '%firefox%' THEN 'Browser'
                    WHEN ar.application_name ILIKE '%filezilla%' OR ar.application_name ILIKE '%winscp%' THEN 'Server Management'
                    WHEN ar.application_name ILIKE '%datagrip%' OR ar.application_name ILIKE '%pgadmin%' THEN 'Database'
                    ELSE 'General'
                END as project_type,
                -- Extract project name
                CASE 
                    WHEN ar.window_title ILIKE '%localhost:%' THEN 
                        SUBSTRING(ar.window_title FROM 'localhost:([0-9]+)')
                    WHEN ar.application_name ILIKE '%cursor%' OR ar.application_name ILIKE '%vscode%' THEN
                        SPLIT_PART(SPLIT_PART(ar.window_title, ' - ', 2), ' - ', 1)
                    WHEN ar.application_name ILIKE '%chrome%' OR ar.application_name ILIKE '%firefox%' THEN
                        SPLIT_PART(ar.window_title, ' - ', 1)
                    ELSE ar.application_name
                END as project_name,
                -- Extract file name
                CASE 
                    WHEN ar.window_title LIKE '%.%' THEN 
                        SPLIT_PART(ar.window_title, ' - ', 1)
                    ELSE ar.window_title
                END as file_name
            FROM activity_records ar
            WHERE ar.timestamp >= :start_date 
            AND ar.timestamp <= :end_date
            AND ar.duration >= 5  -- Filter out very short activities
            AND ar.window_title IS NOT NULL
            AND ar.window_title != ''
            AND ar.developer_id = :developer_id  -- Filter by current user's developer ID
            GROUP BY ar.application_name, ar.window_title, ar.developer_id, ar.category
            ORDER BY total_duration DESC
            LIMIT :limit
        """)
        
        # Get current user's developer ID (assuming username matches developer_id)
        # You might need to adjust this based on your user-developer mapping
        developer_id = current_user.username  # or however you map users to developers
        
        result = db.execute(query, {
            "start_date": start,
            "end_date": end,
            "limit": limit,
            "developer_id": developer_id
        }).fetchall()
        
        # Format response similar to your existing structure
        top_titles = []
        for row in result:
            # Clean up project name
            project_name = row.project_name or row.application_name
            if project_name and len(project_name.strip()) > 0:
                project_name = project_name.strip()
            else:
                project_name = row.application_name
            
            # Clean up file name
            file_name = row.file_name or row.window_title
            if len(file_name) > 100:  # Truncate long titles
                file_name = file_name[:97] + "..."
            
            top_titles.append({
                'application_name': row.application_name,
                'window_title': row.window_title,
                'total_duration': float(row.total_duration),
                'activity_count': row.activity_count,
                'last_seen': row.last_seen,
                'duration_formatted': f"{float(row.total_duration) / 3600:.2f}h",
                'last_seen_formatted': row.last_seen.strftime('%Y-%m-%d %H:%M:%S') if row.last_seen else '',
                
                # Project information for your dashboard
                'project_info': {
                    'project_type': row.project_type,
                    'project_name': project_name,
                    'file_name': file_name
                }
            })
        
        return {
            "top_window_titles": top_titles,
            "total_titles": len(top_titles),
            "date_range": {"start": start.isoformat(), "end": end.isoformat()}
        }
        
    except Exception as e:
        print(f"Error in top-window-titles: {e}")  # Debug logging
        raise HTTPException(status_code=500, detail=f"Error fetching top window titles: {str(e)}")
