from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ActivityRecordBase(BaseModel):
    application_name: str
    window_title: str
    url: Optional[str] = None
    category: str
    duration: float
    timestamp: datetime

class ActivityRecordCreate(ActivityRecordBase):
    pass

class ActivityRecord(ActivityRecordBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ActivitySummary(BaseModel):
    application_name: str
    category: str
    total_duration: float
    percentage: float
    urls: Optional[List[str]] = None
