// 1. DynamicDeveloperSelector.jsx - Auto-discovering developer selector

import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, Wifi, WifiOff, Database, Monitor, Settings } from 'lucide-react';

const DynamicDeveloperSelector = ({ onDeveloperChange, selectedDeveloper }) => {
  const [developers, setDevelopers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [lastDiscovered, setLastDiscovered] = useState(null);
  const [discoverySettings, setDiscoverySettings] = useState({
    scanNetwork: false,
    scanLocal: true,
    scanDatabase: true
  });
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    loadDevelopers();
  }, []);

  // Auto-refresh status every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (developers.length > 0) {
        refreshStatus();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [developers]);

  const loadDevelopers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/developers', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDevelopers(data.developers || []);
      }
    } catch (error) {
      console.error('Error loading developers:', error);
    }
    setLoading(false);
  };

  const discoverDevelopers = async (forceRefresh = false) => {
    setDiscovering(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        scan_network: discoverySettings.scanNetwork,
        scan_local: discoverySettings.scanLocal,
        scan_database: discoverySettings.scanDatabase,
        force_refresh: forceRefresh
      });

      const response = await fetch(`http://localhost:8000/discover-developers?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDevelopers(data.developers || []);
        setLastDiscovered(new Date(data.discovered_at));
      }
    } catch (error) {
      console.error('Error discovering developers:', error);
    }
    setDiscovering(false);
  };

  const refreshStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/developers-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDevelopers(data.developers_status || []);
      }
    } catch (error) {
      console.error('Error refreshing status:', error);
    }
  };

  const getStatusIcon = (status, source) => {
    if (source === 'database') return <Database size={16} className="text-blue-500" />;
    
    switch (status) {
      case 'online': return <Wifi size={16} className="text-green-500" />;
      case 'offline': return <WifiOff size={16} className="text-red-500" />;
      case 'database_only': return <Database size={16} className="text-blue-500" />;
      default: return <Monitor size={16} className="text-gray-400" />;
    }
  };

  const getStatusText = (status, source) => {
    if (source === 'database') return 'Database Only';
    
    switch (status) {
      case 'online': return 'Online';
      case 'offline': return 'Offline';
      case 'database_only': return 'Database Only';
      default: return 'Unknown';
    }
  };

  const getStatusColor = (status, source) => {
    if (source === 'database') return 'border-blue-200 bg-blue-50';
    
    switch (status) {
      case 'online': return 'border-green-200 bg-green-50';
      case 'offline': return 'border-red-200 bg-red-50';
      case 'database_only': return 'border-blue-200 bg-blue-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Search size={20} className="text-blue-600" />
          Developer Discovery
          {selectedDeveloper && (
            <span className="text-sm font-normal text-blue-600 bg-blue-100 px-3 py-1 rounded-full ml-2">
              {developers.find(dev => dev.id === selectedDeveloper)?.name || 'Selected'}
            </span>
          )}
        </h3>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Discovery Settings"
          >
            <Settings size={16} />
          </button>
          
          <button
            onClick={refreshStatus}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg border border-blue-200 transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Status
          </button>

          <button
            onClick={() => discoverDevelopers(false)}
            disabled={discovering}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Search size={14} className={discovering ? 'animate-pulse' : ''} />
            {discovering ? 'Discovering...' : 'Discover'}
          </button>
        </div>
      </div>

      {/* Discovery Settings */}
      {showSettings && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg border">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Discovery Settings</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={discoverySettings.scanLocal}
                onChange={(e) => setDiscoverySettings(prev => ({ ...prev, scanLocal: e.target.checked }))}
                className="rounded text-blue-600"
              />
              <span className="text-sm text-gray-600">Scan Local Machine</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={discoverySettings.scanDatabase}
                onChange={(e) => setDiscoverySettings(prev => ({ ...prev, scanDatabase: e.target.checked }))}
                className="rounded text-blue-600"
              />
              <span className="text-sm text-gray-600">Check Database Records</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={discoverySettings.scanNetwork}
                onChange={(e) => setDiscoverySettings(prev => ({ ...prev, scanNetwork: e.target.checked }))}
                className="rounded text-blue-600"
              />
              <span className="text-sm text-gray-600">Scan Network (Slow)</span>
            </label>
          </div>
          
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => discoverDevelopers(true)}
              disabled={discovering}
              className="px-3 py-1 text-xs bg-orange-600 text-white hover:bg-orange-700 rounded transition-colors"
            >
              Force Refresh
            </button>
            
            {lastDiscovered && (
              <span className="text-xs text-gray-500 self-center">
                Last discovered: {lastDiscovered.toLocaleString()}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Developer Selection */}
      {developers.length > 0 ? (
        <>
          <div className="mb-4">
            <select 
              value={selectedDeveloper || ''} 
              onChange={(e) => onDeveloperChange(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg text-gray-700 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select a developer...</option>
              {developers.map((dev) => (
                <option key={dev.id} value={dev.id}>
                  {dev.name} ({dev.hostname}) - {getStatusText(dev.status, dev.source)}
                </option>
              ))}
            </select>
          </div>

          {/* Developer Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {developers.map((dev) => (
              <div 
                key={dev.id} 
                onClick={() => onDeveloperChange(dev.id)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
                  selectedDeveloper === dev.id 
                    ? 'border-blue-500 bg-blue-50 shadow-md' 
                    : `${getStatusColor(dev.status, dev.source)} border-2 hover:border-blue-300`
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(dev.status, dev.source)}
                    <h4 className="font-medium text-gray-800">{dev.name}</h4>
                  </div>
                  {selectedDeveloper === dev.id && (
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  )}
                </div>
                
                <div className="space-y-1">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Host:</span> {dev.hostname || dev.host}
                  </p>
                  
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Status:</span> {getStatusText(dev.status, dev.source)}
                  </p>
                  
                  {dev.activity_count > 0 && (
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Activities:</span> {dev.activity_count.toLocaleString()}
                    </p>
                  )}
                  
                  {dev.last_seen && (
                    <p className="text-xs text-gray-500">
                      Last seen: {new Date(dev.last_seen).toLocaleString()}
                    </p>
                  )}
                  
                  <div className="flex items-center justify-between mt-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      dev.source === 'local' ? 'bg-green-100 text-green-700' :
                      dev.source === 'network' ? 'bg-blue-100 text-blue-700' :
                      dev.source === 'database' ? 'bg-purple-100 text-purple-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {dev.source}
                    </span>
                    
                    {dev.status === 'online' && (
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span className="text-xs text-green-600">Live</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-8">
          <Search size={48} className="mx-auto text-gray-400 mb-4" />
          <h4 className="text-lg font-medium text-gray-600 mb-2">No Developers Found</h4>
          <p className="text-gray-500 mb-4">
            Click "Discover" to automatically find ActivityWatch instances on your network and in your database.
          </p>
          <button
            onClick={() => discoverDevelopers(true)}
            disabled={discovering}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Search size={16} className={discovering ? 'animate-pulse' : ''} />
            {discovering ? 'Discovering...' : 'Start Discovery'}
          </button>
        </div>
      )}

      {/* Loading States */}
      {(loading || discovering) && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
          <div className="text-center">
            <RefreshCw size={32} className="animate-spin text-blue-600 mx-auto mb-2" />
            <p className="text-gray-600">
              {discovering ? 'Discovering developers...' : 'Loading...'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// 2. Enhanced Dashboard.jsx integration

import React, { useState, useEffect } from 'react';
import DynamicDeveloperSelector from './DynamicDeveloperSelector';
// ... other imports

function EnhancedDashboard() {
  const [selectedDeveloper, setSelectedDeveloper] = useState('');
  const [activityData, setActivityData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dataSource, setDataSource] = useState('');
  // ... existing state

  const fetchActivityData = async (developerId = selectedDeveloper) => {
    if (!developerId) {
      setActivityData([]);
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const startDate = startOfDay(new Date()).toISOString();
      const endDate = endOfDay(new Date()).toISOString();
      
      const response = await fetch(
        `http://localhost:8000/activity-data/${developerId}?start_date=${startDate}&end_date=${endDate}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setActivityData(data.data || []);
        setDataSource(data.data_source || '');
        setTotalTime(data.total_time || 0);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('Error fetching activity data:', error);
    }
    setLoading(false);
  };

  const handleDeveloperChange = (developerId) => {
    setSelectedDeveloper(developerId);
    if (developerId) {
      fetchActivityData(developerId);
    } else {
      setActivityData([]);
      setTotalTime(0);
    }
  };

  useEffect(() => {
    if (selectedDeveloper) {
      fetchActivityData();
    }
  }, [startDate, endDate]);

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
          <Monitor className="text-blue-600" />
          Multi-Developer Dashboard
        </h1>
        
        {dataSource && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-600">Data from:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              dataSource === 'activitywatch' ? 'bg-green-100 text-green-700' :
              dataSource === 'database' ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {dataSource === 'activitywatch' ? 'Live ActivityWatch' : 'Database Cache'}
            </span>
          </div>
        )}
      </div>

      {/* Developer Selector */}
      <DynamicDeveloperSelector
        selectedDeveloper={selectedDeveloper}
        onDeveloperChange={handleDeveloperChange}
      />

      {/* Activity Data Display */}
      {selectedDeveloper && activityData.length > 0 && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Time</p>
                  <p className="text-2xl font-bold text-blue-600">{formatTime(totalTime)}</p>
                </div>
                <Clock className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Activities</p>
                  <p className="text-2xl font-bold text-green-600">{activityData.length}</p>
                </div>
                <Activity className="h-8 w-8 text-green-600" />
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Data Source</p>
                  <p className="text-lg font-semibold text-purple-600 capitalize">{dataSource}</p>
                </div>
                {dataSource === 'activitywatch' ? 
                  <Wifi className="h-8 w-8 text-purple-600" /> :
                  <Database className="h-8 w-8 text-purple-600" />
                }
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Last Updated</p>
                  <p className="text-sm text-gray-700">
                    {lastUpdated ? format(lastUpdated, 'HH:mm:ss') : 'Never'}
                  </p>
                </div>
                <RefreshCw className="h-8 w-8 text-orange-600" />
              </div>
            </div>
          </div>

          {/* Activity Charts and Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Activity Distribution</h3>
              <ActivityChart data={activityData} />
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Activities</h3>
              <ActivityTable data={activityData.slice(0, 10)} formatTime={formatTime} />
            </div>
          </div>
        </div>
      )}

      {/* No Developer Selected State */}
      {!selectedDeveloper && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Search size={64} className="mx-auto text-gray-400 mb-6" />
          <h3 className="text-xl font-semibold text-gray-700 mb-4">Welcome to Multi-Developer Dashboard</h3>
          <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
            This dashboard automatically discovers ActivityWatch instances running on your local machine, 
            network, and retrieves historical data from your database. Select a developer above to get started.
          </p>
          <div className="bg-gray-50 rounded-lg p-6 max-w-xl mx-auto">
            <h4 className="font-medium text-gray-800 mb-3">Features:</h4>
            <ul className="text-left text-gray-600 space-y-2">
              <li>• Automatic discovery of ActivityWatch instances</li>
              <li>• Real-time and historical data viewing</li>
              <li>• Network scanning for remote developers</li>
              <li>• Database caching for offline access</li>
              <li>• Live status monitoring</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default EnhancedDashboard;