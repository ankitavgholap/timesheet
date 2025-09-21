from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from stateless_webhook import router as stateless_router
import uvicorn
import models, schemas, crud, auth, database
from database import SessionLocal, engine
from my_activitywatch_client import ActivityWatchClient
from productivity_calculator import ProductivityCalculator
from realistic_hours_calculator import RealisticHoursCalculator
from developer_discovery import DeveloperDiscovery
from models import DiscoveredDeveloper, ActivityRecord
from concurrent.futures import ThreadPoolExecutor

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Timesheet API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stateless_router, prefix="/api/v1", tags=["stateless-webhook"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.verify_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/activity-data")
def get_activity_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity data from ActivityWatch and store in database"""
    try:
        aw_client = ActivityWatchClient()
        
        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        # Fetch data from ActivityWatch
        activity_data = aw_client.get_activity_data(start, end)
        
        # Store in database
        for activity in activity_data:
            crud.create_activity_record(db, activity, current_user.id)
        
        # Get processed data for frontend
        processed_data = crud.get_activity_summary(db, current_user.id, start, end)
        
        return {
            "data": processed_data,
            "total_time": sum(item["duration"] for item in processed_data),
            "date_range": {"start": start.isoformat(), "end": end.isoformat()}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activity data: {str(e)}")

@app.get("/activity-summary")
def get_activity_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity summary from database"""
    try:
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        summary = crud.get_activity_summary(db, current_user.id, start, end)
        
        return {
            "data": summary,
            "total_time": sum(item["duration"] for item in summary),
            "date_range": {"start": start.isoformat(), "end": end.isoformat()}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting activity summary: {str(e)}")

@app.get("/productivity-analysis")
def get_productivity_analysis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get productivity analysis for the specified date range"""
    try:
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        calculator = ProductivityCalculator()
        analysis = calculator.calculate_productivity_score_from_activitywatch(start, end)
        
        return {
            "productivity_analysis": analysis,
            "date_range": {"start": start.isoformat(), "end": end.isoformat()}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating productivity: {str(e)}")

@app.get("/daily-hours")
def get_daily_hours(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily working hours report with color coding"""
    try:
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            # Default to last 7 days
            start = datetime.now(timezone.utc) - timedelta(days=7)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        calculator = RealisticHoursCalculator()
        report = calculator.calculate_daily_report(db, current_user.id, start, end)
        
        return {
            "daily_hours_report": report,
            "date_range": {"start": start.isoformat(), "end": end.isoformat()}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating daily hours: {str(e)}")

@app.get("/top-window-titles")
def get_top_window_titles(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    current_user: models.User = Depends(get_current_user)
):
    """Get top window titles by duration from ActivityWatch"""
    try:
        aw_client = ActivityWatchClient()
        
        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.now(timezone.utc)
        
        # Get top window titles from ActivityWatch
        top_titles = aw_client.get_top_window_titles(start, end, limit)
        
        # Format duration for frontend
        for title in top_titles:
            title['duration_formatted'] = f"{title['total_duration'] / 3600:.2f}h"
            title['last_seen_formatted'] = title['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "top_window_titles": top_titles,
            "total_titles": len(top_titles),
            "date_range": {"start": start.isoformat(), "end": end.isoformat()}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top window titles: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
