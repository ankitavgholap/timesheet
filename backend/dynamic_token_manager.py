# dynamic_token_manager.py
# Completely dynamic token generation system

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
from pathlib import Path

class DynamicTokenManager:
    def __init__(self, config_file: str = "token_manager_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_or_create_config()
        self.engine = create_engine(self.config["database_url"])
    
    def load_or_create_config(self) -> Dict:
        """Load configuration or create default one"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default configuration
            default_config = {
                "database_url": "postgresql://postgres:asdf1234@localhost:5432/timesheet",
                "api_base_url": "https://api-timesheet.firsteconomy.com",
                "master_passwords": [],  # Will be generated dynamically
                "token_settings": {
                    "expiry_days": 365,
                    "token_prefix": "AWToken_",
                    "token_length": 48
                },
                "security": {
                    "require_email_verification": False,
                    "allowed_domains": [],  # Empty = allow all
                    "max_tokens_per_developer": 5
                },
                "notifications": {
                    "admin_email": "",
                    "send_token_notifications": False
                }
            }
            
            self.save_config(default_config)
            print(f"📝 Created default config: {self.config_file}")
            print("🔧 Please configure the settings and run again")
            
            return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def generate_master_password(self) -> str:
        """Generate a new master password"""
        # Create readable but secure password
        words = ['Time', 'Sheet', 'Track', 'Work', 'Code', 'Dev', 'Team']
        password = f"{secrets.choice(words)}{secrets.choice(words)}{secrets.randbelow(9999):04d}!"
        return password
    
    def add_master_password(self, description: str = "Default") -> str:
        """Add a new master password"""
        password = self.generate_master_password()
        
        password_entry = {
            "password": password,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "usage_count": 0
        }
        
        self.config["master_passwords"].append(password_entry)
        self.save_config(self.config)
        
        print(f"✅ New master password generated: {password}")
        print(f"📋 Description: {description}")
        
        return password
    
    def validate_master_password(self, password: str) -> bool:
        """Validate master password"""
        for entry in self.config["master_passwords"]:
            if entry["password"] == password and entry["active"]:
                # Increment usage count
                entry["usage_count"] = entry.get("usage_count", 0) + 1
                entry["last_used"] = datetime.now().isoformat()
                self.save_config(self.config)
                return True
        return False
    
    def generate_api_token(self, developer_id: str) -> str:
        """Generate API token"""
        prefix = self.config["token_settings"]["token_prefix"]
        length = self.config["token_settings"]["token_length"]
        token = f"{prefix}{secrets.token_urlsafe(length)}"
        return token
    
    def validate_developer_info(self, developer_id: str, email: str) -> Dict[str, str]:
        """Validate developer information"""
        errors = []
        
        # Validate developer ID
        if not developer_id or len(developer_id) < 3:
            errors.append("Developer ID must be at least 3 characters")
        
        if not developer_id.replace('_', '').replace('-', '').isalnum():
            errors.append("Developer ID can only contain letters, numbers, underscore, and hyphen")
        
        # Validate email
        if not email or '@' not in email:
            errors.append("Valid email is required")
        
        # Check allowed domains
        allowed_domains = self.config["security"]["allowed_domains"]
        if allowed_domains:
            domain = email.split('@')[1].lower()
            if domain not in allowed_domains:
                errors.append(f"Email domain not allowed. Allowed: {', '.join(allowed_domains)}")
        
        # Check existing tokens count
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM developer_api_tokens WHERE developer_id = :dev_id AND is_active = true"),
                    {"dev_id": developer_id}
                )
                token_count = result.scalar()
                
                max_tokens = self.config["security"]["max_tokens_per_developer"]
                if token_count >= max_tokens:
                    errors.append(f"Maximum {max_tokens} tokens allowed per developer")
        
        except Exception as e:
            errors.append(f"Database validation error: {e}")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def create_developer_token(self, developer_id: str, email: str, master_password: str, description: str = "Auto-generated") -> Dict:
        """Create new developer token"""
        
        # Validate master password
        if not self.validate_master_password(master_password):
            return {"success": False, "error": "Invalid master password"}
        
        # Validate developer info
        validation = self.validate_developer_info(developer_id, email)
        if not validation["valid"]:
            return {"success": False, "error": "; ".join(validation["errors"])}
        
        try:
            # Generate token
            api_token = self.generate_api_token(developer_id)
            expiry_date = datetime.now() + timedelta(days=self.config["token_settings"]["expiry_days"])
            
            # Insert into database
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO developer_api_tokens 
                        (developer_id, api_token, token_name, expires_at, is_active, created_at)
                        VALUES (:dev_id, :token, :name, :expires, true, NOW())
                    """),
                    {
                        "dev_id": developer_id,
                        "token": api_token,
                        "name": f"{developer_id} - {description}",
                        "expires": expiry_date
                    }
                )
                conn.commit()
            
            # Generate client configuration
            client_config = {
                "api_url": f"{self.config['api_base_url']}/api/multi-dev",
                "api_token": api_token,
                "developer_id": developer_id,
                "sync_interval": 300,
                "generated_at": datetime.now().isoformat(),
                "expires_at": expiry_date.isoformat(),
                "server_info": {
                    "api_base": self.config["api_base_url"],
                    "support_email": self.config["notifications"]["admin_email"]
                }
            }
            
            return {
                "success": True,
                "token_info": {
                    "developer_id": developer_id,
                    "api_token": api_token,
                    "expires_at": expiry_date.isoformat(),
                    "created_at": datetime.now().isoformat()
                },
                "client_config": client_config
            }
            
        except Exception as e:
            return {"success": False, "error": f"Database error: {e}"}
    
    def list_developers(self) -> List[Dict]:
        """List all developers with token info"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT 
                            developer_id,
                            COUNT(*) as token_count,
                            MAX(created_at) as last_token_created,
                            MAX(last_used) as last_activity,
                            SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_tokens
                        FROM developer_api_tokens 
                        GROUP BY developer_id
                        ORDER BY last_token_created DESC
                    """)
                )
                
                developers = []
                for row in result:
                    developers.append({
                        "developer_id": row[0],
                        "token_count": row[1],
                        "last_token_created": row[2].isoformat() if row[2] else None,
                        "last_activity": row[3].isoformat() if row[3] else None,
                        "active_tokens": row[4]
                    })
                
                return developers
                
        except Exception as e:
            print(f"Error listing developers: {e}")
            return []
    
    def revoke_tokens(self, developer_id: str = None, token_id: str = None) -> Dict:
        """Revoke tokens for a developer or specific token"""
        try:
            with self.engine.connect() as conn:
                if token_id:
                    # Revoke specific token
                    result = conn.execute(
                        text("UPDATE developer_api_tokens SET is_active = false WHERE api_token = :token"),
                        {"token": token_id}
                    )
                elif developer_id:
                    # Revoke all tokens for developer
                    result = conn.execute(
                        text("UPDATE developer_api_tokens SET is_active = false WHERE developer_id = :dev_id"),
                        {"dev_id": developer_id}
                    )
                else:
                    return {"success": False, "error": "Either developer_id or token_id required"}
                
                conn.commit()
                
                return {
                    "success": True,
                    "revoked_count": result.rowcount,
                    "message": f"Revoked {result.rowcount} tokens"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Database error: {e}"}
    
    def get_installer_script(self, custom_api_url: str = None) -> str:
        """Generate installer script with current configuration"""
        api_url = custom_api_url or f"{self.config['api_base_url']}/api/multi-dev"
        
        installer_template = f'''#!/bin/bash
# Dynamic Activity Tracker Installer
# Generated at: {datetime.now().isoformat()}

set -e

API_URL="{api_url}"
INSTALL_DIR="$HOME/.timesheet-tracker"

echo "🚀 Installing Timesheet Activity Tracker..."

# [Rest of installer script with dynamic API_URL]
# This would contain the full installer script from before
# but with the API_URL dynamically set

echo "Configuration:"
echo "  API URL: $API_URL"
echo "  Install Directory: $INSTALL_DIR"

# ... rest of installation logic ...
'''
        return installer_template

def main():
    """CLI interface for token management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic Token Manager')
    parser.add_argument('action', choices=[
        'setup', 'add-master-password', 'create-token', 'list-developers', 
        'revoke-tokens', 'generate-installer'
    ])
    parser.add_argument('--developer-id', help='Developer ID')
    parser.add_argument('--email', help='Developer email')
    parser.add_argument('--master-password', help='Master password')
    parser.add_argument('--description', help='Token description')
    parser.add_argument('--config', default='token_manager_config.json', help='Config file path')
    
    args = parser.parse_args()
    
    manager = DynamicTokenManager(args.config)
    
    if args.action == 'setup':
        print("🔧 Token Manager Setup")
        print("=" * 30)
        
        # Setup database URL
        db_url = input(f"Database URL [{manager.config['database_url']}]: ").strip()
        if db_url:
            manager.config['database_url'] = db_url
        
        # Setup API base URL
        api_url = input(f"API Base URL [{manager.config['api_base_url']}]: ").strip()
        if api_url:
            manager.config['api_base_url'] = api_url
        
        # Setup admin email
        admin_email = input("Admin email (optional): ").strip()
        if admin_email:
            manager.config['notifications']['admin_email'] = admin_email
        
        # Setup allowed domains
        domains = input("Allowed email domains (comma-separated, empty for all): ").strip()
        if domains:
            manager.config['security']['allowed_domains'] = [d.strip() for d in domains.split(',')]
        
        manager.save_config(manager.config)
        
        # Generate first master password
        password = manager.add_master_password("Initial setup")
        
        print(f"\n✅ Setup complete!")
        print(f"📋 Share this master password with your team: {password}")
    
    elif args.action == 'add-master-password':
        description = args.description or input("Description for this password: ")
        password = manager.add_master_password(description)
        print(f"New master password: {password}")
    
    elif args.action == 'create-token':
        developer_id = args.developer_id or input("Developer ID: ")
        email = args.email or input("Email: ")
        master_password = args.master_password or input("Master password: ")
        description = args.description or "CLI generated"
        
        result = manager.create_developer_token(developer_id, email, master_password, description)
        
        if result["success"]:
            print("✅ Token created successfully!")
            print(f"Developer: {result['token_info']['developer_id']}")
            print(f"Token: {result['token_info']['api_token']}")
            print(f"Expires: {result['token_info']['expires_at']}")
            
            # Save config file
            config_file = f"config_{developer_id}.json"
            with open(config_file, 'w') as f:
                json.dump(result['client_config'], f, indent=2)
            print(f"📁 Config saved to: {config_file}")
        else:
            print(f"❌ Error: {result['error']}")
    
    elif args.action == 'list-developers':
        developers = manager.list_developers()
        
        if not developers:
            print("No developers found")
            return
        
        print("👥 Developers:")
        print("-" * 80)
        for dev in developers:
            print(f"ID: {dev['developer_id']}")
            print(f"  Active Tokens: {dev['active_tokens']}/{dev['token_count']}")
            print(f"  Last Token: {dev['last_token_created']}")
            print(f"  Last Activity: {dev['last_activity'] or 'Never'}")
            print()
    
    elif args.action == 'revoke-tokens':
        developer_id = args.developer_id or input("Developer ID to revoke (or press Enter for all): ")
        
        if developer_id:
            result = manager.revoke_tokens(developer_id=developer_id)
        else:
            confirm = input("Revoke ALL tokens? (yes/no): ")
            if confirm.lower() == 'yes':
                # This would need additional implementation
                print("Bulk revocation not implemented yet")
                return
            else:
                print("Cancelled")
                return
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    elif args.action == 'generate-installer':
        script = manager.get_installer_script()
        
        with open('install_timesheet_tracker.sh', 'w') as f:
            f.write(script)
        
        print("✅ Installer script generated: install_timesheet_tracker.sh")

if __name__ == "__main__":
    main()