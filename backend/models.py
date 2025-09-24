from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, func, Boolean
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    activities = relationship("ActivityRecord", back_populates="user")


class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Multi-developer support (stateless) - Enhanced
    developer_id = Column(String, index=True, nullable=True)  # String identifier, no FK
    developer_name = Column(String(255), index=True, nullable=True)  # Developer display name
    developer_hostname = Column(String(255), nullable=True)  # Hostname of developer machine
    device_id = Column(String(255), nullable=True)  # ActivityWatch device ID
    
    application_name = Column(String, index=True)
    window_title = Column(Text)
    url = Column(Text, nullable=True)  # For browser activities
    file_path = Column(Text, nullable=True)  # For IDE/editor files
    database_connection = Column(String, nullable=True)  # For database tools
    specific_process = Column(String, nullable=True)  # For system processes
    detailed_activity = Column(Text, nullable=True)  # Enhanced description
    category = Column(String, index=True)  # browser, ide, productivity, etc.
    duration = Column(Float)  # Duration in seconds
    timestamp = Column(DateTime(timezone=True))  # Original activity timestamp
    activity_timestamp = Column(DateTime(timezone=True), nullable=True)  # For better querying
    bucket_name = Column(String(255), nullable=True)  # ActivityWatch bucket name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Project information fields
    project_name = Column(String, index=True, nullable=True)  # Extracted project name
    project_type = Column(String, nullable=True)  # Development, Server Management, etc.
    project_file = Column(String, nullable=True)  # File or activity within project

    user = relationship("User", back_populates="activities")


# Optional: Developer model for future use (not required for stateless system)
class Developer(Base):
    __tablename__ = "developers"
    
    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(String, unique=True, index=True)  # Unique identifier
    name = Column(String)
    email = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    api_token = Column(String, unique=True, nullable=True)  # Optional for future use
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)


# Enhanced model for dynamic developer discovery
class DiscoveredDeveloper(Base):
    """Cache discovered developers to avoid repeated network scans"""
    __tablename__ = 'discovered_developers_enhanced'
    
    id = Column(String(255), primary_key=True)  # developer_id
    name = Column(String(255))
    host = Column(String(255))
    port = Column(Integer)
    hostname = Column(String(255))
    device_id = Column(String(255))
    description = Column(Text)
    version = Column(String(50))
    bucket_count = Column(Integer, default=0)
    activity_count = Column(Integer, default=0)
    
    # Status tracking
    status = Column(String(50), default='unknown')  # online, offline, database_only
    last_seen = Column(DateTime(timezone=True))
    last_checked = Column(DateTime(timezone=True))
    
    # Discovery metadata
    source = Column(String(50))  # network, local, database
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
