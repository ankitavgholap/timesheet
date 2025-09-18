import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, Monitor, Globe, Code, Briefcase, Play, Settings } from 'lucide-react';

function ActivityTable({ data, formatTime, showUrls = false, showProjects = false, showDetails = true }) {
  const [sortField, setSortField] = useState('duration');
  const [sortDirection, setSortDirection] = useState('desc');
  const [expandedRows, setExpandedRows] = useState(new Set());

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'browser':
        return <Globe size={16} color="#4285f4" />;
      case 'development':
        return <Code size={16} color="#28a745" />;
      case 'productivity':
        return <Briefcase size={16} color="#ffc107" />;
      case 'entertainment':
        return <Play size={16} color="#e91e63" />;
      case 'system':
        return <Settings size={16} color="#6c757d" />;
      default:
        return <Monitor size={16} color="#6c757d" />;
    }
  };

  const isWorkRelatedActivity = (item) => {
    const appName = (item.application_name || '').toLowerCase();
    const windowTitle = (item.window_title || '').toLowerCase();
    const category = (item.category || '').toLowerCase();
    
    // Work-related applications
    const workApps = [
      // IDEs and Code Editors
      'cursor', 'vscode', 'visual studio', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs', 'notepad++',
      // Server Management
      'filezilla', 'winscp', 'putty', 'ssh', 'terminal',
      // Web Development & Server Management
      'plesk', 'cpanel', 'whm', 'directadmin', 'webmin',
      // Database Tools
      'datagrip', 'pgadmin', 'phpmyadmin', 'mysql', 'postgresql', 'mongodb',
      // Development Tools
      'postman', 'insomnia', 'git', 'github', 'gitlab', 'docker', 'kubernetes',
      // Design & Content
      'figma', 'photoshop', 'illustrator', 'canva',
      // Productivity (work-related)
      'notion', 'obsidian', 'trello', 'asana', 'jira', 'confluence'
    ];
    
    // Check if application is work-related
    const isWorkApp = workApps.some(workApp => appName.includes(workApp));
    
    // Check for work-related categories
    const isWorkCategory = ['development', 'database', 'productivity'].includes(category);
    
    // Check for work-related browser activities (exclude entertainment)
    const isWorkBrowser = category === 'browser' && item.urls && item.urls.length > 0 && 
      item.urls.some(url => {
        const domain = url.toLowerCase();
        return domain.includes('github') || domain.includes('stackoverflow') || 
               domain.includes('docs.') || domain.includes('api.') ||
               domain.includes('developer') || domain.includes('tutorial') ||
               domain.includes('plesk') || domain.includes('cpanel') ||
               domain.includes('aws') || domain.includes('azure') || domain.includes('gcp');
      });
    
    // Exclude system locks and non-work activities
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
        file: item.project_file || 'Activity',
        path: item.file_path || item.window_title,
        type: item.project_type || 'Work'
      };
    }
    
    // Fallback extraction for items without database project info
    const appName = (item.application_name || '').toLowerCase();
    const windowTitle = item.window_title || '';
    
    // Skip only entertainment and system locks
    const isSystemLock = windowTitle.toLowerCase().includes('lock') || windowTitle.toLowerCase().includes('locked') || 
                        appName.includes('lockapp') || appName.includes('logonui');
    const isEntertainment = item.category === 'entertainment' || 
                           windowTitle.toLowerCase().includes('youtube') || windowTitle.toLowerCase().includes('netflix') ||
                           windowTitle.toLowerCase().includes('spotify') || windowTitle.toLowerCase().includes('music');
    
    if (isSystemLock || isEntertainment) {
      return null;
    }
    
    // AGGRESSIVE PROJECT EXTRACTION: Extract projects from ALL window titles
    let projectName = null;
    let fileName = null;
    let activityType = 'Work';
    
    // Method 1: FileZilla/FTP - Extract server/domain names
    if (appName.includes('filezilla') || appName.includes('winscp') || appName.includes('ftp')) {
      // Extract any domain or IP from window title
      const serverMatch = windowTitle.match(/([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d+\.\d+\.\d+\.\d+)/);
      if (serverMatch) {
        return {
          project: `FTP: ${serverMatch[1]}`,
          file: 'Server Connection',
          path: windowTitle,
          type: 'Server Management'
        };
      }
      // Extract any meaningful part of the title
      const titleParts = windowTitle.split(/[\s\-\/\\]/);
      const meaningfulPart = titleParts.find(part => part.length > 3 && !part.match(/filezilla|ftp/i));
      if (meaningfulPart) {
        return {
          project: `FTP: ${meaningfulPart}`,
          file: 'Server Connection',
          path: windowTitle,
          type: 'Server Management'
        };
      }
      return {
        project: 'FileZilla/FTP',
        file: 'Server Connection',
        path: windowTitle,
        type: 'Server Management'
      };
    }
    
    // Method 2: cPanel/Plesk/Hosting - Extract ALL hosting-related activities
    if (windowTitle.toLowerCase().includes('cpanel') || windowTitle.toLowerCase().includes('plesk') || 
        windowTitle.toLowerCase().includes('hosting') || windowTitle.toLowerCase().includes('panel') ||
        windowTitle.toLowerCase().includes('whm') || windowTitle.toLowerCase().includes('directadmin')) {
      
      // Extract domain from URL or title
      const domainMatch = windowTitle.match(/([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
      if (domainMatch) {
        return {
          project: `Hosting: ${domainMatch[1]}`,
          file: 'Control Panel',
          path: windowTitle,
          type: 'Server Management'
        };
      }
      
      // Extract any meaningful identifier
      const titleParts = windowTitle.split(/[\s\-\/]/);
      const meaningfulPart = titleParts.find(part => part.length > 3 && !part.match(/cpanel|plesk|hosting|panel/i));
      if (meaningfulPart) {
        return {
          project: `Hosting: ${meaningfulPart}`,
          file: 'Control Panel',
          path: windowTitle,
          type: 'Server Management'
        };
      }
      
      return {
        project: 'cPanel/Hosting',
        file: 'Control Panel',
        path: windowTitle,
        type: 'Server Management'
      };
    }
    
    // Method 3: Browser - Extract EVERY website as a project
    if (appName.includes('chrome') || appName.includes('firefox') || appName.includes('edge') || 
        appName.includes('safari') || appName.includes('browser')) {
      
      // Local development servers
      if (windowTitle.includes('localhost:') || windowTitle.includes('127.0.0.1:')) {
        const portMatch = windowTitle.match(/localhost:(\d+)|127\.0\.0\.1:(\d+)/);
        const port = portMatch ? (portMatch[1] || portMatch[2]) : 'unknown';
        return {
          project: `localhost:${port}`,
          file: 'Local Development',
          path: windowTitle,
          type: 'Web Development'
        };
      }
      
      // Extract domain from any URL or title
      const urlMatch = windowTitle.match(/https?:\/\/([^\/\s]+)|([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
      if (urlMatch) {
        const domain = urlMatch[1] || urlMatch[2];
        return {
          project: domain,
          file: 'Website',
          path: windowTitle,
          type: 'Web Development'
        };
      }
      
      // Use the first meaningful part of the title as project
      const titleParts = windowTitle.split(' - ');
      const firstPart = titleParts[0]?.trim();
      if (firstPart && firstPart.length > 2) {
        return {
          project: firstPart,
          file: 'Web Page',
          path: windowTitle,
          type: 'Web Development'
        };
      }
      
      return {
        project: 'Web Browsing',
        file: 'Browser Activity',
        path: windowTitle,
        type: 'Web Development'
      };
    }
    
    // Method 4: IDE window titles - Extract ALL project names
    if (appName.includes('cursor') || appName.includes('vscode') || appName.includes('code') || 
        appName.includes('pycharm') || appName.includes('intellij') || appName.includes('sublime') ||
        appName.includes('atom') || appName.includes('vim') || appName.includes('emacs')) {
      
      // Pattern: "filename - projectname - IDE"
      const idePattern = /^(.+?)\s*-\s*(.+?)\s*-\s*(Visual Studio Code|Cursor|Code|PyCharm|IntelliJ|Sublime|Atom)/i;
      const ideMatch = windowTitle.match(idePattern);
      
      if (ideMatch) {
        fileName = ideMatch[1].trim();
        projectName = ideMatch[2].trim();
        return {
          project: projectName,
          file: fileName,
          path: item.file_path,
          type: 'Development'
        };
      }
      
      // Try to extract from any part of the title
      const titleParts = windowTitle.split(' - ').filter(part => 
        part && !part.match(/Visual Studio Code|Cursor|Code|PyCharm|IntelliJ|Sublime|Atom/i)
      );
      
      if (titleParts.length >= 2) {
        return {
          project: titleParts[titleParts.length - 1],
          file: titleParts[0],
          path: item.file_path,
          type: 'Development'
        };
      } else if (titleParts.length === 1 && titleParts[0].length > 2) {
        return {
          project: titleParts[0],
          file: 'Code File',
          path: item.file_path,
          type: 'Development'
        };
      }
      
      return {
        project: 'IDE Work',
        file: 'Development',
        path: item.file_path,
        type: 'Development'
      };
    }
    
    // Method 5: Database tools - Extract ALL database connections
    if (appName.includes('datagrip') || appName.includes('pgadmin') || appName.includes('phpmyadmin') || 
        appName.includes('mysql') || appName.includes('postgresql') || appName.includes('mongodb') ||
        windowTitle.toLowerCase().includes('database') || windowTitle.toLowerCase().includes('sql')) {
      
      // Try to extract database name or connection info
      const dbMatch = windowTitle.match(/([a-zA-Z0-9_-]+)@([a-zA-Z0-9.-]+)|([a-zA-Z0-9_-]+)\s*database/i);
      if (dbMatch) {
        const dbName = dbMatch[1] || dbMatch[3] || 'Database';
        const server = dbMatch[2] || '';
        return {
          project: server ? `DB: ${dbName}@${server}` : `DB: ${dbName}`,
          file: 'Database',
          path: windowTitle,
          type: 'Database'
        };
      }
      
      // Extract any meaningful part from title
      const titleParts = windowTitle.split(/[\s\-@]/);
      const meaningfulPart = titleParts.find(part => part.length > 3 && !part.match(/datagrip|pgadmin|mysql|database/i));
      if (meaningfulPart) {
        return {
          project: `DB: ${meaningfulPart}`,
          file: 'Database',
          path: windowTitle,
          type: 'Database'
        };
      }
      
      return {
        project: 'Database Work',
        file: 'Database',
        path: windowTitle,
        type: 'Database'
      };
    }
    
    // Method 6: API tools - Extract ALL API work
    if (appName.includes('postman') || appName.includes('insomnia') || appName.includes('rest') ||
        windowTitle.toLowerCase().includes('api') || windowTitle.toLowerCase().includes('postman')) {
      
      // Try to extract API project or collection name
      const apiMatch = windowTitle.match(/([a-zA-Z0-9_-]+)\s*(API|Collection|Request)/i);
      if (apiMatch) {
        return {
          project: `API: ${apiMatch[1]}`,
          file: 'API Testing',
          path: windowTitle,
          type: 'API Development'
        };
      }
      
      // Extract any meaningful part
      const titleParts = windowTitle.split(/[\s\-]/);
      const meaningfulPart = titleParts.find(part => part.length > 3 && !part.match(/postman|insomnia|api/i));
      if (meaningfulPart) {
        return {
          project: `API: ${meaningfulPart}`,
          file: 'API Testing',
          path: windowTitle,
          type: 'API Development'
        };
      }
      
      return {
        project: 'API Development',
        file: 'API Testing',
        path: windowTitle,
        type: 'API Development'
      };
    }
    
    // Method 7: Extract from file path if available
    if (item.file_path) {
      const pathParts = item.file_path.split(/[/\\]/);
      if (pathParts.length > 1) {
        const parentDir = pathParts[pathParts.length - 2];
        return {
          project: parentDir,
          file: pathParts[pathParts.length - 1],
          path: item.file_path,
          type: 'Development'
        };
      }
    }
    
    // Method 8: Fallback - Use application name or window title as project
    if (windowTitle && windowTitle.length > 3) {
      // Clean up the title and use first meaningful part
      const cleanTitle = windowTitle.split(' - ')[0]?.trim() || windowTitle.trim();
      if (cleanTitle.length > 3) {
        return {
          project: cleanTitle,
          file: 'Activity',
          path: windowTitle,
          type: 'Work'
        };
      }
    }
    
    // Last resort - use application name
    if (item.application_name && item.application_name.length > 3) {
      return {
        project: item.application_name.replace('.exe', ''),
        file: 'Application',
        path: windowTitle,
        type: 'Work'
      };
    }
    
    // Server Management Tools (FileZilla, Plesk, cPanel)
    if (appName.includes('filezilla') || appName.includes('winscp')) {
      const serverInfo = item.window_title || item.detailed_activity || '';
      const serverMatch = serverInfo.match(/(\w+\.\w+|\d+\.\d+\.\d+\.\d+)/);
      return {
        project: serverMatch ? serverMatch[1] : 'Server Management',
        file: 'FTP/SFTP Transfer',
        path: serverInfo,
        type: 'Server Management'
      };
    }
    
    if (appName.includes('plesk') || item.window_title?.toLowerCase().includes('plesk')) {
      return {
        project: 'Plesk Panel',
        file: 'Server Administration',
        path: item.urls?.[0] || item.window_title,
        type: 'Server Management'
      };
    }
    
    if (appName.includes('cpanel') || item.window_title?.toLowerCase().includes('cpanel')) {
      return {
        project: 'cPanel',
        file: 'Hosting Management',
        path: item.urls?.[0] || item.window_title,
        type: 'Server Management'
      };
    }
    
    // Database Management
    if (appName.includes('datagrip') || appName.includes('pgadmin') || appName.includes('phpmyadmin')) {
      const dbName = item.database_connection || 'Database';
      return {
        project: dbName,
        file: 'Database Management',
        path: item.database_connection || item.window_title,
        type: 'Database'
      };
    }
    
    // Extract project from detailed activity (for IDEs)
    if (item.detailed_activity && item.detailed_activity.includes(' in ')) {
      const parts = item.detailed_activity.split(' in ');
      if (parts.length > 1) {
        return {
          project: parts[1],
          file: parts[0].replace('Coding: ', ''),
          path: item.file_path,
          type: 'Development'
        };
      }
    }
    
    // Work-related browser activities
    if (item.category === 'browser' && item.urls && item.urls.length > 0) {
      const url = item.urls[0];
      try {
        const urlObj = new URL(url);
        const domain = urlObj.hostname.replace('www.', '');
        
        // Categorize work-related domains
        if (domain.includes('github') || domain.includes('gitlab')) {
          const pathParts = urlObj.pathname.split('/').filter(p => p);
          const repoName = pathParts.length > 1 ? `${pathParts[0]}/${pathParts[1]}` : domain;
          return {
            project: repoName,
            file: 'Repository',
            path: url,
            type: 'Development'
          };
        } else if (domain.includes('stackoverflow') || domain.includes('docs.') || domain.includes('developer')) {
          return {
            project: domain,
            file: 'Documentation/Research',
            path: url,
            type: 'Research'
          };
        } else {
          return {
            project: domain,
            file: item.window_title || 'Web Development',
            path: url,
            type: 'Web Development'
          };
        }
      } catch (e) {
        // Invalid URL, fallback
      }
    }
    
    // Group development tools under a common project if no specific project found
    if (appName.includes('cursor') || appName.includes('vscode') || appName.includes('code')) {
      // Try to extract project from window title
      if (item.window_title) {
        const titleParts = item.window_title.split(' - ');
        if (titleParts.length > 1) {
          // Look for project name in title like "package.json - timesheet - Cursor"
          const possibleProject = titleParts[titleParts.length - 2];
          if (possibleProject && possibleProject !== 'Visual Studio Code' && possibleProject !== 'Cursor') {
            return {
              project: possibleProject,
              file: titleParts[0],
              path: item.file_path,
              type: 'Development'
            };
          }
        }
      }
      return {
        project: 'Development Work',
        file: item.window_title || 'Code Editor',
        path: item.file_path,
        type: 'Development'
      };
    }
    
    // Group API tools under project context
    if (appName.includes('postman') || appName.includes('insomnia')) {
      // Try to extract project context from window title
      if (item.window_title && item.window_title.includes('timesheet')) {
        return {
          project: 'timesheet',
          file: 'API Testing',
          path: null,
          type: 'Development'
        };
      }
      return {
        project: 'API Development',
        file: 'API Testing',
        path: null,
        type: 'Development'
      };
    }
    
    // Fallback for other work tools
    return {
      project: 'General Work',
      file: item.window_title || item.application_name || 'Work Activity',
      path: null,
      type: 'Work'
    };
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const toggleRowExpansion = (index) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  const sortedData = [...data].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    // For window_title sorting, fall back to detailed_activity or application_name
    if (sortField === 'window_title') {
      aValue = a.window_title || a.detailed_activity || a.application_name;
      bValue = b.window_title || b.detailed_activity || b.application_name;
    }
    
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
        textAlign: 'center', 
        padding: '40px', 
        color: '#666' 
      }}>
        No activity data available
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle} onClick={() => handleSort('window_title')}>
              {showProjects ? 'Project / File' : 'Application'}
              <SortIcon field="window_title" />
            </th>
            <th style={thStyle} onClick={() => handleSort('category')}>
              Category
              <SortIcon field="category" />
            </th>
            <th style={thStyle} onClick={() => handleSort('duration')}>
              Time Spent
              <SortIcon field="duration" />
            </th>
            <th style={thStyle} onClick={() => handleSort('percentage')}>
              Percentage
              <SortIcon field="percentage" />
            </th>
            {(showUrls || showProjects) && showDetails && (
              <th style={thStyle}>
                {showProjects ? 'Project Details' : 'Details'}
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((item, index) => {
            const projectInfo = showProjects ? extractProjectInfo(item) : null;
            
            // Skip non-work activities when showing projects
            if (showProjects && !projectInfo) {
              return null;
            }
            
            return (
              <React.Fragment key={index}>
                <tr 
                  style={{ 
                    backgroundColor: index % 2 === 0 ? '#fff' : '#f8f9fa',
                    cursor: (showUrls && item.urls && item.urls.length > 0) || showProjects ? 'pointer' : 'default'
                  }}
                  onClick={() => {
                    if ((showUrls && item.urls && item.urls.length > 0) || showProjects) {
                      toggleRowExpansion(index);
                    }
                  }}
                >
                  <td style={tdStyle}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {getCategoryIcon(item.category)}
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: '500' }}>
                          {showProjects && projectInfo ? 
                            `${projectInfo.project}` : 
                            (item.window_title || item.detailed_activity || item.application_name)
                          }
                        </span>
                        {showProjects && projectInfo && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                            <span style={{ fontSize: '12px', color: '#666' }}>
                              📄 {projectInfo.file}
                            </span>
                            <span style={{ 
                              fontSize: '10px', 
                              color: '#fff', 
                              background: projectInfo.type === 'Development' ? '#28a745' :
                                         projectInfo.type === 'Server Management' ? '#007bff' :
                                         projectInfo.type === 'Database' ? '#6f42c1' :
                                         projectInfo.type === 'Research' ? '#fd7e14' :
                                         '#6c757d',
                              padding: '2px 6px',
                              borderRadius: '8px',
                              fontWeight: '500'
                            }}>
                              {projectInfo.type}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                <td style={tdStyle}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '500',
                    background: item.category === 'browser' ? '#e3f2fd' :
                               item.category === 'development' ? '#e8f5e8' :
                               item.category === 'productivity' ? '#fff3cd' :
                               item.category === 'entertainment' ? '#fce4ec' :
                               '#f8f9fa',
                    color: item.category === 'browser' ? '#1976d2' :
                           item.category === 'development' ? '#388e3c' :
                           item.category === 'productivity' ? '#f57c00' :
                           item.category === 'entertainment' ? '#c2185b' :
                           '#6c757d'
                  }}>
                    {item.category}
                  </span>
                </td>
                <td style={tdStyle}>
                  <span style={{ fontWeight: '500', color: '#667eea' }}>
                    {formatTime(item.duration)}
                  </span>
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      width: '60px',
                      height: '6px',
                      background: '#e9ecef',
                      borderRadius: '3px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${Math.min(item.percentage, 100)}%`,
                        height: '100%',
                        background: '#667eea',
                        borderRadius: '3px'
                      }} />
                    </div>
                    <span style={{ fontSize: '12px', color: '#666' }}>
                      {item.percentage.toFixed(1)}%
                    </span>
                  </div>
                </td>
                {(showUrls || showProjects) && showDetails && (
                  <td style={tdStyle}>
                    {showProjects ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span style={{ fontSize: '12px', color: '#666' }}>
                          {projectInfo?.path ? '📁 Path available' : '📋 Activity details'}
                        </span>
                        {expandedRows.has(index) ? 
                          <ChevronUp size={14} color="#666" /> : 
                          <ChevronDown size={14} color="#666" />
                        }
                      </div>
                    ) : item.urls && item.urls.length > 0 ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span style={{ fontSize: '12px', color: '#666' }}>
                          {item.urls.length} URL{item.urls.length > 1 ? 's' : ''}
                        </span>
                        {expandedRows.has(index) ? 
                          <ChevronUp size={14} color="#666" /> : 
                          <ChevronDown size={14} color="#666" />
                        }
                      </div>
                    ) : (
                      <span style={{ fontSize: '12px', color: '#ccc' }}>-</span>
                    )}
                  </td>
                )}
              </tr>
                {(showUrls || showProjects) && expandedRows.has(index) && (
                <tr>
                  <td colSpan="5" style={{ ...tdStyle, background: '#f8f9fa', padding: '16px' }}>
                    {showProjects ? (
                      /* Project Details View */
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                        {/* Project Information */}
                        <div>
                          <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px', fontWeight: 'bold' }}>
                            🚀 Project Information:
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontSize: '11px', color: '#666' }}>📁 Project: </span>
                              <span style={{ fontSize: '12px', color: '#333', fontWeight: '500' }}>
                                {projectInfo?.project || 'Unknown Project'}
                              </span>
                              <span style={{ 
                                fontSize: '9px', 
                                color: '#fff', 
                                background: projectInfo?.type === 'Development' ? '#28a745' :
                                           projectInfo?.type === 'Server Management' ? '#007bff' :
                                           projectInfo?.type === 'Database' ? '#6f42c1' :
                                           projectInfo?.type === 'Research' ? '#fd7e14' :
                                           '#6c757d',
                                padding: '2px 5px',
                                borderRadius: '6px',
                                fontWeight: '500'
                              }}>
                                {projectInfo?.type || 'Work'}
                              </span>
                            </div>
                            <div>
                              <span style={{ fontSize: '11px', color: '#666' }}>📄 Activity: </span>
                              <span style={{ fontSize: '11px', color: '#333', fontFamily: 'monospace' }}>
                                {projectInfo?.file || 'Unknown File'}
                              </span>
                            </div>
                            {projectInfo?.path && (
                              <div>
                                <span style={{ fontSize: '11px', color: '#666' }}>🔗 Path: </span>
                                <span style={{ fontSize: '10px', color: '#333', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                                  {projectInfo.path}
                                </span>
                              </div>
                            )}
                            <div>
                              <span style={{ fontSize: '11px', color: '#666' }}>⏱️ Duration: </span>
                              <span style={{ fontSize: '12px', color: '#667eea', fontWeight: '500' }}>
                                {formatTime(item.duration)}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Activity Context */}
                        <div>
                          <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px', fontWeight: 'bold' }}>
                            📋 Activity Context:
                          </div>
                          <div style={{ fontSize: '12px', color: '#333', marginBottom: '8px' }}>
                            {item.detailed_activity || item.window_title || 'No detailed activity information'}
                          </div>
                          
                          {/* Application Used */}
                          <div style={{ marginBottom: '4px' }}>
                            <span style={{ fontSize: '11px', color: '#666' }}>💻 Application: </span>
                            <span style={{ fontSize: '11px', color: '#333' }}>
                              {item.application_name}
                            </span>
                          </div>
                          
                          {/* Category */}
                          <div style={{ marginBottom: '4px' }}>
                            <span style={{ fontSize: '11px', color: '#666' }}>🏷️ Category: </span>
                            <span style={{ fontSize: '11px', color: '#333', textTransform: 'capitalize' }}>
                              {item.category}
                            </span>
                          </div>

                          {/* URLs if available */}
                          {item.urls && item.urls.length > 0 && (
                            <div style={{ marginTop: '8px' }}>
                              <div style={{ fontSize: '11px', color: '#666', marginBottom: '4px' }}>🌐 Related URLs:</div>
                              {item.urls.slice(0, 3).map((url, urlIndex) => (
                                <div key={urlIndex} style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2px' }}>
                                  <ExternalLink size={10} color="#667eea" />
                                  <a 
                                    href={url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    style={{ 
                                      color: '#667eea', 
                                      textDecoration: 'none',
                                      fontSize: '10px'
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {url.length > 50 ? url.substring(0, 50) + '...' : url}
                                  </a>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      /* Original URLs View */
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                        {/* URLs Section */}
                        {item.urls && item.urls.length > 0 && (
                          <div>
                            <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px', fontWeight: 'bold' }}>
                              🌐 Websites Visited:
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                              {item.urls.slice(0, 5).map((url, urlIndex) => (
                                <div key={urlIndex} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <ExternalLink size={12} color="#667eea" />
                                  <a 
                                    href={url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    style={{ 
                                      color: '#667eea', 
                                      textDecoration: 'none',
                                      fontSize: '12px'
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {url}
                                  </a>
                                </div>
                              ))}
                              {item.urls.length > 5 && (
                                <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                                  ... and {item.urls.length - 5} more
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Detailed Activity Section */}
                        <div>
                          <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px', fontWeight: 'bold' }}>
                            📋 Detailed Activity:
                          </div>
                          <div style={{ fontSize: '12px', color: '#333', marginBottom: '8px' }}>
                            {item.detailed_activity || item.window_title}
                          </div>
                          
                          {/* File Path */}
                          {item.file_path && (
                            <div style={{ marginBottom: '4px' }}>
                              <span style={{ fontSize: '11px', color: '#666' }}>📁 File: </span>
                              <span style={{ fontSize: '11px', color: '#333', fontFamily: 'monospace' }}>
                                {item.file_path}
                              </span>
                            </div>
                          )}
                          
                          {/* Database Connection */}
                          {item.database_connection && (
                            <div style={{ marginBottom: '4px' }}>
                              <span style={{ fontSize: '11px', color: '#666' }}>🗄️ Database: </span>
                              <span style={{ fontSize: '11px', color: '#333', fontFamily: 'monospace' }}>
                                {item.database_connection}
                              </span>
                            </div>
                          )}
                          
                          {/* Specific Process */}
                          {item.specific_process && (
                            <div style={{ marginBottom: '4px' }}>
                              <span style={{ fontSize: '11px', color: '#666' }}>⚙️ Process: </span>
                              <span style={{ fontSize: '11px', color: '#333', fontFamily: 'monospace' }}>
                                {item.specific_process}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </td>
                </tr>
              )}
            </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default ActivityTable;
