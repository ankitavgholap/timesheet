# ActivityWatch Sync Client

This client automatically syncs your local ActivityWatch data to the central timesheet server, enabling team productivity tracking and centralized analytics.

## 🎯 Features

- **Automatic Sync**: Continuously syncs ActivityWatch data every 30 minutes
- **Secure**: Token-based authentication with encrypted HTTPS communication
- **Reliable**: Automatic retry and error handling
- **Lightweight**: Minimal resource usage, runs silently in background
- **Flexible**: Configurable sync intervals and data retention
- **Logging**: Comprehensive logging for troubleshooting

## 📋 Prerequisites

### Software Requirements
- **Python 3.8+** installed on your machine
- **ActivityWatch** installed and running (get from [activitywatch.net](https://activitywatch.net/))
- **Internet connection** to reach the central server

### Server Requirements
- Your system administrator should have provided:
  - Server URL (e.g., `https://timesheet.company.com`)
  - Your unique Developer ID (e.g., `dev001`) 
  - Your API token for authentication

## 🚀 Quick Start

### 1. Download and Setup

#### Windows
```bash
# Download the client files to a folder like C:\ActivityWatchSync\
# Double-click setup.bat to run automatic setup
setup.bat
```

#### Linux/macOS
```bash
# Download the client files to a folder like ~/activitywatch-sync/
# Make setup script executable and run it
chmod +x setup.sh
./setup.sh
```

### 2. Configure

Edit the `.env` file with your details:

```env
# Server Configuration (provided by admin)
SERVER_URL=https://timesheet.company.com/api/v1
DEVELOPER_ID=john_doe
API_TOKEN=your-secure-api-token-here

# Local ActivityWatch (usually no need to change)
ACTIVITYWATCH_HOST=http://localhost:5600

# Sync frequency (30 minutes is recommended)
SYNC_INTERVAL_MINUTES=30
```

### 3. Test Connection

```bash
# Windows
venv\Scripts\activate.bat
python activitywatch_sync.py --test

# Linux/macOS
source venv/bin/activate
python activitywatch_sync.py --test
```

You should see:
```
✅ ActivityWatch connection: ✅
✅ Server connection: ✅
✅ Authentication: ✅
✅ All connections successful!
```

### 4. Start Syncing

```bash
# Run continuous sync (stays running)
python activitywatch_sync.py --continuous

# Or sync last 24 hours once
python activitywatch_sync.py --sync-hours 24
```

## 🔧 Usage Options

### Command Line Arguments

```bash
# Test connections only
python activitywatch_sync.py --test

# One-time sync (specify hours of data)
python activitywatch_sync.py --sync-hours 8

# Continuous sync (default, runs forever)
python activitywatch_sync.py --continuous
python activitywatch_sync.py  # same as --continuous
```

### Configuration Options

Edit `.env` file to customize:

```env
# How often to sync (in minutes)
SYNC_INTERVAL_MINUTES=30

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Custom log file location
LOG_FILE=custom_sync.log

# ActivityWatch host (if running on different port)
ACTIVITYWATCH_HOST=http://localhost:5600
```

## 🔄 Running as a Service

### Windows Service

1. **Install NSSM** (Non-Sucking Service Manager):
   - Download from [nssm.cc](https://nssm.cc/)
   - Extract to `C:\nssm\`

2. **Create Service**:
```cmd
# Open Command Prompt as Administrator
cd C:\path\to\activitywatch-sync
C:\nssm\nssm.exe install "ActivityWatch Sync"

# Configure service in the GUI that opens:
Application Path: C:\path\to\activitywatch-sync\venv\Scripts\python.exe
Application Directory: C:\path\to\activitywatch-sync
Arguments: activitywatch_sync.py --continuous
```

3. **Start Service**:
```cmd
net start "ActivityWatch Sync"
```

### Linux Systemd Service

1. **Create service file**:
```bash
sudo nano /etc/systemd/system/activitywatch-sync.service
```

2. **Add configuration**:
```ini
[Unit]
Description=ActivityWatch Sync Client
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/activitywatch-sync
ExecStart=/home/your-username/activitywatch-sync/venv/bin/python activitywatch_sync.py --continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable activitywatch-sync
sudo systemctl start activitywatch-sync

# Check status
sudo systemctl status activitywatch-sync
```

### macOS LaunchAgent

1. **Create plist file**:
```bash
nano ~/Library/LaunchAgents/com.company.activitywatch-sync.plist
```

2. **Add configuration**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company.activitywatch-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/activitywatch-sync/venv/bin/python</string>
        <string>/path/to/activitywatch-sync/activitywatch_sync.py</string>
        <string>--continuous</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/activitywatch-sync</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

3. **Load and start**:
```bash
launchctl load ~/Library/LaunchAgents/com.company.activitywatch-sync.plist
launchctl start com.company.activitywatch-sync
```

## 📊 What Data is Synced

The client syncs the following information from your ActivityWatch:

### Collected Data
- **Application names** (e.g., "Chrome.exe", "VSCode")
- **Window titles** (e.g., "Project - Visual Studio Code")
- **Duration** of each activity
- **Timestamps** when activities occurred
- **Bucket information** (ActivityWatch data source)

### Processed Information
The server intelligently processes this data to extract:
- **Project names** (from IDE window titles)
- **File names** being worked on
- **Websites visited** (from browser titles)
- **Application categories** (development, productivity, etc.)
- **Working hours calculations**

### Privacy Notes
- **No file contents** are ever transmitted
- **No screenshots** or keystrokes are captured
- **Only window titles and app names** are sent
- **All data encrypted** in transit with HTTPS
- **Local ActivityWatch data** remains on your machine

## 📈 Monitoring and Logs

### Log Files
The client creates detailed logs in `activitywatch_sync.log`:

```bash
# View recent logs
tail -f activitywatch_sync.log

# Windows equivalent
powershell Get-Content activitywatch_sync.log -Wait -Tail 20
```

### Log Levels
Set `LOG_LEVEL` in `.env` for different detail levels:
- **ERROR**: Only errors
- **WARNING**: Errors and warnings
- **INFO**: General operation info (recommended)
- **DEBUG**: Detailed debug information

### Sample Log Output
```
2025-01-15 14:30:01 - INFO - 🔄 Starting sync for period: 2025-01-15 13:30:01 to 2025-01-15 14:30:01
2025-01-15 14:30:02 - INFO - Collected 47 activities from local ActivityWatch
2025-01-15 14:30:03 - INFO - ✅ Successfully sent 47 activities to server
2025-01-15 14:30:03 - INFO - Server response: Stored 47 activities for John Doe
```

## ❗ Troubleshooting

### Common Issues

#### 1. "ActivityWatch connection: ❌"
**Problem**: Can't connect to local ActivityWatch
**Solutions**:
- Ensure ActivityWatch is running
- Check if web UI works: http://localhost:5600
- Try restarting ActivityWatch
- Check if port 5600 is blocked by firewall

#### 2. "Server connection: ❌"
**Problem**: Can't reach the central server
**Solutions**:
- Check your internet connection
- Verify SERVER_URL in `.env` file
- Check if company firewall blocks the connection
- Try accessing the URL in a browser

#### 3. "Authentication: ❌"
**Problem**: Invalid credentials
**Solutions**:
- Verify DEVELOPER_ID and API_TOKEN in `.env`
- Contact your system administrator for new credentials
- Check for extra spaces or characters in credentials

#### 4. "No activities found to sync"
**Problem**: ActivityWatch has no data
**Solutions**:
- Use your computer normally for a while
- Check ActivityWatch is tracking activities
- Verify ActivityWatch web UI shows data
- Try syncing a longer time period: `--sync-hours 24`

### Getting Help

1. **Check logs** in `activitywatch_sync.log`
2. **Run test mode**: `python activitywatch_sync.py --test`
3. **Try verbose logging**: Set `LOG_LEVEL=DEBUG` in `.env`
4. **Contact your system administrator** with:
   - Your DEVELOPER_ID
   - Relevant log entries
   - Error messages

## 🔧 Advanced Configuration

### Custom Sync Intervals
```env
# Sync every 15 minutes (more frequent)
SYNC_INTERVAL_MINUTES=15

# Sync every 2 hours (less frequent)
SYNC_INTERVAL_MINUTES=120
```

### Custom ActivityWatch Port
```env
# If ActivityWatch runs on different port
ACTIVITYWATCH_HOST=http://localhost:5700
```

### Network Proxy Support
```env
# For corporate networks with proxy
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

### Multiple Sync Clients
If you have multiple computers, install the client on each:
1. Use the **same DEVELOPER_ID** across all machines
2. Use the **same API_TOKEN** across all machines
3. Server will merge data from all your machines

## 🔐 Security

### Data Security
- All communication uses **HTTPS encryption**
- API tokens are **unique per developer**
- **No sensitive file contents** are transmitted
- **Local data never deleted** by the sync process

### Token Security
- **Never share** your API token
- **Don't commit** .env files to version control
- **Rotate tokens** periodically (contact admin)
- **Revoke tokens** if compromised

## 📝 Version History

### v1.0.0 (Current)
- Initial release
- Basic ActivityWatch sync functionality
- Token-based authentication
- Automatic retry and error handling
- Comprehensive logging
- Service installation support

## 🤝 Support

For technical support:
1. Check this documentation
2. Review log files
3. Contact your system administrator
4. Include relevant error messages and logs

---

**Note**: This client is designed to work with your company's centralized timesheet system. All data is processed according to your organization's privacy policies.
