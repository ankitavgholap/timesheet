#!/usr/bin/env python3
"""
Database Migration Script
Adds multi-developer support to existing timesheet database
"""

import os
import sys
from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please ensure .env file exists with DATABASE_URL")
        sys.exit(1)
    return db_url

def run_migration():
    """Run database migration to add developer support"""
    print("🚀 Starting database migration for multi-developer support...")
    
    # Get database connection
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            print("✅ Connected to database successfully")
            
            # Create developers table
            print("📊 Creating developers table...")
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS developers (
                    id SERIAL PRIMARY KEY,
                    developer_id VARCHAR UNIQUE NOT NULL,
                    name VARCHAR NOT NULL,
                    email VARCHAR,
                    active BOOLEAN DEFAULT TRUE,
                    api_token VARCHAR UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_sync TIMESTAMP
                );
            '''))
            print("✅ Developers table created/verified")
            
            # Add developer_id column to activity_records if it doesn't exist
            print("🔗 Adding developer_id column to activity_records...")
            try:
                conn.execute(text('''
                    ALTER TABLE activity_records 
                    ADD COLUMN developer_id VARCHAR;
                '''))
                print("✅ Added developer_id column to activity_records")
            except SQLAlchemyError as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("ℹ️  developer_id column already exists in activity_records")
                else:
                    print(f"⚠️  Error adding developer_id column: {e}")
            
            # Create indexes for performance
            print("🎯 Creating database indexes...")
            
            # Index on developers.developer_id
            try:
                conn.execute(text('''
                    CREATE INDEX IF NOT EXISTS idx_developers_developer_id 
                    ON developers(developer_id);
                '''))
                print("✅ Created index on developers.developer_id")
            except SQLAlchemyError as e:
                print(f"⚠️  Index creation warning: {e}")
            
            # Index on developers.api_token
            try:
                conn.execute(text('''
                    CREATE INDEX IF NOT EXISTS idx_developers_api_token 
                    ON developers(api_token);
                '''))
                print("✅ Created index on developers.api_token")
            except SQLAlchemyError as e:
                print(f"⚠️  Index creation warning: {e}")
            
            # Index on activity_records.developer_id
            try:
                conn.execute(text('''
                    CREATE INDEX IF NOT EXISTS idx_activity_records_developer_id 
                    ON activity_records(developer_id);
                '''))
                print("✅ Created index on activity_records.developer_id")
            except SQLAlchemyError as e:
                print(f"⚠️  Index creation warning: {e}")
            
            # Index on activity_records timestamp for better performance
            try:
                conn.execute(text('''
                    CREATE INDEX IF NOT EXISTS idx_activity_records_timestamp 
                    ON activity_records(timestamp);
                '''))
                print("✅ Created index on activity_records.timestamp")
            except SQLAlchemyError as e:
                print(f"⚠️  Index creation warning: {e}")
            
            # Commit all changes
            conn.commit()
            print("✅ All database changes committed successfully")
            
            # Verify table structure
            print("🔍 Verifying table structure...")
            
            # Check developers table
            result = conn.execute(text('''
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'developers'
                ORDER BY ordinal_position;
            '''))
            
            developers_columns = result.fetchall()
            if developers_columns:
                print("✅ Developers table structure:")
                for col in developers_columns:
                    print(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("⚠️  Could not verify developers table structure")
            
            # Check if activity_records has developer_id column
            result = conn.execute(text('''
                SELECT column_name
                FROM information_schema.columns 
                WHERE table_name = 'activity_records' AND column_name = 'developer_id';
            '''))
            
            if result.fetchone():
                print("✅ activity_records.developer_id column verified")
            else:
                print("❌ activity_records.developer_id column missing")
            
            # Show current record counts
            print("\n📊 Current database statistics:")
            
            result = conn.execute(text("SELECT COUNT(*) FROM users;"))
            user_count = result.scalar()
            print(f"   - Users: {user_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM developers;"))
            dev_count = result.scalar()
            print(f"   - Developers: {dev_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM activity_records;"))
            activity_count = result.scalar()
            print(f"   - Activity Records: {activity_count}")
            
            result = conn.execute(text('''
                SELECT COUNT(*) FROM activity_records WHERE developer_id IS NOT NULL;
            '''))
            dev_activity_count = result.scalar()
            print(f"   - Activity Records with Developer ID: {dev_activity_count}")
            
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def create_sample_developer():
    """Create a sample developer for testing"""
    print("\n🧪 Creating sample developer for testing...")
    
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    import secrets
    
    try:
        with engine.connect() as conn:
            # Check if sample developer already exists
            result = conn.execute(text('''
                SELECT developer_id FROM developers WHERE developer_id = 'sample_dev';
            '''))
            
            if result.fetchone():
                print("ℹ️  Sample developer already exists")
                return
            
            # Generate sample API token
            api_token = secrets.token_urlsafe(32)
            
            # Insert sample developer
            conn.execute(text('''
                INSERT INTO developers (developer_id, name, email, api_token, active, created_at)
                VALUES (:dev_id, :name, :email, :token, :active, NOW());
            '''), {
                'dev_id': 'sample_dev',
                'name': 'Sample Developer',
                'email': 'sample@company.com',
                'token': api_token,
                'active': True
            })
            
            conn.commit()
            
            print("✅ Sample developer created successfully!")
            print(f"   - Developer ID: sample_dev")
            print(f"   - API Token: {api_token}")
            print(f"   - Name: Sample Developer")
            print("\n💡 You can use these credentials to test the sync client")
            
    except SQLAlchemyError as e:
        print(f"❌ Error creating sample developer: {e}")

def main():
    """Main migration function"""
    print("=" * 60)
    print("🔄 TIMESHEET DATABASE MIGRATION")
    print("   Adding Multi-Developer Support")
    print("=" * 60)
    
    # Run the migration
    run_migration()
    
    # Ask if user wants to create sample developer
    print("\n" + "=" * 60)
    response = input("Create a sample developer for testing? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        create_sample_developer()
    
    print("\n" + "=" * 60)
    print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print("\nNext steps:")
    print("1. Update your backend/main.py to include multi_developer_api routes")
    print("2. Update your models.py to include the Developer model")
    print("3. Restart your backend service")
    print("4. Test developer registration with admin token")
    print("5. Distribute sync clients to team members")
    print("=" * 60)

if __name__ == "__main__":
    main()
