from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Get DATABASE_URL from environment, with SQLite as fallback
DATABASE_URL = os.getenv("DATABASE_URL")

# Debug print (remove this later)
print(f"DEBUG: DATABASE_URL from env: {repr(DATABASE_URL)}")

# Use SQLite as default if no DATABASE_URL or if there's an issue
if not DATABASE_URL or DATABASE_URL == "":
    DATABASE_URL = "sqlite:///./timesheet.db"
    print(f"DEBUG: Using default SQLite: {DATABASE_URL}")

# Create engine with appropriate settings
try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    elif DATABASE_URL.startswith("postgresql"):
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
    else:
        engine = create_engine(DATABASE_URL)
    
    print(f"DEBUG: Engine created successfully with URL: {DATABASE_URL}")
    
except Exception as e:
    print(f"DEBUG: Engine creation failed: {e}")
    print(f"DEBUG: Falling back to SQLite")
    DATABASE_URL = "sqlite:///./timesheet.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Add function to get database connection for testing
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
