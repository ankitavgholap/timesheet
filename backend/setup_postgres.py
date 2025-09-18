#!/usr/bin/env python3
"""
PostgreSQL database setup script for the timesheet application
This script creates the necessary tables in your existing PostgreSQL database
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import models
from database import Base, engine
import crud
from schemas import UserCreate

load_dotenv()

def setup_database():
    """Set up the database tables and create a test user"""
    print("Setting up PostgreSQL database for Timesheet application...")
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"Connected to PostgreSQL: {version}")
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        
        # Create a session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if we need to create a test user
            existing_users = db.query(models.User).count()
            print(f"Found {existing_users} existing users in database")
            
            if existing_users == 0:
                print("Creating test user...")
                test_user = UserCreate(
                    username="admin",
                    email="admin@timesheet.com",
                    password="admin123"
                )
                user = crud.create_user(db, test_user)
                print(f"✅ Test user created: {user.username} (ID: {user.id})")
                print("You can login with username: admin, password: admin123")
            else:
                print("Users already exist in database")
            
        finally:
            db.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Update your .env file with your PostgreSQL connection string:")
        print("   DATABASE_URL=postgresql://username:password@localhost/your_timesheet_db")
        print("2. Start the backend server: python run_backend.py")
        print("3. Start the frontend: npm start (in frontend directory)")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Ensure the database exists and you have proper permissions")
        sys.exit(1)

def check_existing_tables():
    """Check what tables already exist in the database"""
    print("Checking existing tables...")
    
    try:
        with engine.connect() as conn:
            # Query to get all table names
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"Found {len(tables)} existing tables:")
                for table in tables:
                    print(f"  - {table}")
                    
                # Check if our tables exist
                our_tables = ['users', 'activity_records']
                existing_our_tables = [t for t in tables if t in our_tables]
                
                if existing_our_tables:
                    print(f"\nTimesheet tables already exist: {existing_our_tables}")
                    response = input("Do you want to continue? This will not drop existing data. (y/N): ")
                    if response.lower() != 'y':
                        print("Setup cancelled.")
                        sys.exit(0)
            else:
                print("No tables found in database")
                
    except Exception as e:
        print(f"Warning: Could not check existing tables: {e}")

if __name__ == "__main__":
    print("PostgreSQL Database Setup for Timesheet Application")
    print("=" * 50)
    
    # Check database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please create a .env file with your PostgreSQL connection string:")
        print("DATABASE_URL=postgresql://username:password@localhost/your_database")
        sys.exit(1)
    
    if not database_url.startswith("postgresql"):
        print("❌ DATABASE_URL does not appear to be a PostgreSQL connection string")
        print(f"Current DATABASE_URL: {database_url}")
        print("Expected format: postgresql://username:password@localhost/database_name")
        sys.exit(1)
    
    print(f"Database URL: {database_url}")
    
    # Check existing tables
    check_existing_tables()
    
    # Set up database
    setup_database()
