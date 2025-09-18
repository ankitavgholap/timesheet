from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, func
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
    user_id = Column(Integer, ForeignKey("users.id"))
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
