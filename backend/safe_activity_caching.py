# backend/safe_activity_caching.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import ActivityRecord
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def safe_create_activity_record(db: Session, activity_data: dict, user_id: int = 1):
    """Safely create activity record with proper error handling"""
    try:
        # Check if record already exists to avoid duplicates
        existing = db.query(ActivityRecord).filter(
            and_(
                ActivityRecord.user_id == user_id,
                ActivityRecord.application_name == activity_data.get('application_name'),
                ActivityRecord.window_title == activity_data.get('window_title'),
                ActivityRecord.timestamp == activity_data.get('activity_timestamp'),
                ActivityRecord.duration == activity_data.get('duration')
            )
        ).first()
        
        if existing:
            # Record already exists, skip
            return existing
        
        # Create new record
        activity_record = ActivityRecord(
            user_id=user_id,
            developer_id=activity_data.get('developer_id'),
            developer_name=activity_data.get('developer_name'),
            developer_hostname=activity_data.get('developer_hostname'),
            device_id=activity_data.get('device_id'),
            application_name=activity_data.get('application_name'),
            window_title=activity_data.get('window_title'),
            url=activity_data.get('url'),
            file_path=activity_data.get('file_path'),
            detailed_activity=activity_data.get('detailed_activity'),
            category=activity_data.get('category'),
            duration=activity_data.get('duration'),
            timestamp=activity_data.get('activity_timestamp'),
            activity_timestamp=activity_data.get('activity_timestamp'),
            bucket_name=activity_data.get('bucket_name')
        )
        
        db.add(activity_record)
        db.commit()
        db.refresh(activity_record)
        
        return activity_record
        
    except Exception as e:
        logger.warning(f"Failed to cache activity safely: {e}")
        # Rollback the failed transaction
        db.rollback()
        return None

def get_activity_records_for_developer(db: Session, developer_name: str, start_date: datetime, end_date: datetime):
    """Get activity records for a specific developer"""
    try:
        return db.query(ActivityRecord).filter(
            and_(
                or_(
                    ActivityRecord.developer_name == developer_name,
                    ActivityRecord.developer_id == developer_name
                ),
                ActivityRecord.activity_timestamp >= start_date,
                ActivityRecord.activity_timestamp <= end_date
            )
        ).order_by(ActivityRecord.duration.desc()).limit(1000).all()
        
    except Exception as e:
        logger.error(f"Error getting activity records: {e}")
        return []
