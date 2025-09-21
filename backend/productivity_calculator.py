#!/usr/bin/env python3
"""
Productivity Calculator - Analyze user productivity based on activity patterns
"""
from datetime import datetime
from typing import Dict, List

import models
from my_activitywatch_client import ActivityWatchClient
from sqlalchemy import and_
from sqlalchemy.orm import Session


class ProductivityCalculator:
    def __init__(self):
        # Productivity weights for different categories
        self.category_weights = {
            'development': 1.0,  # Highly productive (IDE work)
            'productivity': 0.95,  # Very productive  
            'database': 0.95,  # Very productive (database work)
            'browser': 0.2,  # Low productivity (YouTube, mail, social media)
            'entertainment': 0.0,  # Not productive at all
            'system': 0.1,  # Minimal productivity
            'other': 0.15  # Low productivity
        }

        # Time-based productivity multipliers
        self.time_multipliers = {
            'peak_hours': 1.2,  # 9 AM - 5 PM
            'evening': 0.9,  # 5 PM - 9 PM
            'night': 0.7,  # 9 PM - 11 PM
            'late_night': 0.5  # 11 PM - 6 AM
        }

        # Focus session bonuses (continuous work on same category)
        self.focus_bonuses = {
            'short_focus': 1.1,  # 30-60 minutes
            'medium_focus': 1.2,  # 1-2 hours
            'long_focus': 1.3,  # 2+ hours
            'deep_focus': 1.5  # 3+ hours
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

    def get_time_category(self, timestamp: datetime) -> str:
        """Categorize time of day for productivity analysis"""
        hour = timestamp.hour

        if 9 <= hour < 17:
            return 'peak_hours'
        elif 17 <= hour < 21:
            return 'evening'
        elif 21 <= hour < 23:
            return 'night'
        else:
            return 'late_night'

    def calculate_focus_sessions(self, activities: List[models.ActivityRecord]) -> List[Dict]:
        """Identify focus sessions (continuous work on same category)"""
        if not activities:
            return []

        focus_sessions = []
        current_session = {
            'category': activities[0].category,
            'start_time': activities[0].timestamp,
            'end_time': activities[0].timestamp,
            'duration': activities[0].duration,
            'activities': [activities[0]]
        }

        for i in range(1, len(activities)):
            activity = activities[i]
            prev_activity = activities[i - 1]

            # Check if this continues the current session
            time_gap = abs((activity.timestamp - prev_activity.timestamp).total_seconds())
            same_category = activity.category == current_session['category']

            # If gap is less than 5 minutes and same category, continue session
            if time_gap <= 300 and same_category:
                current_session['end_time'] = activity.timestamp
                current_session['duration'] += activity.duration
                current_session['activities'].append(activity)
            else:
                # End current session and start new one
                if current_session['duration'] >= 1800:  # At least 30 minutes
                    focus_sessions.append(current_session.copy())

                current_session = {
                    'category': activity.category,
                    'start_time': activity.timestamp,
                    'end_time': activity.timestamp,
                    'duration': activity.duration,
                    'activities': [activity]
                }

        # Add the last session if it's long enough
        if current_session['duration'] >= 1800:
            focus_sessions.append(current_session)

        return focus_sessions

    def get_focus_bonus(self, duration_seconds: float) -> float:
        """Get focus bonus multiplier based on session duration"""
        duration_minutes = duration_seconds / 60

        if duration_minutes >= 180:  # 3+ hours
            return self.focus_bonuses['deep_focus']
        elif duration_minutes >= 120:  # 2+ hours
            return self.focus_bonuses['long_focus']
        elif duration_minutes >= 60:  # 1+ hours
            return self.focus_bonuses['medium_focus']
        elif duration_minutes >= 30:  # 30+ minutes
            return self.focus_bonuses['short_focus']
        else:
            return 1.0

    def calculate_productivity_score_from_activitywatch(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate productivity score directly from ActivityWatch data"""
        aw_client = ActivityWatchClient()

        try:
            activity_data = aw_client.get_activity_data(start_date, end_date)
        except Exception as e:
            print(f"Error fetching ActivityWatch data: {e}")
            return {
                'overall_score': 0,
                'total_time': 0,
                'productive_time': 0,
                'total_time_formatted': '0h',
                'productive_time_formatted': '0h',
                'productivity_percentage': 0,
                'category_breakdown': {},
                'focus_sessions': 0,
                'longest_focus_session': 0,
                'longest_focus_session_formatted': '0h',
                'average_focus_session': 0,
                'average_focus_session_formatted': '0h',
                'recommendations': ['Error fetching ActivityWatch data.']
            }

        if not activity_data:
            return {
                'overall_score': 0,
                'total_time': 0,
                'productive_time': 0,
                'total_time_formatted': '0h',
                'productive_time_formatted': '0h',
                'productivity_percentage': 0,
                'category_breakdown': {},
                'focus_sessions': 0,
                'longest_focus_session': 0,
                'longest_focus_session_formatted': '0h',
                'average_focus_session': 0,
                'average_focus_session_formatted': '0h',
                'recommendations': ['No activity data available for this period.']
            }

        # Convert ActivityWatch data to mock activities for existing logic
        mock_activities = []
        for activity in activity_data:
            mock_activity = type('MockActivity', (), {
                'category': activity['category'],
                'duration': activity['duration'],
                'application_name': activity['application_name'],
                'timestamp': activity['timestamp']
            })()
            mock_activities.append(mock_activity)

        return self.calculate_productivity_score(None, None, start_date, end_date, mock_activities)

    def calculate_productivity_score(self, db: Session, user_id: int,
                                     start_date: datetime, end_date: datetime, activities=None) -> Dict:
        """Calculate comprehensive productivity score"""

        # Get all activities for the period (use provided activities or fetch from DB)
        if activities is None:
            activities = db.query(models.ActivityRecord).filter(
                and_(
                    models.ActivityRecord.user_id == user_id,
                    models.ActivityRecord.timestamp >= start_date,
                    models.ActivityRecord.timestamp <= end_date
                )
            ).order_by(models.ActivityRecord.timestamp.asc()).all()

        if not activities:
            return {
                'overall_score': 0,
                'total_time': 0,
                'productive_time': 0,
                'productivity_percentage': 0,
                'category_breakdown': {},
                'focus_sessions': [],
                'recommendations': ['No activity data available for this period.']
            }

        total_time = sum(activity.duration for activity in activities)
        productive_time = 0
        category_scores = {}
        category_times = {}

        # Calculate base productivity scores
        for activity in activities:
            category = activity.category
            duration = activity.duration

            # Get base productivity weight
            base_weight = self.category_weights.get(category, 0.2)

            # Apply time-based multiplier
            time_category = self.get_time_category(activity.timestamp)
            time_multiplier = self.time_multipliers.get(time_category, 1.0)

            # Calculate weighted productivity time
            weighted_time = duration * base_weight * time_multiplier
            productive_time += weighted_time

            # Track by category
            if category not in category_scores:
                category_scores[category] = 0
                category_times[category] = 0

            category_scores[category] += weighted_time
            category_times[category] += duration

        # Calculate focus sessions and apply bonuses
        focus_sessions = self.calculate_focus_sessions(activities)
        focus_bonus_time = 0

        for session in focus_sessions:
            focus_bonus = self.get_focus_bonus(session['duration'])
            base_weight = self.category_weights.get(session['category'], 0.2)
            bonus_time = session['duration'] * base_weight * (focus_bonus - 1.0)
            focus_bonus_time += bonus_time

        productive_time += focus_bonus_time

        # Calculate overall productivity percentage
        productivity_percentage = (productive_time / total_time * 100) if total_time > 0 else 0

        # Calculate overall score (0-100)
        overall_score = min(100, productivity_percentage)

        # Create category breakdown
        category_breakdown = {}
        for category, score in category_scores.items():
            category_breakdown[category] = {
                'time_spent': category_times[category],
                'productive_time': score,
                'productivity_rate': (score / category_times[category] * 100) if category_times[category] > 0 else 0,
                'percentage_of_total': (category_times[category] / total_time * 100) if total_time > 0 else 0
            }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score, category_breakdown, focus_sessions, total_time
        )

        return {
            'overall_score': round(overall_score, 1),
            'total_time': total_time,
            'productive_time': productive_time,
            'total_time_formatted': self.format_time_readable(total_time / 3600),
            'productive_time_formatted': self.format_time_readable(productive_time / 3600),
            'productivity_percentage': round(productivity_percentage, 1),
            'category_breakdown': category_breakdown,
            'focus_sessions': len(focus_sessions),
            'longest_focus_session': max([s['duration'] for s in focus_sessions]) if focus_sessions else 0,
            'longest_focus_session_formatted': self.format_time_readable(
                max([s['duration'] for s in focus_sessions]) / 3600) if focus_sessions else '0h',
            'average_focus_session': sum([s['duration'] for s in focus_sessions]) / len(
                focus_sessions) if focus_sessions else 0,
            'average_focus_session_formatted': self.format_time_readable((sum([s['duration'] for s in
                                                                               focus_sessions]) / len(
                focus_sessions)) / 3600) if focus_sessions else '0h',
            'recommendations': recommendations,
            'time_distribution': self._get_time_distribution(activities),
            'productivity_trend': self._get_productivity_trend(activities)
        }

    def _generate_recommendations(self, score: float, categories: Dict,
                                  focus_sessions: List, total_time: float) -> List[str]:
        """Generate personalized productivity recommendations"""
        recommendations = []

        # Overall score recommendations
        if score < 30:
            recommendations.append("🔴 Low productivity detected. Consider reducing distracting activities.")
        elif score < 60:
            recommendations.append("🟡 Moderate productivity. There's room for improvement.")
        else:
            recommendations.append("🟢 Good productivity! Keep up the excellent work.")

        # Category-specific recommendations
        browser_time = categories.get('browser', {}).get('time_spent', 0)
        entertainment_time = categories.get('entertainment', {}).get('time_spent', 0)

        if browser_time > total_time * 0.3:
            recommendations.append("🌐 High browser usage detected. Consider using website blockers during work hours.")

        if entertainment_time > total_time * 0.2:
            recommendations.append("🎮 Significant entertainment time. Try scheduling specific break times.")

        # Focus session recommendations
        if len(focus_sessions) < 2:
            recommendations.append("🎯 Try to create longer focus sessions (30+ minutes) for better productivity.")
        elif len(focus_sessions) > 8:
            recommendations.append("⚡ Many short sessions detected. Consider consolidating work into longer blocks.")

        # Development-specific recommendations
        dev_time = categories.get('development', {}).get('time_spent', 0)
        if dev_time > 0:
            if dev_time < total_time * 0.4:
                recommendations.append("💻 Consider dedicating more time to focused development work.")
            else:
                recommendations.append("💻 Great development focus! You're spending quality time coding.")

        return recommendations

    def _get_time_distribution(self, activities: List[models.ActivityRecord]) -> Dict:
        """Get time distribution across different hours of the day"""
        hour_distribution = {}

        for activity in activities:
            hour = activity.timestamp.hour
            if hour not in hour_distribution:
                hour_distribution[hour] = 0
            hour_distribution[hour] += activity.duration

        return hour_distribution

    def _get_productivity_trend(self, activities: List[models.ActivityRecord]) -> Dict:
        """Calculate productivity trend over time"""
        if not activities:
            return {'trend': 'stable', 'change': 0}

        # Split activities into first and second half
        mid_point = len(activities) // 2
        first_half = activities[:mid_point]
        second_half = activities[mid_point:]

        def calc_half_productivity(half_activities):
            if not half_activities:
                return 0

            total_time = sum(a.duration for a in half_activities)
            productive_time = sum(
                a.duration * self.category_weights.get(a.category, 0.2)
                for a in half_activities
            )
            return (productive_time / total_time * 100) if total_time > 0 else 0

        first_productivity = calc_half_productivity(first_half)
        second_productivity = calc_half_productivity(second_half)

        change = second_productivity - first_productivity

        if abs(change) < 5:
            trend = 'stable'
        elif change > 0:
            trend = 'improving'
        else:
            trend = 'declining'

        return {'trend': trend, 'change': round(change, 1)}
