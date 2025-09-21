# Add this to your existing models.py file

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, func, Boolean

# New Developer model - add this to your models.py
class Developer(Base):
    __tablename__ = "developers"
    
    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(String, unique=True, index=True)  # Unique identifier
    name = Column(String)
    email = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    api_token = Column(String, unique=True)  # For authentication
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    activities = relationship("ActivityRecord", back_populates="developer")

# Update your existing ActivityRecord model by adding these fields:
# Add these columns to your existing ActivityRecord class:

# In your ActivityRecord class, add:
developer_id = Column(String, ForeignKey("developers.developer_id"), nullable=True)
developer = relationship("Developer", back_populates="activities")

# Also make sure your ActivityRecord has these existing fields:
# project_name = Column(String, index=True, nullable=True)  # Already exists
# project_type = Column(String, nullable=True)  # Already exists
