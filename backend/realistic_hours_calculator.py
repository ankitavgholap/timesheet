#!/usr/bin/env python3
"""
Realistic Hours Calculator - More accurate working hours calculation
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import models
from my_activitywatch_client import ActivityWatchClient

class RealisticHoursCalculator:
    def __init__(self):
        # Working hour thresholds
        self.thresholds = {
            'low': 6.0,      # Less than 6 hours = Red
            'medium': 8.0,   # 6-8 hours = Yellow
            'high': 8.0      # More than 8 hours = Green
        }
    
    def format_time_readable(self, hours: float) -> str:
        """Convert decimal hours to readable format (e.g., 5.5 -> '5h 30m')"""
        if hours == 0:
            return '0h'
        
        total_minutes = int(hours * 60)
        hours_part = total_minutes // 60
        minutes_part = total_minutes % 60
        
        if hours_part == 0:
            return f'{minutes_part}m'
        elif minutes_part == 0:
            return f'{hours_part}h'
        else:
            return f'{hours_part}h {minutes_part}m'

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

    def calculate_realistic_working_hours(self, activities: List[models.ActivityRecord]) -> Dict:
        """Calculate realistic working hours based on activity patterns"""
        if not activities:
            return {
                'working_hours': 0.0,
                'total_hours': 0.0,
                'breakdown': {}
            }
        
        category_data = {}
        total_time = 0
        
        # Group activities by category
        for activity in activities:
            category = activity.category
            duration = activity.duration
            total_time += duration
            
            if category not in category_data:
                category_data[category] = {
                    'total_time': 0,
                    'count': 0,
                    'apps': {}
                }
            
            category_data[category]['total_time'] += duration
            category_data[category]['count'] += 1
            
            # Track specific apps
            app_name = activity.application_name
            if app_name not in category_data[category]['apps']:
                category_data[category]['apps'][app_name] = 0
            category_data[category]['apps'][app_name] += duration
        
        # Calculate working hours using realistic approach
        working_time = 0
        breakdown = {}
        
        for category, data in category_data.items():
            cat_time = data['total_time']
            cat_hours = cat_time / 3600
            
            if category == 'development':
                # All development time counts as work
                working_hours = cat_hours
                working_time += cat_time
                breakdown[category] = {
                    'total_hours': cat_hours,
                    'working_hours': working_hours,
                    'percentage': 100,
                    'reason': 'All coding/development work'
                }
            
            elif category == 'database':
                # All database work counts as work
                working_hours = cat_hours
                working_time += cat_time
                breakdown[category] = {
                    'total_hours': cat_hours,
                    'working_hours': working_hours,
                    'percentage': 100,
                    'reason': 'All database work'
                }
            
            elif category == 'productivity':
                # All productivity tools count as work
                working_hours = cat_hours
                working_time += cat_time
                breakdown[category] = {
                    'total_hours': cat_hours,
                    'working_hours': working_hours,
                    'percentage': 100,
                    'reason': 'All productivity tools'
                }
            
            elif category == 'browser':
                # Smart browser analysis
                work_percentage = self.analyze_browser_usage(data['apps'])
                working_hours = cat_hours * (work_percentage / 100)
                working_time += cat_time * (work_percentage / 100)
                breakdown[category] = {
                    'total_hours': cat_hours,
                    'working_hours': working_hours,
                    'percentage': work_percentage,
                    'reason': f'{work_percentage}% estimated work-related browsing'
                }
            
            elif category == 'other':
                # Some "other" activities might be work-related
                # Look for specific work-related apps
                work_percentage = self.analyze_other_usage(data['apps'])
                working_hours = cat_hours * (work_percentage / 100)
                working_time += cat_time * (work_percentage / 100)
                breakdown[category] = {
                    'total_hours': cat_hours,
                    'working_hours': working_hours,
                    'percentage': work_percentage,
                    'reason': f'{work_percentage}% estimated work-related activities'
                }
            
            else:
                # System, entertainment, etc. - minimal working time
                working_hours = cat_hours * 0.1  # 10% might be work-related
                working_time += cat_time * 0.1
                breakdown[category] = {
                    'total_hours': cat_hours,
                    'working_hours': working_hours,
                    'percentage': 10,
                    'reason': 'Minimal work-related time'
                }
        
        return {
            'working_hours': working_time / 3600,
            'total_hours': total_time / 3600,
            'breakdown': breakdown
        }

    def analyze_browser_usage(self, apps: Dict[str, float]) -> int:
        """Analyze browser usage to determine work percentage"""
        # For developers, most browser time is work-related:
        # - Documentation, Stack Overflow, GitHub
        # - Testing web applications
        # - Research and learning
        # Only entertainment sites like YouTube should be excluded
        return 85  # 85% of browser time is work-related for developers

    def analyze_other_usage(self, apps: Dict[str, float]) -> int:
        """Analyze 'other' category apps to determine work percentage"""
        work_related_apps = [
            'datagrip64.exe',  # Database tool
            'Postman.exe',     # API testing
            'SnippingTool.exe', # Screenshots for work
            'LockApp.exe'      # Screen lock (break time, but still work session)
        ]
        
        total_time = sum(apps.values())
        work_time = 0
        
        for app, time in apps.items():
            if 'datagrip' in app.lower() or 'postman' in app.lower():
                work_time += time * 1.0  # 100% work time
            elif 'snipping' in app.lower():
                work_time += time * 0.9  # 90% work time
            elif 'lockapp' in app.lower():
                work_time += time * 0.9  # 90% - breaks during work session are still work time
            else:
                work_time += time * 0.5  # 50% of other apps might be work (more generous)
        
        if total_time > 0:
            return int((work_time / total_time) * 100)
        return 50  # Default 50% (more generous)

    def calculate_daily_hours_from_activitywatch(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Calculate daily hours directly from ActivityWatch data"""
        aw_client = ActivityWatchClient()
        
        # Ensure we're working with date boundaries
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get all activities from ActivityWatch
        try:
            activity_data = aw_client.get_activity_data(start_date, end_date)
        except Exception as e:
            print(f"Error fetching ActivityWatch data: {e}")
            return []
        
        # Group activities by date
        daily_activities = {}
        
        for activity in activity_data:
            activity_date = activity['timestamp'].date()
            if activity_date not in daily_activities:
                daily_activities[activity_date] = []
            daily_activities[activity_date].append(activity)
        
        # Calculate for each day
        result = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            if current_date in daily_activities:
                day_activities = daily_activities[current_date]
                
                # Convert ActivityWatch data to our format for calculation
                mock_activities = []
                for activity in day_activities:
                    # Create a mock ActivityRecord-like object
                    mock_activity = type('MockActivity', (), {
                        'category': activity['category'],
                        'duration': activity['duration'],
                        'application_name': activity['application_name'],
                        'timestamp': activity['timestamp']
                    })()
                    mock_activities.append(mock_activity)
                
                hours_data = self.calculate_realistic_working_hours(mock_activities)
                
                working_hours = hours_data['working_hours']
                total_hours = hours_data['total_hours']
                status_info = self.get_status_info(working_hours)
                
                result.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'working_hours': round(working_hours, 2),
                    'total_hours': round(total_hours, 2),
                    'working_hours_formatted': self.format_time_readable(working_hours),
                    'total_hours_formatted': self.format_time_readable(total_hours),
                    'productivity_percentage': round((working_hours / total_hours * 100) if total_hours > 0 else 0, 1),
                    'activities_count': len(day_activities),
                    'status': status_info['status'],
                    'status_color': status_info['color'],
                    'status_background': status_info['background'],
                    'status_message': status_info['message'],
                    'status_icon': status_info['icon'],
                    'breakdown': hours_data['breakdown']
                })
            else:
                # No activity for this day
                status_info = self.get_status_info(0)
                result.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'working_hours': 0.0,
                    'total_hours': 0.0,
                    'working_hours_formatted': '0h',
                    'total_hours_formatted': '0h',
                    'productivity_percentage': 0.0,
                    'activities_count': 0,
                    'status': status_info['status'],
                    'status_color': status_info['color'],
                    'status_background': status_info['background'],
                    'status_message': 'No activity',
                    'status_icon': '⚪',
                    'breakdown': {}
                })
            
            current_date += timedelta(days=1)
        
        return result

    def calculate_daily_hours(self, db: Session, user_id: int, 
                            start_date: datetime, end_date: datetime) -> List[Dict]:
        """Calculate realistic working hours for each day"""
        
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
        daily_activities = {}
        
        for activity in activities:
            activity_date = activity.timestamp.date()
            if activity_date not in daily_activities:
                daily_activities[activity_date] = []
            daily_activities[activity_date].append(activity)
        
        # Calculate for each day
        result = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            if current_date in daily_activities:
                day_activities = daily_activities[current_date]
                hours_data = self.calculate_realistic_working_hours(day_activities)
                
                working_hours = hours_data['working_hours']
                total_hours = hours_data['total_hours']
                status_info = self.get_status_info(working_hours)
                
                result.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'working_hours': round(working_hours, 2),
                    'total_hours': round(total_hours, 2),
                    'working_hours_formatted': self.format_time_readable(working_hours),
                    'total_hours_formatted': self.format_time_readable(total_hours),
                    'productivity_percentage': round((working_hours / total_hours * 100) if total_hours > 0 else 0, 1),
                    'activities_count': len(day_activities),
                    'status': status_info['status'],
                    'status_color': status_info['color'],
                    'status_background': status_info['background'],
                    'status_message': status_info['message'],
                    'status_icon': status_info['icon'],
                    'breakdown': hours_data['breakdown']
                })
            else:
                # No activity for this day
                status_info = self.get_status_info(0)
                result.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'working_hours': 0.0,
                    'total_hours': 0.0,
                    'working_hours_formatted': '0h',
                    'total_hours_formatted': '0h',
                    'productivity_percentage': 0.0,
                    'activities_count': 0,
                    'status': status_info['status'],
                    'status_color': status_info['color'],
                    'status_background': status_info['background'],
                    'status_message': 'No activity',
                    'status_icon': '⚪',
                    'breakdown': {}
                })
            
            current_date += timedelta(days=1)
        
        return result

    def get_summary(self, daily_data: List[Dict]) -> Dict:
        """Calculate summary from daily data"""
        if not daily_data:
            return {
                'total_days': 0,
                'working_days': 0,
                'avg_working_hours': 0.0,
                'total_working_hours': 0.0,
                'days_above_target': 0,
                'days_on_track': 0,
                'days_below_target': 0,
                'best_day': None
            }
        
        total_working_hours = sum(day['working_hours'] for day in daily_data)
        working_days = len([day for day in daily_data if day['working_hours'] > 0])
        
        days_above_target = len([day for day in daily_data if day['status'] == 'high'])
        days_on_track = len([day for day in daily_data if day['status'] == 'medium'])
        days_below_target = len([day for day in daily_data if day['status'] == 'low'])
        
        best_day = max(daily_data, key=lambda x: x['working_hours']) if daily_data else None
        
        return {
            'total_days': len(daily_data),
            'working_days': working_days,
            'avg_working_hours': round(total_working_hours / len(daily_data), 2) if daily_data else 0,
            'total_working_hours': round(total_working_hours, 2),
            'days_above_target': days_above_target,
            'days_on_track': days_on_track,
            'days_below_target': days_below_target,
            'best_day': {
                'date': best_day['date'],
                'hours': best_day['working_hours']
            } if best_day else None
        }

    def calculate_daily_report(self, db: Session, user_id: int, 
                             start_date: datetime, end_date: datetime) -> Dict:
        """Generate complete realistic daily hours report from ActivityWatch data"""
        # Use ActivityWatch data instead of database records
        daily_data = self.calculate_daily_hours_from_activitywatch(start_date, end_date)
        summary = self.get_summary(daily_data)
        
        return {
            'daily_data': daily_data,
            'summary': summary,
            'thresholds': self.thresholds,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
