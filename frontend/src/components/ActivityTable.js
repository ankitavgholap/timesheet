import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Monitor, Globe, Code, Briefcase, Play, Settings } from 'lucide-react';

function ActivityTable({ data, formatTime }) {
  const [sortField, setSortField] = useState('duration');
  const [sortDirection, setSortDirection] = useState('desc');

  // Process raw activity data for the table
  const processDataForTable = (rawData) => {
    if (!rawData || rawData.length === 0) return [];
    
    // Group by application
    const grouped = {};
    rawData.forEach(item => {
      const appName = item.application_name || 'Unknown';
      if (!grouped[appName]) {
        grouped[appName] = {
          application_name: appName,
          duration: 0,
          count: 0,
          category: item.category || 'Other'
        };
      }
      grouped[appName].duration += item.duration || 0;
      grouped[appName].count += 1;
    });

    return Object.values(grouped).sort((a, b) => b.duration - a.duration);
  };

  const processedData = processDataForTable(data);

  // Use the formatTime function passed as prop, or create a default one
  const timeFormatter = formatTime || ((seconds) => {
    if (!seconds || seconds === 0) return '0m';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
    } else if (minutes > 0) {
      return secs > 30 ? `${minutes}m ${secs}s` : `${minutes}m`;
    } else {
      return `${secs}s`;
    }
  });

  const getCategoryIcon = (category) => {
    switch (category?.toLowerCase()) {
      case 'web browsing':
        return <Globe size={16} color="#4285f4" />;
      case 'development':
        return <Code size={16} color="#28a745" />;
      case 'productivity':
        return <Briefcase size={16} color="#ffc107" />;
      case 'communication':
        return <Play size={16} color="#e91e63" />;
      case 'other':
        return <Settings size={16} color="#6c757d" />;
      default:
        return <Monitor size={16} color="#6c757d" />;
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedData = [...processedData].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }
    
    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const totalDuration = processedData.reduce((sum, item) => sum + item.duration, 0);

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px'
  };

  const thStyle = {
    padding: '12px 8px',
    textAlign: 'left',
    borderBottom: '2px solid #e9ecef',
    background: '#f8f9fa',
    fontWeight: '600',
    color: '#495057',
    cursor: 'pointer',
    userSelect: 'none'
  };

  const tdStyle = {
    padding: '12px 8px',
    borderBottom: '1px solid #e9ecef',
    verticalAlign: 'top'
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? 
      <ChevronUp size={14} style={{ marginLeft: '4px' }} /> : 
      <ChevronDown size={14} style={{ marginLeft: '4px' }} />;
  };

  if (!data || data.length === 0) {
    return (
      <div style={{ 
        background: 'white',
        padding: '40px',
        borderRadius: '15px',
        boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
        textAlign: 'center',
        color: '#666'
      }}>
        <h3 style={{ marginBottom: '20px', color: '#333' }}>Top Activities</h3>
        <p>No activity data available</p>
      </div>
    );
  }

  return (
    <div style={{
      background: 'white',
      padding: '25px',
      borderRadius: '15px',
      boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
      overflowX: 'auto'
    }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle} onClick={() => handleSort('application_name')}>
              Application
              <SortIcon field="application_name" />
            </th>
            <th style={thStyle} onClick={() => handleSort('category')}>
              Category
              <SortIcon field="category" />
            </th>
            <th style={thStyle} onClick={() => handleSort('duration')}>
              Time Spent
              <SortIcon field="duration" />
            </th>
            <th style={thStyle}>
              Progress
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedData.slice(0, 10).map((item, index) => (
            <tr 
              key={index}
              style={{ 
                backgroundColor: index % 2 === 0 ? '#fff' : '#f8f9fa'
              }}
            >
              <td style={tdStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {getCategoryIcon(item.category)}
                  <span style={{ fontWeight: '500' }}>
                    {item.application_name || 'Unknown Application'}
                  </span>
                </div>
              </td>
              <td style={tdStyle}>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '500',
                  background: item.category === 'Web Browsing' ? '#e3f2fd' :
                             item.category === 'Development' ? '#e8f5e8' :
                             item.category === 'Productivity' ? '#fff3cd' :
                             item.category === 'Communication' ? '#fce4ec' :
                             '#f8f9fa',
                  color: item.category === 'Web Browsing' ? '#1976d2' :
                         item.category === 'Development' ? '#388e3c' :
                         item.category === 'Productivity' ? '#f57c00' :
                         item.category === 'Communication' ? '#c2185b' :
                         '#6c757d'
                }}>
                  {item.category}
                </span>
              </td>
              <td style={tdStyle}>
                <span style={{ fontWeight: '500', color: '#667eea' }}>
                  {timeFormatter(item.duration)}
                </span>
              </td>
              <td style={tdStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '80px',
                    height: '6px',
                    background: '#e9ecef',
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${Math.min((item.duration / Math.max(...sortedData.map(d => d.duration))) * 100, 100)}%`,
                      height: '100%',
                      background: '#667eea',
                      borderRadius: '3px'
                    }} />
                  </div>
                  <span style={{ fontSize: '12px', color: '#666' }}>
                    {totalDuration > 0 ? ((item.duration / totalDuration) * 100).toFixed(1) : 0}%
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ActivityTable;
