import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Calendar, 
  Clock, 
  TrendingUp, 
  Target, 
  Award,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

function DailyHoursReport({ startDate, endDate }) {
  const [dailyHoursData, setDailyHoursData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    fetchDailyHours();
  }, [startDate, endDate]);

  const fetchDailyHours = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/daily-hours', {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });
      setDailyHoursData(response.data.daily_hours_report);
    } catch (error) {
      console.error('Error fetching daily hours:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'high':
        return <CheckCircle size={16} color="#22c55e" />;
      case 'medium':
        return <AlertTriangle size={16} color="#f59e0b" />;
      case 'low':
        return <Target size={16} color="#ef4444" />;
      default:
        return <Clock size={16} color="#6b7280" />;
    }
  };

  const containerStyle = {
    padding: '20px',
    background: '#fff',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    marginBottom: '20px'
  };

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    cursor: 'pointer',
    paddingBottom: '16px',
    borderBottom: isExpanded ? '2px solid #e5e7eb' : 'none'
  };

  const summaryGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
    marginBottom: '24px'
  };

  const summaryCardStyle = {
    padding: '16px',
    background: '#f9fafb',
    borderRadius: '8px',
    textAlign: 'center',
    border: '1px solid #e5e7eb'
  };

  const dailyGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '12px'
  };

  if (loading) {
    return (
      <div style={containerStyle}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: '16px', color: '#666' }}>Loading daily hours...</p>
        </div>
      </div>
    );
  }

  if (!dailyHoursData) {
    return (
      <div style={containerStyle}>
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          <BarChart3 size={48} color="#ccc" style={{ marginBottom: '16px' }} />
          <p>No daily hours data available</p>
        </div>
      </div>
    );
  }

  const { daily_data, summary } = dailyHoursData;

  return (
    <div style={containerStyle}>
      <div style={headerStyle} onClick={() => setIsExpanded(!isExpanded)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Calendar size={24} color="#667eea" />
          <h2 style={{ margin: 0, color: '#333' }}>Daily Working Hours</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px', color: '#666' }}>
            {summary.working_days} working days
          </span>
          {isExpanded ? 
            <ChevronUp size={20} color="#667eea" /> : 
            <ChevronDown size={20} color="#667eea" />
          }
        </div>
      </div>

      {/* Always show summary */}
      <div style={summaryGridStyle}>
        <div style={summaryCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
            <Clock size={20} color="#667eea" />
            <span style={{ fontWeight: '600', color: '#333' }}>Avg Hours</span>
          </div>
          <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#667eea', margin: 0 }}>
            {summary.avg_working_hours}h
          </p>
        </div>

        <div style={summaryCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
            <CheckCircle size={20} color="#22c55e" />
            <span style={{ fontWeight: '600', color: '#333' }}>Excellent</span>
          </div>
          <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#22c55e', margin: 0 }}>
            {summary.days_above_target}
          </p>
        </div>

        <div style={summaryCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
            <AlertTriangle size={20} color="#f59e0b" />
            <span style={{ fontWeight: '600', color: '#333' }}>On Track</span>
          </div>
          <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#f59e0b', margin: 0 }}>
            {summary.days_on_track}
          </p>
        </div>

        <div style={summaryCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
            <Target size={20} color="#ef4444" />
            <span style={{ fontWeight: '600', color: '#333' }}>Below Target</span>
          </div>
          <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#ef4444', margin: 0 }}>
            {summary.days_below_target}
          </p>
        </div>
      </div>

      {/* Expandable detailed view */}
      {isExpanded && (
        <div style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
          <h3 style={{ marginBottom: '16px', color: '#333' }}>Daily Breakdown</h3>
          
          <div style={dailyGridStyle}>
            {daily_data.map((day, index) => (
              <div key={index} style={{
                padding: '16px',
                background: day.status_background,
                borderRadius: '8px',
                border: `2px solid ${day.status_color}20`,
                borderLeft: `4px solid ${day.status_color}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '600', color: '#333' }}>
                    {formatDate(day.date)}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {getStatusIcon(day.status)}
                    <span style={{ fontSize: '12px', color: day.status_color, fontWeight: '600' }}>
                      {day.status_message}
                    </span>
                  </div>
                </div>
                
                <div style={{ marginBottom: '8px' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: day.status_color }}>
                    {day.working_hours_formatted || `${day.working_hours}h`}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    of {day.total_hours_formatted || `${day.total_hours}h`} total
                  </div>
                </div>

                {day.activities_count > 0 && (
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {day.activities_count} activities • {day.productivity_percentage}% productive
                  </div>
                )}

                {day.activities_count === 0 && (
                  <div style={{ fontSize: '12px', color: '#999', fontStyle: 'italic' }}>
                    No activity recorded
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Best/Worst day info */}
          {summary.best_day && summary.worst_day && (
            <div style={{ 
              marginTop: '24px', 
              padding: '16px', 
              background: '#f0f9ff', 
              borderRadius: '8px',
              border: '1px solid #bae6fd'
            }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333' }}>Highlights</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <Award size={16} color="#22c55e" />
                    <span style={{ fontWeight: '600', color: '#22c55e' }}>Best Day</span>
                  </div>
                  <div style={{ fontSize: '14px', color: '#333' }}>
                    {formatDate(summary.best_day.date)} - {summary.best_day.hours}h
                  </div>
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <TrendingUp size={16} color="#667eea" />
                    <span style={{ fontWeight: '600', color: '#667eea' }}>Total Hours</span>
                  </div>
                  <div style={{ fontSize: '14px', color: '#333' }}>
                    {summary.total_working_hours}h this period
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default DailyHoursReport;
