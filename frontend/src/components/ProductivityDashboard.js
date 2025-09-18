import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Clock, 
  Zap, 
  Award,
  AlertCircle,
  CheckCircle,
  BarChart3,
  Brain
} from 'lucide-react';

function ProductivityDashboard({ startDate, endDate }) {
  const [productivityData, setProductivityData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchProductivityData();
  }, [startDate, endDate]);

  const fetchProductivityData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/productivity-analysis', {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });
      setProductivityData(response.data.productivity_analysis);
    } catch (error) {
      console.error('Error fetching productivity data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#22c55e'; // Green
    if (score >= 60) return '#eab308'; // Yellow
    if (score >= 40) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  const getScoreIcon = (score) => {
    if (score >= 80) return <Award size={24} color="#22c55e" />;
    if (score >= 60) return <Target size={24} color="#eab308" />;
    if (score >= 40) return <AlertCircle size={24} color="#f97316" />;
    return <AlertCircle size={24} color="#ef4444" />;
  };

  // const getTrendIcon = (trend) => {
  //   switch (trend) {
  //     case 'improving':
  //       return <TrendingUp size={16} color="#22c55e" />;
  //     case 'declining':
  //       return <TrendingDown size={16} color="#ef4444" />;
  //     default:
  //       return <BarChart3 size={16} color="#6b7280" />;
  //   }
  // };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m`;
    } else {
      return `${Math.floor(seconds)}s`;
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
    gap: '12px',
    marginBottom: '24px',
    paddingBottom: '16px',
    borderBottom: '2px solid #e5e7eb'
  };

  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '24px'
  };

  const metricCardStyle = {
    padding: '16px',
    background: '#f9fafb',
    borderRadius: '8px',
    border: '1px solid #e5e7eb'
  };

  const scoreCircleStyle = (score) => ({
    width: '120px',
    height: '120px',
    borderRadius: '50%',
    background: `conic-gradient(${getScoreColor(score)} ${score * 3.6}deg, #e5e7eb 0deg)`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 16px',
    position: 'relative'
  });

  const scoreInnerStyle = {
    width: '90px',
    height: '90px',
    borderRadius: '50%',
    background: '#fff',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center'
  };

  if (loading) {
    return (
      <div style={containerStyle}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: '16px', color: '#666' }}>Calculating productivity...</p>
        </div>
      </div>
    );
  }

  if (!productivityData) {
    return (
      <div style={containerStyle}>
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          <Brain size={48} color="#ccc" style={{ marginBottom: '16px' }} />
          <p>No productivity data available</p>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <Brain size={28} color="#667eea" />
        <h2 style={{ margin: 0, color: '#333' }}>Productivity Analysis</h2>
      </div>

      {/* Overall Score */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div style={scoreCircleStyle(productivityData.overall_score)}>
          <div style={scoreInnerStyle}>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: getScoreColor(productivityData.overall_score) }}>
              {productivityData.overall_score}
            </span>
            <span style={{ fontSize: '12px', color: '#666' }}>Score</span>
          </div>
        </div>
        <h3 style={{ margin: '0 0 8px 0', color: '#333' }}>Overall Productivity</h3>
        <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
          {productivityData.productivity_percentage}% of your time was productive
        </p>
      </div>

      {/* Key Metrics */}
      <div style={metricsGridStyle}>
        <div style={metricCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Clock size={20} color="#667eea" />
            <span style={{ fontWeight: '600', color: '#333' }}>Total Time</span>
          </div>
          <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#667eea', margin: 0 }}>
            {productivityData.total_time_formatted || formatTime(productivityData.total_time)}
          </p>
        </div>

        <div style={metricCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Zap size={20} color="#22c55e" />
            <span style={{ fontWeight: '600', color: '#333' }}>Productive Time</span>
          </div>
          <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#22c55e', margin: 0 }}>
            {productivityData.productive_time_formatted || formatTime(productivityData.productive_time)}
          </p>
        </div>

        <div style={metricCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Target size={20} color="#f59e0b" />
            <span style={{ fontWeight: '600', color: '#333' }}>Focus Sessions</span>
          </div>
          <p style={{ fontSize: '20px', fontWeight: 'bold', color: '#f59e0b', margin: 0 }}>
            {productivityData.focus_sessions}
          </p>
        </div>

        {/* <div style={metricCardStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            {getTrendIcon(productivityData.productivity_trend?.trend)}
            <span style={{ fontWeight: '600', color: '#333' }}>Trend</span>
          </div>
          <p style={{ fontSize: '16px', fontWeight: 'bold', margin: 0, textTransform: 'capitalize' }}>
            {productivityData.productivity_trend?.trend || 'Stable'}
            {productivityData.productivity_trend?.change !== 0 && (
              <span style={{ fontSize: '14px', color: '#666', marginLeft: '8px' }}>
                ({productivityData.productivity_trend.change > 0 ? '+' : ''}{productivityData.productivity_trend.change}%)
              </span>
            )}
          </p>
        </div> */}
      </div>


    </div>
  );
}

export default ProductivityDashboard;

