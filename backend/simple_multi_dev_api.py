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
