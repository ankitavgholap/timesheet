#!/usr/bin/env python3
"""
Project Extractor - Extract project information from activity data
"""
import re
from typing import Dict, Optional

def extract_project_info(activity_data: Dict) -> Dict[str, Optional[str]]:
    """
    Extract project information from activity data
    Returns dict with project_name, project_type, and project_file
    """
    app_name = (activity_data.get("application_name", "") or "").lower()
    window_title = activity_data.get("window_title", "") or ""
    file_path = activity_data.get("file_path", "")
    
    # Skip entertainment and system locks
    is_system_lock = "lock" in window_title.lower() or "locked" in window_title.lower() or \
                    "lockapp" in app_name or "logonui" in app_name
    is_entertainment = activity_data.get("category") == "entertainment" or \
                      any(word in window_title.lower() for word in ["youtube", "netflix", "spotify", "music"])
    
    if is_system_lock or is_entertainment:
        return {"project_name": None, "project_type": None, "project_file": None}
    
    # Method 1: FileZilla/FTP - Extract server/domain names
    if any(ftp_app in app_name for ftp_app in ["filezilla", "winscp", "ftp"]):
        # Extract domain or IP from window title
        server_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d+\.\d+\.\d+\.\d+)', window_title)
        if server_match:
            return {
                "project_name": f"FTP: {server_match.group(1)}",
                "project_type": "Server Management",
                "project_file": "Server Connection"
            }
        
        # Extract meaningful part of title
        title_parts = re.split(r'[\s\-\/\\]', window_title)
        meaningful_part = next((part for part in title_parts 
                              if len(part) > 3 and not re.match(r'filezilla|ftp', part, re.I)), None)
        if meaningful_part:
            return {
                "project_name": f"FTP: {meaningful_part}",
                "project_type": "Server Management", 
                "project_file": "Server Connection"
            }
        
        return {
            "project_name": "FileZilla/FTP",
            "project_type": "Server Management",
            "project_file": "Server Connection"
        }
    
    # Method 2: cPanel/Plesk/Hosting
    hosting_keywords = ["cpanel", "plesk", "hosting", "panel", "whm", "directadmin"]
    if any(keyword in window_title.lower() for keyword in hosting_keywords):
        # Extract domain from URL or title
        domain_match = re.search(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', window_title)
        if domain_match:
            return {
                "project_name": f"Hosting: {domain_match.group(1)}",
                "project_type": "Server Management",
                "project_file": "Control Panel"
            }
        
        # Extract meaningful identifier
        title_parts = re.split(r'[\s\-\/]', window_title)
        meaningful_part = next((part for part in title_parts 
                              if len(part) > 3 and not re.match(r'cpanel|plesk|hosting|panel', part, re.I)), None)
        if meaningful_part:
            return {
                "project_name": f"Hosting: {meaningful_part}",
                "project_type": "Server Management",
                "project_file": "Control Panel"
            }
        
        return {
            "project_name": "cPanel/Hosting",
            "project_type": "Server Management", 
            "project_file": "Control Panel"
        }
    
    # Method 3: Browser - Extract websites as projects
    browser_apps = ["chrome", "firefox", "edge", "safari", "browser"]
    if any(browser in app_name for browser in browser_apps):
        # Local development servers
        if "localhost:" in window_title or "127.0.0.1:" in window_title:
            port_match = re.search(r'localhost:(\d+)|127\.0\.0\.1:(\d+)', window_title)
            port = port_match.group(1) or port_match.group(2) if port_match else "unknown"
            return {
                "project_name": f"localhost:{port}",
                "project_type": "Web Development",
                "project_file": "Local Development"
            }
        
        # Extract domain from URL or title
        url_match = re.search(r'https?://([^/\s]+)|([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', window_title)
        if url_match:
            domain = url_match.group(1) or url_match.group(2)
            return {
                "project_name": domain,
                "project_type": "Web Development",
                "project_file": "Website"
            }
        
        # Use first meaningful part of title
        title_parts = window_title.split(' - ')
        first_part = title_parts[0].strip() if title_parts else ""
        if first_part and len(first_part) > 2:
            return {
                "project_name": first_part,
                "project_type": "Web Development",
                "project_file": "Web Page"
            }
        
        return {
            "project_name": "Web Browsing",
            "project_type": "Web Development",
            "project_file": "Browser Activity"
        }
    
    # Method 4: IDE window titles
    ide_apps = ["cursor", "vscode", "code", "pycharm", "intellij", "sublime", "atom", "vim", "emacs"]
    if any(ide in app_name for ide in ide_apps):
        # Pattern: "filename - projectname - IDE"
        ide_pattern = r'^(.+?)\s*-\s*(.+?)\s*-\s*(Visual Studio Code|Cursor|Code|PyCharm|IntelliJ|Sublime|Atom)'
        ide_match = re.search(ide_pattern, window_title, re.I)
        
        if ide_match:
            file_name = ide_match.group(1).strip()
            project_name = ide_match.group(2).strip()
            return {
                "project_name": project_name,
                "project_type": "Development",
                "project_file": file_name
            }
        
        # Try to extract from any part of title
        title_parts = [part.strip() for part in window_title.split(' - ') 
                      if part and not re.match(r'Visual Studio Code|Cursor|Code|PyCharm|IntelliJ|Sublime|Atom', part, re.I)]
        
        if len(title_parts) >= 2:
            return {
                "project_name": title_parts[-1],
                "project_type": "Development", 
                "project_file": title_parts[0]
            }
        elif len(title_parts) == 1 and len(title_parts[0]) > 2:
            return {
                "project_name": title_parts[0],
                "project_type": "Development",
                "project_file": "Code File"
            }
        
        return {
            "project_name": "IDE Work",
            "project_type": "Development",
            "project_file": "Development"
        }
    
    # Method 5: Database tools
    db_apps = ["datagrip", "pgadmin", "phpmyadmin", "mysql", "postgresql", "mongodb"]
    if any(db_app in app_name for db_app in db_apps) or \
       any(keyword in window_title.lower() for keyword in ["database", "sql"]):
        
        # Try to extract database name or connection info
        db_match = re.search(r'([a-zA-Z0-9_-]+)@([a-zA-Z0-9.-]+)|([a-zA-Z0-9_-]+)\s*database', window_title, re.I)
        if db_match:
            db_name = db_match.group(1) or db_match.group(3) or "Database"
            server = db_match.group(2) or ""
            project_name = f"DB: {db_name}@{server}" if server else f"DB: {db_name}"
            return {
                "project_name": project_name,
                "project_type": "Database",
                "project_file": "Database"
            }
        
        # Extract meaningful part from title
        title_parts = re.split(r'[\s\-@]', window_title)
        meaningful_part = next((part for part in title_parts 
                              if len(part) > 3 and not re.match(r'datagrip|pgadmin|mysql|database', part, re.I)), None)
        if meaningful_part:
            return {
                "project_name": f"DB: {meaningful_part}",
                "project_type": "Database",
                "project_file": "Database"
            }
        
        return {
            "project_name": "Database Work",
            "project_type": "Database",
            "project_file": "Database"
        }
    
    # Method 6: API tools
    api_apps = ["postman", "insomnia", "rest"]
    if any(api_app in app_name for api_app in api_apps) or \
       any(keyword in window_title.lower() for keyword in ["api", "postman"]):
        
        # Try to extract API project or collection name
        api_match = re.search(r'([a-zA-Z0-9_-]+)\s*(API|Collection|Request)', window_title, re.I)
        if api_match:
            return {
                "project_name": f"API: {api_match.group(1)}",
                "project_type": "API Development",
                "project_file": "API Testing"
            }
        
        # Extract meaningful part
        title_parts = re.split(r'[\s\-]', window_title)
        meaningful_part = next((part for part in title_parts 
                              if len(part) > 3 and not re.match(r'postman|insomnia|api', part, re.I)), None)
        if meaningful_part:
            return {
                "project_name": f"API: {meaningful_part}",
                "project_type": "API Development",
                "project_file": "API Testing"
            }
        
        return {
            "project_name": "API Development",
            "project_type": "API Development",
            "project_file": "API Testing"
        }
    
    # Method 7: Extract from file path
    if file_path:
        path_parts = file_path.replace('\\', '/').split('/')
        if len(path_parts) > 1:
            parent_dir = path_parts[-2]
            return {
                "project_name": parent_dir,
                "project_type": "Development",
                "project_file": path_parts[-1]
            }
    
    # Method 8: Fallback - Use window title or application name
    if window_title and len(window_title) > 3:
        clean_title = window_title.split(' - ')[0].strip()
        if len(clean_title) > 3:
            return {
                "project_name": clean_title,
                "project_type": "Work",
                "project_file": "Activity"
            }
    
    # Last resort - use application name
    if activity_data.get("application_name") and len(activity_data["application_name"]) > 3:
        app_clean = activity_data["application_name"].replace('.exe', '')
        return {
            "project_name": app_clean,
            "project_type": "Work",
            "project_file": "Application"
        }
    
    return {"project_name": None, "project_type": None, "project_file": None}

