# database_migration.py - Fixed version that works with your existing database setup

import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.exc import OperationalError, ProgrammingError

# Try to import from your existing database setup
try:
    from database import engine, SessionLocal
    print("Successfully imported database engine")
except ImportError:
    print("Could not import engine from database.py")
    print("Please check your database.py file structure")
    exit(1)

logger = logging.getLogger(__name__)

def check_table_exists(table_name):
    """Check if a table exists"""
    try:
        with engine.connect() as conn:
            result = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            return len(list(result)) > 0
    except:
        # For PostgreSQL/MySQL
        try:
            with engine.connect() as conn:
                result = conn.execute(f"""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                """)
                return len(list(result)) > 0
        except:
            return False

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        with engine.connect() as conn:
            # Try SQLite first
            result = conn.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in result]
            return column_name in columns
    except:
        # Try PostgreSQL/MySQL
        try:
            with engine.connect() as conn:
                result = conn.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = '{column_name}'
                """)
                return len(list(result)) > 0
        except:
            return False

def add_column_safely(table_name, column_name, column_type, default_value=None):
    """Safely add a column to a table if it doesn't exist"""
    try:
        if not check_column_exists(table_name, column_name):
            with engine.connect() as conn:
                if default_value:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'"
                else:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                
                conn.execute(sql)
                conn.commit()  # For some databases
                logger.info(f"Added column {column_name} to {table_name}")
                print(f"✓ Added column {column_name} to {table_name}")
                return True
        else:
            print(f"✓ Column {column_name} already exists in {table_name}")
            return True
    except Exception as e:
        logger.error(f"Failed to add column {column_name} to {table_name}: {e}")
        print(f"✗ Failed to add column {column_name}: {e}")
        return False

def create_index_safely(index_name, table_name, column_name):
    """Safely create an index if it doesn't exist"""
    try:
        with engine.connect() as conn:
            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"
            conn.execute(sql)
            conn.commit()  # For some databases
            logger.info(f"Created index {index_name}")
            return True
    except Exception as e:
        # Index might already exist or database doesn't support IF NOT EXISTS
        try:
            with engine.connect() as conn:
                sql = f"CREATE INDEX {index_name} ON {table_name}({column_name})"
                conn.execute(sql)
                conn.commit()
                logger.info(f"Created index {index_name}")
                return True
        except Exception as e2:
            logger.warning(f"Could not create index {index_name}: {e2}")
            return True  # Don't fail migration for index issues

def migrate_database():
    """Add new columns and tables for dynamic developer discovery"""
    
    print("Starting database migration...")
    
    try:
        # Step 1: Add new columns to activity_records table if it exists
        if check_table_exists('activity_records'):
            print("\n1. Updating activity_records table...")
            
            columns_to_add = [
                ("developer_id", "VARCHAR(255)"),
                ("developer_name", "VARCHAR(255)"),
                ("developer_hostname", "VARCHAR(255)"),
                ("device_id", "VARCHAR(255)"),
                ("bucket_name", "VARCHAR(255)")
            ]
            
            success = True
            for col_name, col_type in columns_to_add:
                if not add_column_safely('activity_records', col_name, col_type):
                    success = False
            
            if success:
                print("✓ Successfully updated activity_records table")
            else:
                print("⚠ Some columns could not be added to activity_records")
        else:
            print("⚠ activity_records table not found - will be created by your existing models")
        
        # Step 2: Create discovered_developers table
        print("\n2. Creating discovered_developers table...")
        
        if not check_table_exists('discovered_developers'):
            Base = declarative_base()
            
            class DiscoveredDeveloper(Base):
                __tablename__ = 'discovered_developers'
                
                id = Column(String(255), primary_key=True)
                name = Column(String(255))
                host = Column(String(255))
                port = Column(Integer)
                hostname = Column(String(255))
                device_id = Column(String(255))
                description = Column(Text)
                version = Column(String(50))
                bucket_count = Column(Integer, default=0)
                activity_count = Column(Integer, default=0)
                
                status = Column(String(50), default='unknown')
                last_seen = Column(DateTime)
                last_checked = Column(DateTime)
                
                source = Column(String(50))
                discovered_at = Column(DateTime, default=func.now())
                is_active = Column(Boolean, default=True)
                
                created_at = Column(DateTime, default=func.now())
                updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
            
            # Create the table
            Base.metadata.create_all(bind=engine)
            print("✓ Created discovered_developers table")
        else:
            print("✓ discovered_developers table already exists")
        
        # Step 3: Create indexes for better performance
        print("\n3. Creating database indexes...")
        
        indexes = [
            ("idx_activity_records_developer_id", "activity_records", "developer_id"),
            ("idx_activity_records_developer_name", "activity_records", "developer_name"),
            ("idx_activity_records_device_id", "activity_records", "device_id"),
            ("idx_activity_records_created_at", "activity_records", "created_at"),
            ("idx_discovered_developers_status", "discovered_developers", "status"),
            ("idx_discovered_developers_source", "discovered_developers", "source"),
            ("idx_discovered_developers_is_active", "discovered_developers", "is_active"),
            ("idx_discovered_developers_last_seen", "discovered_developers", "last_seen"),
        ]
        
        for index_name, table_name, column_name in indexes:
            if check_table_exists(table_name):
                create_index_safely(index_name, table_name, column_name)
        
        print("✓ Database indexes created")
        
        print("\n🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        print(f"\n❌ Migration failed: {e}")
        return False

def populate_existing_data():
    """Populate developer info for existing activity records"""
    print("\nPopulating existing data with default developer info...")
    
    try:
        with engine.connect() as conn:
            # Check if we have any records without developer info
            try:
                result = conn.execute("""
                    SELECT COUNT(*) FROM activity_records 
                    WHERE developer_id IS NULL OR developer_id = ''
                """)
                count = result.fetchone()[0]
                
                if count > 0:
                    # Update existing records with default developer info
                    conn.execute("""
                        UPDATE activity_records 
                        SET developer_id = 'local_default',
                            developer_name = 'Local User',
                            developer_hostname = 'localhost',
                            device_id = 'local_default'
                        WHERE developer_id IS NULL OR developer_id = ''
                    """)
                    
                    # Commit the transaction
                    conn.commit()
                    
                    print(f"✓ Updated {count} existing activity records with default developer info")
                else:
                    print("✓ All activity records already have developer info")
                
            except Exception as e:
                print(f"⚠ Could not update existing records: {e}")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to populate existing data: {e}")
        print(f"❌ Data population failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("DYNAMIC DEVELOPER DISCOVERY - DATABASE MIGRATION")
    print("=" * 60)
    
    if migrate_database():
        print(f"\n{'='*60}")
        print("MIGRATION SUCCESSFUL!")
        
        # Ask if user wants to populate existing data
        response = input("\nDo you want to populate existing activity records with default developer info? (y/n): ")
        if response.lower() in ['y', 'yes']:
            if populate_existing_data():
                print("\n✓ Data population completed!")
            else:
                print("\n⚠ Data population had some issues, but migration was successful")
        
        print(f"\n{'='*60}")
        print("NEXT STEPS:")
        print("1. Add the new Python files (developer_discovery.py, etc.)")
        print("2. Update your app.py with new API endpoints")  
        print("3. Update your models.py with new model classes")
        print("4. Restart your backend server")
        print("5. Test the new discovery features")
        print(f"{'='*60}")
        
    else:
        print(f"\n{'='*60}")
        print("MIGRATION FAILED!")
        print("Please check the error messages above and fix any issues.")
        print("You may need to manually check your database structure.")
        print(f"{'='*60}")