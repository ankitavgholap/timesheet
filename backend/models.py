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
    
    # Multi-developer support (stateless)
    developer_id = Column(String, index=True, nullable=True)  # String identifier, no FK
    
    application_name = Column(String, index=True)
    window_title = Column(Text)
    url = Column(Text, nullable=True)  # For browser activities
    file_path = Column(Text, nullable=True)  # For IDE/editor files
    database_connection = Column(String, nullable=True)  # For database tools
    specific_process = Column(String, nullable=True)  # For system processes
    detailed_activity = Column(Text, nullable=True)  # Enhanced description
    category = Column(String, index=True)  # browser, ide, productivity, etc.
    duration = Column(Float)  # Duration in seconds
    timestamp = Column(DateTime(timezone=True))
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


# Legacy model (if referenced elsewhere)
class DiscoveredDeveloper(Base):
    __tablename__ = "discovered_developers"
    
    id = Column(Integer, primary_key=True, index=True)
    developer_name = Column(String)
    developer_pattern = Column(String)
    confidence_score = Column(Float)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    activity_count = Column(Integer, default=0)
