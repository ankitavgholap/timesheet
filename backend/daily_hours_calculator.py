#!/usr/bin/env python3
"""
Daily Hours Calculator - Calculate day-wise working hours with color coding
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import models

class DailyHoursCalculator:
    def __init__(self):
        # Working hour thresholds
        self.thresholds = {
            'low': 6.0,      # Less than 6 hours = Red
            'medium': 8.0,   # 6-8 hours = Yellow
            'high': 8.0      # More than 8 hours = Green
        }
        
        # Productive categories (what counts as "work")
        self.productive_categories = {
            'development': 1.0,      # Full working time
            'database': 1.0,         # Full working time
            'productivity': 1.0,     # Full working time
            'browser': 0.7,          # Most browser time is work-related (research, documentation, etc.)
            'system': 0.3,           # Some system work is productive
            'other': 0.4,            # Some other activities are work-related
            'entertainment': 0.0     # Not working time
        }

    def get_status_info(self, hours: float) -> Dict:
        """Get status color and message based on working hours"""
        if hours < self.thresholds['low']:
            return {
                'status': 'low',
                'color': '#ef4444',      # Red
                'background': '#fef2f2', # Light red background
                'message': 'Below target',
                'icon': '🔴'
            }
        elif hours < self.thresholds['medium']:
            return {
                'status': 'medium',
                'color': '#f59e0b',      # Yellow/Orange
                'background': '#fffbeb', # Light yellow background
                'message': 'On track',
                'icon': '🟡'
            }
        else:
            return {
                'status': 'high',
                'color': '#22c55e',      # Green
                'background': '#f0fdf4', # Light green background
                'message': 'Excellent!',
                'icon': '🟢'
            }

    def calculate_daily_hours(self, db: Session, user_id: int, 
                            start_date: datetime, end_date: datetime) -> List[Dict]:
        """Calculate working hours for each day in the date range"""
        
        # Ensure we're working with date boundaries
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get all activities in the date range
        activities = db.query(models.ActivityRecord).filter(
            and_(
                models.ActivityRecord.user_id == user_id,
                models.ActivityRecord.timestamp >= start_date,
                models.ActivityRecord.timestamp <= end_date
            )
        ).order_by(models.ActivityRecord.timestamp.asc()).all()
        
        # Group activities by date
        daily_data = {}
        
        for activity in activities:
            # Get the date (without time)
            activity_date = activity.timestamp.date()
            
            if activity_date not in daily_data:
                daily_data[activity_date] = {
                    'date': activity_date,
                    'total_time': 0.0,
                    'working_time': 0.0,
                    'categories': {},
                    'activities_count': 0
                }
            
            # Add to total time
            daily_data[activity_date]['total_time'] += activity.duration
            daily_data[activity_date]['activities_count'] += 1
            
            # Calculate working time based on category
            category_weight = self.productive_categories.get(activity.category, 0.2)
            working_duration = activity.duration * category_weight
            daily_data[activity_date]['working_time'] += working_duration
            
            # Track category breakdown
            category = activity.category
            if category not in daily_data[activity_date]['categories']:
                daily_data[activity_date]['categories'][category] = {
                    'time': 0.0,
                    'working_time': 0.0,
                    'count': 0
                }
            
            daily_data[activity_date]['categories'][category]['time'] += activity.duration
            daily_data[activity_date]['categories'][category]['working_time'] += working_duration
            daily_data[activity_date]['categories'][category]['count'] += 1
        
        # Convert to list and add status information
        result = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            if current_date in daily_data:
                day_data = daily_data[current_date]
                working_hours = day_data['working_time'] / 3600  # Convert to hours
                total_hours = day_data['total_time'] / 3600
                
                status_info = self.get_status_info(working_hours)
                
                day_data.update({
                    'working_hours': round(working_hours, 2),
                    'total_hours': round(total_hours, 2),
                    'productivity_percentage': round((working_hours / total_hours * 100) if total_hours > 0 else 0, 1),
                    'status': status_info['status'],
                    'status_color': status_info['color'],
                    'status_background': status_info['background'],
                    'status_message': status_info['message'],
                    'status_icon': status_info['icon']
                })
                
                result.append(day_data)
            else:
                # No activity for this day
                status_info = self.get_status_info(0)
                result.append({
                    'date': current_date,
                    'total_time': 0.0,
                    'working_time': 0.0,
                    'working_hours': 0.0,
                    'total_hours': 0.0,
                    'productivity_percentage': 0.0,
                    'categories': {},
                    'activities_count': 0,
                    'status': status_info['status'],
                    'status_color': status_info['color'],
                    'status_background': status_info['background'],
                    'status_message': 'No activity',
                    'status_icon': '⚪'
                })
            
            current_date += timedelta(days=1)
        
        return result

    def get_weekly_summary(self, daily_data: List[Dict]) -> Dict:
        """Calculate weekly summary from daily data"""
        if not daily_data:
            return {
                'total_days': 0,
                'working_days': 0,
                'avg_working_hours': 0.0,
                'total_working_hours': 0.0,
                'days_above_target': 0,
                'days_on_track': 0,
                'days_below_target': 0,
                'best_day': None,
                'worst_day': None
            }
        
        total_working_hours = sum(day['working_hours'] for day in daily_data)
        working_days = len([day for day in daily_data if day['working_hours'] > 0])
        
        days_above_target = len([day for day in daily_data if day['status'] == 'high'])
        days_on_track = len([day for day in daily_data if day['status'] == 'medium'])
        days_below_target = len([day for day in daily_data if day['status'] == 'low'])
        
        # Find best and worst days
        best_day = max(daily_data, key=lambda x: x['working_hours']) if daily_data else None
        worst_day = min([day for day in daily_data if day['working_hours'] > 0], 
                       key=lambda x: x['working_hours'], default=None)
        
        return {
            'total_days': len(daily_data),
            'working_days': working_days,
            'avg_working_hours': round(total_working_hours / len(daily_data), 2) if daily_data else 0,
            'total_working_hours': round(total_working_hours, 2),
            'days_above_target': days_above_target,
            'days_on_track': days_on_track,
            'days_below_target': days_below_target,
            'best_day': {
                'date': best_day['date'].strftime('%Y-%m-%d'),
                'hours': best_day['working_hours']
            } if best_day else None,
            'worst_day': {
                'date': worst_day['date'].strftime('%Y-%m-%d'),
                'hours': worst_day['working_hours']
            } if worst_day else None
        }

    def calculate_daily_report(self, db: Session, user_id: int, 
                             start_date: datetime, end_date: datetime) -> Dict:
        """Generate complete daily hours report"""
        daily_data = self.calculate_daily_hours(db, user_id, start_date, end_date)
        weekly_summary = self.get_weekly_summary(daily_data)
        
        # Convert dates to strings for JSON serialization
        for day in daily_data:
            day['date'] = day['date'].strftime('%Y-%m-%d')
        
        return {
            'daily_data': daily_data,
            'summary': weekly_summary,
            'thresholds': self.thresholds,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
