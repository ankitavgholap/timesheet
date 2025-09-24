# backend/create_enhanced_tables.py
"""
Migration script to add enhanced multi-developer tables
Run this once to add the new tables to your existing PostgreSQL database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database import DATABASE_URL, engine
from models import Base, DiscoveredDeveloper, ActivityRecord
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_enhanced_tables():
    """Create or update tables for enhanced multi-developer support"""
    
    logger.info("Creating enhanced tables for multi-developer support...")
    
    try:
        # Create all tables (will skip existing ones)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Base tables created/verified")
        
        # Add new columns to existing activity_records table if they don't exist
        with engine.connect() as conn:
            try:
                # Check if new columns exist, add them if not
                columns_to_add = [
                    ("developer_name", "VARCHAR(255)"),
                    ("developer_hostname", "VARCHAR(255)"), 
                    ("device_id", "VARCHAR(255)"),
                    ("activity_timestamp", "TIMESTAMP WITH TIME ZONE"),
                    ("bucket_name", "VARCHAR(255)")
                ]
                
                for column_name, column_type in columns_to_add:
                    try:
                        # Try to add column - will fail silently if exists
                        alter_sql = f"ALTER TABLE activity_records ADD COLUMN {column_name} {column_type};"
                        conn.execute(text(alter_sql))
                        conn.commit()
                        logger.info(f"✅ Added column: {column_name}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"⚪ Column {column_name} already exists")
                        else:
                            logger.warning(f"⚠️  Could not add column {column_name}: {e}")
                
                # Create indexes for better performance
                indexes_to_create = [
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_records_developer_name ON activity_records (developer_name);",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_records_developer_hostname ON activity_records (developer_hostname);", 
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_records_device_id ON activity_records (device_id);",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_records_activity_timestamp ON activity_records (activity_timestamp);",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_discovered_developers_enhanced_status ON discovered_developers_enhanced (status);",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_discovered_developers_enhanced_source ON discovered_developers_enhanced (source);"
                ]
                
                for index_sql in indexes_to_create:
                    try:
                        conn.execute(text(index_sql))
                        conn.commit()
                        logger.info(f"✅ Created index")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"⚪ Index already exists")
                        else:
                            logger.warning(f"⚠️  Could not create index: {e}")
                            
            except Exception as e:
                logger.error(f"Error updating activity_records table: {e}")
        
        logger.info("🎉 Enhanced tables setup complete!")
        
        # Display summary
        with engine.connect() as conn:
            # Count existing activity records
            result = conn.execute(text("SELECT COUNT(*) FROM activity_records;"))
            activity_count = result.scalar()
            
            logger.info(f"""
📊 Database Summary:
   • Activity Records: {activity_count:,}
   • Enhanced multi-developer support: ✅ Ready
   • Your local name: Ankita-TechTeam
   • Environment: Local PostgreSQL
   
🚀 You can now run your application!
   python main.py
""")
            
    except Exception as e:
        logger.error(f"❌ Error creating enhanced tables: {e}")
        raise

if __name__ == "__main__":
    create_enhanced_tables()
