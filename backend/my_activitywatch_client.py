import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import re
from urllib.parse import urlparse

load_dotenv()

class ActivityWatchClient:
    def __init__(self):
        self.base_url = os.getenv("ACTIVITYWATCH_HOST", "http://localhost:5600")
        self.api_url = f"{self.base_url}/api/0"
        
    def get_buckets(self) -> List[Dict]:
        """Get all available buckets from ActivityWatch"""
        try:
            # Try with trailing slash first (ActivityWatch often redirects to this)
            response = requests.get(f"{self.api_url}/buckets/", allow_redirects=True)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching buckets: {e}")
            # Try alternative endpoints
            try:
                response = requests.get(f"{self.api_url}/buckets", allow_redirects=True)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e2:
                print(f"Error with alternative endpoint: {e2}")
                return {}
    
    def get_events(self, bucket_id: str, start: datetime, end: datetime) -> List[Dict]:
        """Get events from a specific bucket"""
        try:
            # Format dates properly for ActivityWatch API
            start_str = start.strftime('%Y-%m-%dT%H:%M:%S')
            end_str = end.strftime('%Y-%m-%dT%H:%M:%S')
            
            params = {
                'start': start_str,
                'end': end_str,
                'limit': 5000  # Get much more events to capture all activities
            }
            
            # Try without trailing slash first (this seems to work)
            response = requests.get(f"{self.api_url}/buckets/{bucket_id}/events", params=params, allow_redirects=True)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching events from bucket {bucket_id}: {e}")
            try:
                # Try with trailing slash as fallback
                response = requests.get(f"{self.api_url}/buckets/{bucket_id}/events/", params=params, allow_redirects=True)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e2:
                print(f"Error with alternative events endpoint: {e2}")
                return []
    
    def categorize_application(self, app_name: str, window_title: str = "") -> str:
        """Categorize application based on name and window title"""
        app_name_lower = app_name.lower()
        window_title_lower = window_title.lower()
        
        # Browsers
        if any(browser in app_name_lower for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']):
            return 'browser'
        
        # IDEs and Code Editors
        if any(ide in app_name_lower for ide in ['vscode', 'visual studio', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs', 'notepad++', 'cursor', 'code']):
            return 'development'
        
        # Database Tools
        if any(db in app_name_lower for db in ['datagrip', 'pgadmin', 'mysql', 'dbeaver', 'navicat', 'sqlserver', 'oracle']):
            return 'database'
        
        # Productivity
        if any(prod in app_name_lower for prod in ['word', 'excel', 'powerpoint', 'outlook', 'teams', 'slack', 'discord', 'zoom', 'notion', 'obsidian', 'postman']):
            return 'productivity'
        
        # Media
        if any(media in app_name_lower for media in ['spotify', 'youtube', 'vlc', 'media player', 'netflix', 'twitch']):
            return 'entertainment'
        
        # System processes (including .exe files)
        if (any(system in app_name_lower for system in ['explorer', 'finder', 'terminal', 'cmd', 'powershell', 'task manager', 'lock', 'dwm', 'winlogon', 'csrss', 'lsass', 'services', 'svchost', 'searchhost', 'notepad']) 
            or app_name_lower.endswith('.exe') and any(sys_exe in app_name_lower for sys_exe in ['lock', 'explorer', 'dwm', 'winlogon', 'searchhost', 'notepad'])):
            return 'system'
        
        # Development tools that might not be caught above
        if any(dev in app_name_lower for dev in ['git', 'npm', 'node', 'python', 'java', 'dotnet']):
            return 'development'
        
        return 'other'
    
    def extract_detailed_info(self, window_title: str, app_name: str) -> dict:
        """Extract detailed information from window title and app name"""
        info = {
            'url': None,
            'file_path': None,
            'database_connection': None,
            'specific_process': None,
            'detailed_activity': None
        }
        
        app_name_lower = app_name.lower()
        window_title_lower = window_title.lower()
        
        # Browser URL extraction (enhanced)
        if any(browser in app_name_lower for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']):
            info['url'] = self.extract_url_from_browser_title(window_title)
            # For "Claude - Google Chrome", show "Browsing Claude (claude.ai)"
            if ' - ' in window_title:
                page_title = window_title.split(' - ')[0].strip()
                info['detailed_activity'] = f"Browsing: {page_title}"
                if info['url']:
                    info['detailed_activity'] += f" ({info['url']})"
            else:
                info['detailed_activity'] = f"Browsing: {window_title}"
        
        # IDE and Code Editor details
        elif any(ide in app_name_lower for ide in ['vscode', 'visual studio', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs', 'notepad++', 'cursor']):
            info['file_path'] = self.extract_file_path(window_title)
            # For "package.json - timesheet - Cursor", show "Coding: package.json in timesheet"
            if info['file_path']:
                if '/' in info['file_path']:
                    project, filename = info['file_path'].rsplit('/', 1)
                    info['detailed_activity'] = f"Coding: {filename} in {project}"
                else:
                    info['detailed_activity'] = f"Coding: {info['file_path']}"
            else:
                info['detailed_activity'] = f"Coding: {window_title}"
        
        # Database tools (DataGrip, pgAdmin, etc.)
        elif any(db_tool in app_name_lower for db_tool in ['datagrip', 'pgadmin', 'mysql', 'dbeaver', 'navicat', 'sqlserver', 'oracle']):
            info['database_connection'] = self.extract_database_info(window_title)
            if info['database_connection']:
                info['detailed_activity'] = f"Database: Connected to {info['database_connection']}"
            else:
                # For DataGrip64.exe, show a cleaner name
                clean_app_name = app_name.replace('.exe', '').replace('64', '')
                info['detailed_activity'] = f"Database: {clean_app_name} - {window_title}"
        
        # System processes and executables
        elif (self.categorize_application(app_name, window_title) == 'system' or 
              app_name_lower.endswith('.exe')):
            info['specific_process'] = app_name
            # Show exact process name like "LockApp.exe", "explorer.exe"
            clean_app_name = app_name.replace('.exe', '') if app_name.endswith('.exe') else app_name
            if window_title and window_title != app_name and len(window_title.strip()) > 0:
                info['detailed_activity'] = f"System: {clean_app_name} - {window_title}"
            else:
                info['detailed_activity'] = f"System: {clean_app_name}"
        
        # Office applications
        elif any(office in app_name_lower for office in ['word', 'excel', 'powerpoint', 'outlook']):
            info['file_path'] = self.extract_office_document(window_title)
            if info['file_path']:
                info['detailed_activity'] = f"Office: {info['file_path']}"
            else:
                info['detailed_activity'] = f"Office: {window_title}"
        
        # Communication apps
        elif any(comm in app_name_lower for comm in ['teams', 'slack', 'discord', 'zoom', 'skype']):
            info['detailed_activity'] = f"Communication: {window_title}"
        
        # Media applications
        elif any(media in app_name_lower for media in ['spotify', 'youtube', 'vlc', 'media player', 'netflix']):
            # For media like "Aaj Ka Khiladi (Ninnu Kori) Latest Hindi Dubbed Movie"
            info['detailed_activity'] = f"Media: {window_title}"
        
        # Default detailed activity
        if not info['detailed_activity']:
            info['detailed_activity'] = f"{app_name}: {window_title}"
        
        return info
    
    def extract_url_from_browser_title(self, window_title: str) -> Optional[str]:
        """Enhanced URL extraction from browser window title"""
        # For titles like "Claude - Google Chrome", extract the main site
        browser_patterns = [
            # Common browser title formats: "Page Title - Browser Name"
            r'^(.+?)\s*-\s*(Google Chrome|Mozilla Firefox|Microsoft Edge|Safari|Opera|Brave)',
            # Direct URL patterns
            r'https?://[^\s\)]+',
            r'www\.[^\s\)]+',
        ]
        
        for pattern in browser_patterns:
            match = re.search(pattern, window_title, re.IGNORECASE)
            if match:
                if 'http' in match.group() or 'www' in match.group():
                    # Direct URL found
                    url = match.group()
                    if not url.startswith('http'):
                        url = 'https://' + url
                    try:
                        parsed = urlparse(url)
                        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    except:
                        return url
                else:
                    # Page title found, try to infer URL
                    page_title = match.group(1).strip()
                    
                    # Map common page titles to URLs
                    title_to_url = {
                        'claude': 'https://claude.ai',
                        'chatgpt': 'https://chat.openai.com',
                        'github': 'https://github.com',
                        'stackoverflow': 'https://stackoverflow.com',
                        'google': 'https://google.com',
                        'youtube': 'https://youtube.com',
                        'gmail': 'https://gmail.com',
                        'linkedin': 'https://linkedin.com',
                        'twitter': 'https://twitter.com',
                        'facebook': 'https://facebook.com',
                    }
                    
                    page_lower = page_title.lower()
                    for key, url in title_to_url.items():
                        if key in page_lower:
                            return url
                    
                    # If no mapping found, create a generic URL
                    if len(page_title) < 50 and not any(char in page_title for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
                        return f"https://www.{page_title.lower().replace(' ', '')}.com"
        
        # Enhanced domain extraction patterns
        domain_patterns = [
            r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}',  # Domain pattern
        ]
        
        for pattern in domain_patterns:
            matches = re.findall(pattern, window_title)
            for match in matches:
                if isinstance(match, tuple):
                    domain = ''.join(match)
                else:
                    domain = match
                
                # Filter out common non-domain words
                if not any(word in domain.lower() for word in ['document', 'untitled', 'new', 'file', 'google', 'chrome', 'firefox']):
                    return f"https://{domain}"
        
        return None
    
    def extract_file_path(self, window_title: str) -> Optional[str]:
        """Extract file path from IDE window title"""
        # Enhanced patterns for different IDE title formats
        patterns = [
            # Full Windows path
            r'([A-Za-z]:\\[^|<>:*?"]+\.[a-zA-Z0-9]+)',
            # Unix path
            r'(/[^|<>:*?"]+\.[a-zA-Z0-9]+)',
            # Cursor/VS Code format: "filename.ext - project - Editor"
            r'^([^-]+\.[a-zA-Z0-9]+)\s*-\s*([^-]+)\s*-\s*(Cursor|Code|Visual Studio)',
            # Simple format: "filename.ext - Editor"
            r'^([^-]+\.[a-zA-Z0-9]+)\s*-\s*(Cursor|Code|Visual Studio|PyCharm|IntelliJ)',
            # Project format: "project - Editor" (like "timesheet - Cursor")
            r'^([^-]+)\s*-\s*(Cursor|Code|Visual Studio|PyCharm|IntelliJ)$',
            # Just filename with extension at start
            r'^([^\\/:*?"<>|]+\.[a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, window_title, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    # For patterns with multiple groups
                    first_part = match.group(1).strip()
                    second_part = match.group(2).strip() if len(match.groups()) > 1 else ""
                    
                    # If second part is an editor name, first part is the file/project
                    if second_part.lower() in ['cursor', 'code', 'visual studio', 'pycharm', 'intellij']:
                        return first_part
                    # If first part has extension, it's a file in a project
                    elif '.' in first_part and len(first_part.split('.')) == 2:
                        return f"{second_part}/{first_part}"
                    else:
                        return first_part
                else:
                    return match.group(1).strip()
        
        return None
    
    def extract_database_info(self, window_title: str) -> Optional[str]:
        """Extract database connection info from database tool window title"""
        # Common database tool patterns
        db_patterns = [
            r'@([^@\s]+)',  # @hostname or @database
            r'([a-zA-Z0-9_]+@[a-zA-Z0-9.-]+)',  # user@host
            r'([a-zA-Z0-9_]+)\s*-\s*([a-zA-Z0-9.-]+)',  # database - host
        ]
        
        for pattern in db_patterns:
            match = re.search(pattern, window_title)
            if match:
                return match.group()
        
        return None
    
    def extract_office_document(self, window_title: str) -> Optional[str]:
        """Extract document name from Office application title"""
        # Remove common Office app suffixes
        title = window_title
        office_suffixes = [' - Word', ' - Excel', ' - PowerPoint', ' - Microsoft Word', ' - Microsoft Excel', ' - Microsoft PowerPoint']
        
        for suffix in office_suffixes:
            if suffix in title:
                title = title.replace(suffix, '')
                break
        
        return title.strip() if title.strip() else None
    
    def get_activity_data(self, start: datetime, end: datetime) -> List[Dict]:
        """Get processed activity data from ActivityWatch"""
        buckets = self.get_buckets()
        activity_data = []
        
        for bucket_name, bucket_info in buckets.items():
            # Focus on window and browser buckets
            if 'afk' in bucket_name.lower():
                continue
                
            events = self.get_events(bucket_name, start, end)
            
            for event in events:
                data = event.get('data', {})
                duration = event.get('duration', 0)
                timestamp = datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00'))
                
                app_name = data.get('app', data.get('application', 'Unknown'))
                window_title = data.get('title', '')
                
                # Skip very short activities (less than 5 seconds)
                if duration < 5:
                    continue
                
                category = self.categorize_application(app_name, window_title)
                
                # Extract detailed information
                detailed_info = self.extract_detailed_info(window_title, app_name)
                
                activity_data.append({
                    'application_name': app_name,
                    'window_title': window_title,
                    'url': detailed_info['url'],
                    'file_path': detailed_info['file_path'],
                    'database_connection': detailed_info['database_connection'],
                    'specific_process': detailed_info['specific_process'],
                    'detailed_activity': detailed_info['detailed_activity'],
                    'category': category,
                    'duration': duration,
                    'timestamp': timestamp
                })
        
        return activity_data
    
    def get_top_window_titles(self, start: datetime, end: datetime, limit: int = 20) -> List[Dict]:
        """Get top window titles by duration from ActivityWatch - Direct API call for better data"""
        try:
            print(f"🔍 Fetching window titles from {start} to {end}")
            
            # Use direct API call instead of processed activity data
            buckets = self.get_buckets()
            all_events = []
            
            for bucket_name, bucket_info in buckets.items():
                # Skip AFK buckets but include all others
                if 'afk' in bucket_name.lower():
                    continue
                    
                print(f"📊 Getting events from bucket: {bucket_name}")
                events = self.get_events(bucket_name, start, end)
                
                for event in events:
                    data = event.get('data', {})
                    duration = event.get('duration', 0)
                    timestamp = datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00'))
                    
                    app_name = data.get('app', data.get('application', 'Unknown'))
                    window_title = data.get('title', '')
                    
                    # Skip very short activities, locks, and non-work activities
                    if duration < 5:
                        continue
                    
                    # Skip entertainment and non-work activities
                    if self._is_non_work_activity(window_title, app_name):
                        continue
                    
                    all_events.append({
                        'window_title': window_title,
                        'application_name': app_name,
                        'duration': duration,
                        'timestamp': timestamp,
                        'bucket': bucket_name
                    })
            
            print(f"📈 Found {len(all_events)} total events")
            
            # Group by window title and sum durations
            title_stats = {}
            for event in all_events:
                title = event['window_title']
                app_name = event['application_name']
                duration = event['duration']
                timestamp = event['timestamp']
                
                key = f"{title}|{app_name}"
                if key not in title_stats:
                    title_stats[key] = {
                        'window_title': title,
                        'application_name': app_name,
                        'category': self.categorize_application(app_name, title),
                        'total_duration': 0,
                        'activity_count': 0,
                        'project_info': self.extract_project_from_title(title, app_name),
                        'last_seen': timestamp
                    }
                
                title_stats[key]['total_duration'] += duration
                title_stats[key]['activity_count'] += 1
                
                # Keep the most recent timestamp
                if timestamp > title_stats[key]['last_seen']:
                    title_stats[key]['last_seen'] = timestamp
            
            # Sort by total duration and return top results
            sorted_titles = sorted(
                title_stats.values(), 
                key=lambda x: x['total_duration'], 
                reverse=True
            )
            
            print(f"🏆 Returning top {min(limit, len(sorted_titles))} window titles")
            return sorted_titles[:limit]
            
        except Exception as e:
            print(f"❌ Error getting top window titles: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_project_from_title(self, window_title: str, app_name: str) -> Dict:
        """Extract project information from window title and app name"""
        app_name_lower = app_name.lower()
        
        # IDE Projects
        if any(ide in app_name_lower for ide in ['cursor', 'vscode', 'code', 'pycharm', 'intellij']):
            # Pattern: "filename.ext - project - IDE"
            ide_pattern = r'^(.+?)\s*-\s*(.+?)\s*-\s*(Cursor|Code|Visual Studio|PyCharm|IntelliJ)'
            match = re.search(ide_pattern, window_title, re.IGNORECASE)
            if match:
                return {
                    'project_name': match.group(2).strip(),
                    'file_name': match.group(1).strip(),
                    'project_type': 'Development'
                }
            
            # Pattern: "project - IDE"
            simple_pattern = r'^(.+?)\s*-\s*(Cursor|Code|Visual Studio|PyCharm|IntelliJ)$'
            match = re.search(simple_pattern, window_title, re.IGNORECASE)
            if match:
                return {
                    'project_name': match.group(1).strip(),
                    'file_name': 'Project Root',
                    'project_type': 'Development'
                }
        
        # Browser Projects
        elif any(browser in app_name_lower for browser in ['chrome', 'firefox', 'edge', 'safari']):
            # Extract domain or page title
            if ' - ' in window_title:
                page_title = window_title.split(' - ')[0].strip()
                
                # Check for localhost development
                if 'localhost:' in window_title:
                    port_match = re.search(r'localhost:(\d+)', window_title)
                    port = port_match.group(1) if port_match else 'unknown'
                    return {
                        'project_name': f'localhost:{port}',
                        'file_name': page_title,
                        'project_type': 'Web Development'
                    }
                
                # Check for known domains
                url_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', window_title)
                if url_match:
                    return {
                        'project_name': url_match.group(1),
                        'file_name': page_title,
                        'project_type': 'Web Development'
                    }
                
                return {
                    'project_name': page_title,
                    'file_name': 'Web Page',
                    'project_type': 'Web Development'
                }
        
        # FileZilla/FTP
        elif 'filezilla' in app_name_lower or 'ftp' in app_name_lower:
            server_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d+\.\d+\.\d+\.\d+)', window_title)
            if server_match:
                return {
                    'project_name': f'FTP: {server_match.group(1)}',
                    'file_name': 'Server Connection',
                    'project_type': 'Server Management'
                }
        
        # cPanel/Hosting
        elif any(panel in window_title.lower() for panel in ['cpanel', 'plesk', 'hosting']):
            domain_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', window_title)
            if domain_match:
                return {
                    'project_name': f'Hosting: {domain_match.group(1)}',
                    'file_name': 'Control Panel',
                    'project_type': 'Server Management'
                }
        
        # Database Tools
        elif any(db in app_name_lower for db in ['datagrip', 'pgadmin', 'mysql', 'dbeaver']):
            db_match = re.search(r'([a-zA-Z0-9_-]+)@([a-zA-Z0-9.-]+)', window_title)
            if db_match:
                return {
                    'project_name': f'DB: {db_match.group(1)}@{db_match.group(2)}',
                    'file_name': 'Database',
                    'project_type': 'Database'
                }
        
        # Default fallback
        return {
            'project_name': app_name.replace('.exe', ''),
            'file_name': window_title[:50] + '...' if len(window_title) > 50 else window_title,
            'project_type': 'Work'
        }

    def _is_non_work_activity(self, window_title: str, app_name: str) -> bool:
        """Check if activity is non-work related and should be filtered out"""
        if not window_title and not app_name:
            return True
        
        # Filter out empty or unknown activities
        if (not window_title or window_title.strip() == '' or 
            app_name in ['Unknown', 'unknown', ''] or
            window_title.strip() == '' or
            len(window_title.strip()) < 3):
            return True
            
        title_lower = window_title.lower() if window_title else ''
        app_lower = app_name.lower() if app_name else ''
        
        # Generic/meaningless titles to filter out
        generic_keywords = [
            'new tab', 'blank page', 'untitled', 'loading', 'please wait',
            'error', '404', 'not found', 'access denied', 'forbidden',
            'react', 'node', 'npm', 'yarn', 'webpack', 'babel'  # Generic tech terms without context
        ]
        
        # Entertainment and non-work activities to filter out
        entertainment_keywords = [
            'youtube', 'netflix', 'spotify', 'music', 'video', 'movie', 'song',
            'entertainment', 'game', 'gaming', 'twitch', 'stream', 'instagram',
            'facebook', 'twitter', 'tiktok', 'snapchat', 'whatsapp', 'telegram',
            'reddit', 'pinterest', 'linkedin personal', 'dating', 'shopping',
            'amazon personal', 'flipkart', 'myntra', 'news', 'cricket', 'sports',
            'bollywood', 'hindi', 'dubbed movie', 'latest movie', 'trailer'
        ]
        
        # System and lock activities
        system_keywords = [
            'lock screen', 'locked', 'lockapp', 'screensaver', 'idle',
            'windows default lock', 'logon', 'login screen', 'shutdown',
            'restart', 'sleep mode', 'hibernate'
        ]
        
        # Check for generic/meaningless content
        for keyword in generic_keywords:
            if keyword in title_lower or keyword in app_lower:
                return True
        
        # Check for entertainment content
        for keyword in entertainment_keywords:
            if keyword in title_lower or keyword in app_lower:
                return True
        
        # Check for system activities
        for keyword in system_keywords:
            if keyword in title_lower or keyword in app_lower:
                return True
        
        # Keep work-related activities
        work_keywords = [
            'development', 'code', 'programming', 'cursor', 'vscode', 'visual studio',
            'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'emacs', 'notepad++',
            'git', 'github', 'gitlab', 'bitbucket', 'stackoverflow', 'documentation',
            'api', 'database', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'server', 'hosting', 'cpanel', 'plesk', 'filezilla', 'ssh', 'terminal',
            'cmd', 'powershell', 'bash', 'ubuntu', 'linux', 'aws', 'azure', 'gcp',
            'docker', 'kubernetes', 'nginx', 'apache', 'php', 'python', 'javascript',
            'react', 'vue', 'angular', 'node', 'npm', 'yarn', 'webpack', 'babel',
            'typescript', 'html', 'css', 'sass', 'scss', 'bootstrap', 'tailwind',
            'figma', 'photoshop', 'illustrator', 'canva', 'design', 'ui', 'ux',
            'project', 'client', 'work', 'business', 'admin', 'dashboard', 'panel',
            'claude', 'chatgpt', 'ai', 'automation', 'script', 'tool', 'utility',
            'testing', 'debug', 'error', 'bug', 'fix', 'deploy', 'build', 'compile',
            'localhost', '127.0.0.1', 'dev', 'staging', 'production', 'live',
            'waaree', 'firsteconomy', 'gera', 'istana', 'kiki', 'leads', 'crm',
            'salesforce', 'integration', 'ajax', 'form', 'validation', 'email',
            'mail', 'inbox', 'contact', 'inquiry', 'website', 'domain', 'dns',
            'ssl', 'certificate', 'backup', 'migration', 'update', 'upgrade'
        ]
        
        # If it contains work keywords, it's work-related
        for keyword in work_keywords:
            if keyword in title_lower or keyword in app_lower:
                return False
        
        # If it's a browser activity, check if it's work-related
        if any(browser in app_lower for browser in ['chrome', 'firefox', 'edge', 'safari']):
            # Check if it's a work-related website or localhost
            if ('localhost' in title_lower or '127.0.0.1' in title_lower or 
                'dev' in title_lower or 'admin' in title_lower or 
                'dashboard' in title_lower or 'panel' in title_lower or
                'cpanel' in title_lower or 'plesk' in title_lower or
                any(domain in title_lower for domain in [
                    'github.com', 'stackoverflow.com', 'docs.', 'api.',
                    'developer.', 'console.', 'aws.', 'azure.', 'cloud.',
                    'firsteconomy.com', 'waaree.com', 'claude.ai', 'openai.com'
                ])):
                return False
            
            # If it's just a generic browser activity without work context, filter it
            if not any(work_word in title_lower for work_word in [
                'project', 'work', 'client', 'business', 'development', 'code',
                'api', 'database', 'server', 'admin', 'dashboard', 'integration'
            ]):
                return True
        
        # Default: if we can't determine, keep it (better to show too much than too little)
        return False

    def test_connection(self) -> bool:
        """Test connection to ActivityWatch server"""
        try:
            response = requests.get(f"{self.api_url}/buckets", timeout=5)
            return response.status_code == 200
        except:
            return False
