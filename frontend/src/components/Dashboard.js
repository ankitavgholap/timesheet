import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { format, startOfDay, endOfDay } from 'date-fns';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

import ActivityChart from './ActivityChart';
import ActivityTable from './ActivityTable';
import ProductivityDashboard from './ProductivityDashboard';
import DailyHoursReport from './DailyHoursReport';
import { Calendar, RefreshCw, Activity, Clock, ChevronDown, ChevronUp } from 'lucide-react';

function Dashboard() {
  const [activityData, setActivityData] = useState([]);
  const [topWindowTitles, setTopWindowTitles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState(startOfDay(new Date()));
  const [endDate, setEndDate] = useState(endOfDay(new Date()));
  const [totalTime, setTotalTime] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isTopActivitiesOpen, setIsTopActivitiesOpen] = useState(false);

  const fetchActivityData = async (fetchFromAW = false) => {
    setLoading(true);
    try {
      const endpoint = fetchFromAW ? '/activity-data' : '/activity-summary';
      const response = await axios.get(endpoint, {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });

      setActivityData(response.data.data || []);
      setTotalTime(response.data.total_time || 0);
      setLastUpdated(new Date());
      
      if (fetchFromAW) {
        toast.success('Activity data synced from ActivityWatch!');
      }
    } catch (error) {
      console.error('Error fetching activity data:', error);
      if (error.response?.status === 500 && fetchFromAW) {
        toast.error('Could not connect to ActivityWatch. Make sure it\'s running on localhost:5600');
      } else {
        toast.error('Failed to fetch activity data');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchTopWindowTitles = async () => {
    try {
      console.log('🔍 Fetching top window titles for date range:', {
        start: startDate.toISOString(),
        end: endDate.toISOString()
      });
      
      const response = await axios.get('/top-window-titles', {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          limit: 30  // Get more window titles
        }
      });

      console.log('📊 Received window titles:', response.data.top_window_titles?.length || 0);
      setTopWindowTitles(response.data.top_window_titles || []);
    } catch (error) {
      console.error('Error fetching top window titles:', error);
      // Don't show error toast for this as it's supplementary data
    }
  };

  useEffect(() => {
    fetchActivityData(false); // Load from database first
    fetchTopWindowTitles(); // Load top window titles from ActivityWatch
  }, [startDate, endDate]);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const formatDecimalHoursToHoursMinutes = (decimalHoursString) => {
      // Extract the numeric value from strings like "0.10h" or "1.5h"
      const numericValue = parseFloat(decimalHoursString.replace(/[^\d.]/g, ''));
      
      if (isNaN(numericValue)) return decimalHoursString; // Return original if parsing fails
      
      const hours = Math.floor(numericValue);
      const minutes = Math.round((numericValue - hours) * 60);
      
      if (hours > 0 && minutes > 0) {
        return `${hours}h ${minutes}m`;
      } else if (hours > 0) {
        return `${hours}h`;
      } else if (minutes > 0) {
        return `${minutes}m`;
      } else {
        return '0m';
      }
    };


  const isWorkRelatedActivity = (item) => {
    const appName = (item.application_name || '').toLowerCase();
    const windowTitle = (item.window_title || '').toLowerCase();
    const category = (item.category || '').toLowerCase();
    
    // Work-related applications
    const workApps = [
      'cursor', 'vscode', 'visual studio', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs', 'notepad++',
      'filezilla', 'winscp', 'putty', 'ssh', 'terminal',
      'plesk', 'cpanel', 'whm', 'directadmin', 'webmin',
      'datagrip', 'pgadmin', 'phpmyadmin', 'mysql', 'postgresql', 'mongodb',
      'postman', 'insomnia', 'git', 'github', 'gitlab', 'docker', 'kubernetes',
      'figma', 'photoshop', 'illustrator', 'canva',
      'notion', 'obsidian', 'trello', 'asana', 'jira', 'confluence'
    ];
    
    const isWorkApp = workApps.some(workApp => appName.includes(workApp));
    const isWorkCategory = ['development', 'database', 'productivity'].includes(category);
    const isWorkBrowser = category === 'browser' && item.urls && item.urls.length > 0 && 
      item.urls.some(url => {
        const domain = url.toLowerCase();
        return domain.includes('github') || domain.includes('stackoverflow') || 
               domain.includes('docs.') || domain.includes('api.') ||
               domain.includes('developer') || domain.includes('tutorial') ||
               domain.includes('plesk') || domain.includes('cpanel') ||
               domain.includes('aws') || domain.includes('azure') || domain.includes('gcp');
      });
    
    const isSystemLock = windowTitle.includes('lock') || windowTitle.includes('locked') || 
                        appName.includes('lockapp') || appName.includes('logonui');
    const isEntertainment = category === 'entertainment' || 
                           windowTitle.includes('youtube') || windowTitle.includes('netflix') ||
                           windowTitle.includes('spotify') || windowTitle.includes('music');
    
    return (isWorkApp || isWorkCategory || isWorkBrowser) && !isSystemLock && !isEntertainment;
  };

  const extractProjectInfo = (item) => {
    // First, check if project info is already in the database
    if (item.project_name) {
      return { 
        project: item.project_name, 
        type: item.project_type || 'Work',
        file: item.project_file || 'Activity'
      };
    }
    
    // Skip entertainment and system locks
    const appName = (item.application_name || '').toLowerCase();
    const windowTitle = item.window_title || '';
    
    const isSystemLock = windowTitle.toLowerCase().includes('lock') || windowTitle.toLowerCase().includes('locked') || 
                        appName.includes('lockapp') || appName.includes('logonui');
    const isEntertainment = item.category === 'entertainment' || 
                           windowTitle.toLowerCase().includes('youtube') || windowTitle.toLowerCase().includes('netflix') ||
                           windowTitle.toLowerCase().includes('spotify') || windowTitle.toLowerCase().includes('music');
    
    if (isSystemLock || isEntertainment) {
      return null;
    }
    
    // Fallback extraction if not in database (for backward compatibility)
    if (appName.includes('filezilla') || appName.includes('winscp') || appName.includes('ftp')) {
      const serverMatch = windowTitle.match(/([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d+\.\d+\.\d+\.\d+)/);
      if (serverMatch) {
        return { project: `FTP: ${serverMatch[1]}`, type: 'Server Management' };
      }
      return { project: 'FileZilla/FTP', type: 'Server Management' };
    }
    
    if (windowTitle.toLowerCase().includes('cpanel') || windowTitle.toLowerCase().includes('plesk')) {
      const domainMatch = windowTitle.match(/([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
      if (domainMatch) {
        return { project: `Hosting: ${domainMatch[1]}`, type: 'Server Management' };
      }
      return { project: 'cPanel/Hosting', type: 'Server Management' };
    }
    
    if (appName.includes('chrome') || appName.includes('firefox') || appName.includes('edge')) {
      if (windowTitle.includes('localhost:')) {
        const portMatch = windowTitle.match(/localhost:(\d+)/);
        const port = portMatch ? portMatch[1] : 'unknown';
        return { project: `localhost:${port}`, type: 'Web Development' };
      }
      
      const urlMatch = windowTitle.match(/https?:\/\/([^\/\s]+)|([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
      if (urlMatch) {
        const domain = urlMatch[1] || urlMatch[2];
        return { project: domain, type: 'Web Development' };
      }
      
      const titleParts = windowTitle.split(' - ');
      if (titleParts.length > 0 && titleParts[0].trim()) {
        return { project: titleParts[0].trim(), type: 'Web Development' };
      }
    }

    
    
    if (appName.includes('cursor') || appName.includes('vscode') || appName.includes('code')) {
      const idePattern = /^(.+?)\s*-\s*(.+?)\s*-\s*(Visual Studio Code|Cursor|Code)/i;
      const ideMatch = windowTitle.match(idePattern);
      
      if (ideMatch) {
        return { project: ideMatch[2].trim(), type: 'Development' };
      }
    }
    
    // Last resort - use application name
    if (item.application_name && item.application_name.length > 3) {
      return { 
        project: item.application_name.replace('.exe', ''), 
        type: 'Work' 
      };
    }
    
    // Server Management Tools
    if (appName.includes('filezilla') || appName.includes('winscp')) {
      const serverInfo = item.window_title || item.detailed_activity || '';
      const serverMatch = serverInfo.match(/(\w+\.\w+|\d+\.\d+\.\d+\.\d+)/);
      return { project: serverMatch ? serverMatch[1] : 'Server Management', type: 'Server Management' };
    }
    
    if (appName.includes('plesk') || item.window_title?.toLowerCase().includes('plesk')) {
      return { project: 'Plesk Panel', type: 'Server Management' };
    }
    
    if (appName.includes('cpanel') || item.window_title?.toLowerCase().includes('cpanel')) {
      return { project: 'cPanel', type: 'Server Management' };
    }
    
    // Database Management
    if (appName.includes('datagrip') || appName.includes('pgadmin') || appName.includes('phpmyadmin')) {
      const dbName = item.database_connection || 'Database';
      return { project: dbName, type: 'Database' };
    }
    
    // Extract project from detailed activity
    if (item.detailed_activity && item.detailed_activity.includes(' in ')) {
      const parts = item.detailed_activity.split(' in ');
      if (parts.length > 1) {
        return { project: parts[1], type: 'Development' };
      }
    }
    
    // Work-related browser activities
    if (item.category === 'browser' && item.urls && item.urls.length > 0) {
      const url = item.urls[0];
      try {
        const urlObj = new URL(url);
        const domain = urlObj.hostname.replace('www.', '');
        
        if (domain.includes('github') || domain.includes('gitlab')) {
          const pathParts = urlObj.pathname.split('/').filter(p => p);
          const repoName = pathParts.length > 1 ? `${pathParts[0]}/${pathParts[1]}` : domain;
          return { project: repoName, type: 'Development' };
        } else {
          return { project: domain, type: 'Web Development' };
        }
      } catch (e) {
        // Invalid URL, fallback
      }
    }
    
    // Add this new function to convert decimal hours to hours and minutes
    
    // Group development tools under a common project if no specific project found
    if (appName.includes('cursor') || appName.includes('vscode') || appName.includes('code')) {
      // Try to extract project from window title
      if (item.window_title) {
        const titleParts = item.window_title.split(' - ');
        if (titleParts.length > 1) {
          // Look for project name in title like "package.json - timesheet - Cursor"
          const possibleProject = titleParts[titleParts.length - 2];
          if (possibleProject && possibleProject !== 'Visual Studio Code' && possibleProject !== 'Cursor') {
            return { project: possibleProject, type: 'Development' };
          }
        }
      }
      return { project: 'Development Work', type: 'Development' };
    }
    
    // Group API tools under project context
    if (appName.includes('postman') || appName.includes('insomnia')) {
      // Try to extract project context from window title
      if (item.window_title && item.window_title.includes('timesheet')) {
        return { project: 'timesheet', type: 'Development' };
      }
      return { project: 'API Development', type: 'Development' };
    }
    
    // Fallback for other work tools
    return { project: 'General Work', type: 'Work' };
  };

  const dashboardStyle = {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto'
  };

  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
    flexWrap: 'wrap',
    gap: '20px'
  };

  const titleStyle = {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#333',
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  };

  const controlsStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    flexWrap: 'wrap'
  };

  const datePickerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: 'white',
    padding: '12px 16px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
  };

  const statsStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px'
  };

  const statCardStyle = {
    background: 'white',
    padding: '24px',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    textAlign: 'center'
  };

  const contentStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '30px',
    marginBottom: '30px'
  };

  const chartContainerStyle = {
    background: 'white',
    padding: '24px',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
  };

  return (
    <div style={dashboardStyle}>
      <div style={headerStyle}>
        <h1 style={titleStyle}>
          <Activity size={36} color="#667eea" />
          Activity Dashboard
        </h1>
        
        <div style={controlsStyle}>
          <div style={datePickerStyle}>
            <Calendar size={20} color="#667eea" />
            <DatePicker
              selected={startDate}
              onChange={setStartDate}
              selectsStart
              startDate={startDate}
              endDate={endDate}
              placeholderText="Start Date"
              dateFormat="MMM d, yyyy"
            />
            <span>to</span>
            <DatePicker
              selected={endDate}
              onChange={setEndDate}
              selectsEnd
              startDate={startDate}
              endDate={endDate}
              minDate={startDate}
              placeholderText="End Date"
              dateFormat="MMM d, yyyy"
            />
          </div>
          
          <button
            onClick={() => fetchActivityData(true)}
            disabled={loading}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <RefreshCw size={16} className={loading ? 'spinning' : ''} />
            Sync from ActivityWatch
          </button>
        </div>
      </div>

      <div style={statsStyle}>
        <div style={statCardStyle}>
          <Clock size={32} color="#667eea" style={{ marginBottom: '12px' }} />
          <h3 style={{ margin: '0 0 8px 0', color: '#333' }}>Total Time</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#667eea', margin: 0 }}>
            {formatTime(totalTime)}
          </p>
        </div>
        
        <div style={statCardStyle}>
          <Activity size={32} color="#28a745" style={{ marginBottom: '12px' }} />
          <h3 style={{ margin: '0 0 8px 0', color: '#333' }}>Active Projects</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745', margin: 0 }}>
            {(() => {
              // Count unique projects from work activities
              const uniqueProjects = new Set();
              activityData.forEach(item => {
                const projectInfo = extractProjectInfo(item);
                if (projectInfo && projectInfo.project) {
                  uniqueProjects.add(projectInfo.project);
                }
              });
              return uniqueProjects.size;
            })()}
          </p>
          <p style={{ fontSize: '12px', color: '#666', margin: '4px 0 0 0' }}>
            in selected period
          </p>
        </div>
        
        <div style={statCardStyle}>
          <RefreshCw size={32} color="#ffc107" style={{ marginBottom: '12px' }} />
          <h3 style={{ margin: '0 0 8px 0', color: '#333' }}>Last Updated</h3>
          <p style={{ fontSize: '14px', color: '#666', margin: 0 }}>
            {lastUpdated ? format(lastUpdated, 'MMM d, yyyy HH:mm') : 'Never'}
          </p>
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p style={{ marginTop: '16px', color: '#666' }}>Loading activity data...</p>
        </div>
      )}

      {!loading && activityData.length > 0 && (
        <>
          {/* Daily Hours Report */}
          <DailyHoursReport startDate={startDate} endDate={endDate} />
          
          {/* Productivity Analysis */}
          <ProductivityDashboard startDate={startDate} endDate={endDate} />
          
          <div style={contentStyle}>
            <div style={chartContainerStyle}>
              <h3 style={{ marginBottom: '20px', color: '#333' }}>Activity Distribution</h3>
              <ActivityChart data={activityData} />
            </div>
            
            <div style={chartContainerStyle}>
              <h3 style={{ marginBottom: '20px', color: '#333' }}>
                Project Details
                <span style={{ fontSize: '14px', color: '#666', fontWeight: 'normal', marginLeft: '8px' }}>
                  ({format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')})
                </span>
              </h3>
              
              {/* Top Window Titles from ActivityWatch */}
              {topWindowTitles.length > 0 && (
                <div style={{ marginBottom: '30px' }}>
                  <h4 style={{ 
                    fontSize: '16px', 
                    color: '#333', 
                    marginBottom: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    🏆 Top Window Titles from ActivityWatch
                    <span style={{ 
                      fontSize: '12px', 
                      color: '#666', 
                      fontWeight: 'normal',
                      background: '#f3f4f6',
                      padding: '2px 8px',
                      borderRadius: '12px'
                    }}>
                      Live Data
                    </span>
                  </h4>
                  
                  <div style={{
                    display: 'grid',
                    gap: '12px',
                    maxHeight: '400px',
                    overflowY: 'auto',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '16px'
                  }}>
                    {topWindowTitles.map((title, index) => (
                      <div key={index} style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '12px',
                        background: '#f9fafb',
                        borderRadius: '6px',
                        border: '1px solid #e5e7eb'
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <span style={{
                              fontSize: '14px',
                              fontWeight: '600',
                              color: '#1f2937',
                              background: title.project_info?.project_type === 'Development' ? '#dcfce7' :
                                         title.project_info?.project_type === 'Web Development' ? '#dbeafe' :
                                         title.project_info?.project_type === 'Server Management' ? '#fef3c7' :
                                         title.project_info?.project_type === 'Database' ? '#f3e8ff' :
                                         '#f3f4f6',
                              color: title.project_info?.project_type === 'Development' ? '#166534' :
                                     title.project_info?.project_type === 'Web Development' ? '#1e40af' :
                                     title.project_info?.project_type === 'Server Management' ? '#92400e' :
                                     title.project_info?.project_type === 'Database' ? '#7c3aed' :
                                     '#374151',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '11px'
                            }}>
                              {title.project_info?.project_type || 'Work'}
                            </span>
                            <span style={{ fontSize: '14px', fontWeight: '500', color: '#1f2937' }}>
                              {title.project_info?.project_name || title.application_name}
                            </span>
                          </div>
                          
                          <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '2px' }}>
                            📄 {title.project_info?.file_name || title.window_title}
                          </div>
                          
                          <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                            💻 {title.application_name} • {title.activity_count} activities
                          </div>
                        </div>
                        
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ 
                            fontSize: '16px', 
                            fontWeight: '600', 
                            color: '#059669',
                            marginBottom: '2px'
                          }}>
                            {formatDecimalHoursToHoursMinutes(title.duration_formatted)}
                          </div>
                          <div style={{ fontSize: '10px', color: '#9ca3af' }}>
                            Last: {new Date(title.last_seen).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Top Activities - Accordion */}
          <div style={chartContainerStyle}>
            <div 
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                padding: '16px 0',
                borderBottom: isTopActivitiesOpen ? '1px solid #e5e7eb' : 'none',
                marginBottom: isTopActivitiesOpen ? '20px' : '0'
              }}
              onClick={() => setIsTopActivitiesOpen(!isTopActivitiesOpen)}
            >
              <h3 style={{ margin: 0, color: '#333' }}>Top Activities</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '14px', color: '#666' }}>
                  
                </span>
                {isTopActivitiesOpen ? 
                  <ChevronUp size={20} color="#667eea" /> : 
                  <ChevronDown size={20} color="#667eea" />
                }
              </div>
            </div>
            
            {isTopActivitiesOpen && (
              <div style={{
                animation: 'fadeIn 0.3s ease-in-out'
              }}>
                <ActivityTable data={activityData.filter(item => isWorkRelatedActivity(item))} formatTime={formatTime} showUrls={true} showDetails={false} />
              </div>
            )}
          </div>
          
        </>
      )}

      {!loading && activityData.length === 0 && (
        <div style={chartContainerStyle}>
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#666' }}>
            <Activity size={64} color="#ccc" style={{ marginBottom: '20px' }} />
            <h3 style={{ marginBottom: '12px' }}>No Activity Data</h3>
            <p style={{ marginBottom: '20px' }}>
              No activity data found for the selected date range.
            </p>
            <button
              onClick={() => fetchActivityData(true)}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '0 auto' }}
            >
              <RefreshCw size={16} />
              Sync from ActivityWatch
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
