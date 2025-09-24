# Add these imports to the top of your main.py (if not already there)
from pydantic import BaseModel
from typing import Optional
import re

# Add this model class near your other models/schemas
class DeveloperRegistration(BaseModel):
    developer_name: str
    developer_id: str
    api_token: str
    ip_address: Optional[str] = "127.0.0.1"
    activitywatch_port: Optional[int] = 5600
    hostname: Optional[str] = "unknown"
    active: Optional[bool] = True

# Add these endpoints to your main.py

@app.get("/register-developer")
async def serve_registration_form():
    """Serve the developer registration form"""
    return FileResponse("register-developer.html")

@app.post("/api/register-developer")
async def register_developer(
    registration: DeveloperRegistration,
    db: Session = Depends(get_db)
):
    """Register a new developer for monitoring"""
    try:
        # Validate access token format
        if not registration.api_token.startswith('AWToken_'):
            raise HTTPException(
                status_code=400,
                detail="Invalid access token format. Token must start with 'AWToken_'"
            )
        
        # Check if developer ID already exists
        existing_dev = db.execute(
            text("SELECT developer_id FROM developers WHERE developer_id = :dev_id"),
            {"dev_id": registration.developer_id}
        ).fetchone()
        
        if existing_dev:
            raise HTTPException(
                status_code=400,
                detail=f"Developer ID '{registration.developer_id}' already exists"
            )
        
        # Check if token is already used
        token_check = db.execute(
            text("SELECT developer_id FROM developers WHERE api_token = :token"),
            {"token": registration.api_token}
        ).fetchone()
        
        if token_check:
            raise HTTPException(
                status_code=400,
                detail="This access token is already in use"
            )
        
        # Add new columns if they don't exist (one-time setup)
        try:
            db.execute(text("ALTER TABLE developers ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45) DEFAULT '127.0.0.1'"))
            db.execute(text("ALTER TABLE developers ADD COLUMN IF NOT EXISTS activitywatch_port INTEGER DEFAULT 5600"))
            db.execute(text("ALTER TABLE developers ADD COLUMN IF NOT EXISTS hostname VARCHAR(255) DEFAULT 'unknown'"))
            db.execute(text("ALTER TABLE developers ADD COLUMN IF NOT EXISTS last_sync TIMESTAMP WITH TIME ZONE"))
            db.commit()
        except:
            pass  # Columns might already exist
        
        # Insert new developer
        insert_query = text("""
            INSERT INTO developers (
                developer_id, name, api_token, ip_address, 
                activitywatch_port, hostname, active, created_at
            ) VALUES (
                :developer_id, :name, :api_token, :ip_address,
                :activitywatch_port, :hostname, :active, NOW()
            )
        """)
        
        db.execute(insert_query, {
            "developer_id": registration.developer_id,
            "name": registration.developer_name,
            "api_token": registration.api_token,
            "ip_address": registration.ip_address,
            "activitywatch_port": registration.activitywatch_port,
            "hostname": registration.hostname,
            "active": registration.active
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": "Developer registered successfully",
            "developer_id": registration.developer_id,
            "developer_name": registration.developer_name,
            "monitoring_starts": "immediately"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@app.get("/api/developers-status")
async def get_developers_status(db: Session = Depends(get_db)):
    """Get status of all registered developers"""
    try:
        query = text("""
            SELECT 
                d.developer_id,
                d.name,
                d.ip_address,
                d.active,
                d.last_sync,
                COUNT(ar.id) as recent_activities
            FROM developers d
            LEFT JOIN activity_records ar ON d.developer_id = ar.developer_id 
                AND ar.created_at > NOW() - INTERVAL '1 hour'
            WHERE d.active = true
            GROUP BY d.developer_id, d.name, d.ip_address, d.active, d.last_sync
            ORDER BY d.name
        """)
        
        result = db.execute(query)
        developers = []
        
        for row in result:
            developers.append({
                "developer_id": row[0],
                "name": row[1],
                "ip_address": row[2],
                "active": row[3],
                "last_sync": row[4].isoformat() if row[4] else None,
                "recent_activities": row[5],
                "status": "monitoring" if row[5] > 0 else "registered"
            })
        
        return {
            "success": True,
            "developers": developers,
            "total_count": len(developers)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting developers status: {str(e)}"
        )