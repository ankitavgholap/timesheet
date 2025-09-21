#!/usr/bin/env python3
"""
Bulk Developer Registration Script
Registers multiple developers and generates their configurations automatically
"""

import requests
import json
import csv
import os
import sys
import secrets
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class DeveloperRegistrationManager:
    def __init__(self, server_url: str, admin_token: str):
        self.server_url = server_url.rstrip('/')
        self.admin_token = admin_token
        self.api_base = f"{self.server_url}/api/v1"
        
        self.headers = {
            "Admin-Token": self.admin_token,
            "Content-Type": "application/json"
        }
    
    def generate_developer_id(self, name: str, email: Optional[str] = None) -> str:
        """Generate unique developer ID from name and email"""
        # Clean and normalize name
        clean_name = name.lower().strip()
        clean_name = ''.join(c if c.isalnum() or c.isspace() else '' for c in clean_name)
        clean_name = '_'.join(clean_name.split())
        
        # Add email hash for uniqueness if provided
        if email:
            email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:4]
            developer_id = f"{clean_name}_{email_hash}"
        else:
            year = datetime.now().year
            developer_id = f"{clean_name}_{year}"
        
        return developer_id
    
    def test_server_connection(self) -> bool:
        """Test connection to server and admin token validity"""
        try:
            response = requests.get(
                f"{self.api_base}/developers",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Server connection and admin token verified")
                return True
            elif response.status_code == 401:
                print("❌ Invalid admin token")
                return False
            else:
                print(f"❌ Server error: HTTP {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def register_developer(self, name: str, email: Optional[str] = None) -> Optional[Dict]:
        """Register a single developer"""
        developer_data = {
            "name": name.strip(),
            "email": email.strip() if email else None,
            "active": True
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/register-developer",
                headers=self.headers,
                json=developer_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Registered: {name} → {result['developer_id']}")
                return result
            elif response.status_code == 400:
                error = response.json()
                if "already registered" in error.get('detail', ''):
                    print(f"⚠️  Already exists: {name}")
                    return None
                else:
                    print(f"❌ Registration error for {name}: {error.get('detail')}")
                    return None
            else:
                print(f"❌ Server error for {name}: HTTP {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Network error registering {name}: {e}")
            return None
    
    def register_from_list(self, developers: List[Dict[str, str]]) -> List[Dict]:
        """Register multiple developers from list"""
        successful_registrations = []
        
        print(f"\n🚀 Registering {len(developers)} developers...")
        print("-" * 50)
        
        for i, dev in enumerate(developers, 1):
            name = dev.get('name', '').strip()
            email = dev.get('email', '').strip() or None
            
            if not name:
                print(f"❌ Skipping entry {i}: No name provided")
                continue
            
            print(f"[{i}/{len(developers)}] {name}", end=" ... ")
            
            result = self.register_developer(name, email)
            if result:
                successful_registrations.append(result)
        
        return successful_registrations
    
    def register_from_csv(self, csv_file: str) -> List[Dict]:
        """Register developers from CSV file"""
        if not Path(csv_file).exists():
            print(f"❌ CSV file not found: {csv_file}")
            return []
        
        developers = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 2):  # Start from row 2 (after header)
                    name = row.get('name', '').strip()
                    email = row.get('email', '').strip()
                    
                    if not name:
                        print(f"⚠️  Skipping row {row_num}: No name provided")
                        continue
                    
                    developers.append({
                        'name': name,
                        'email': email if email else None
                    })
            
            print(f"📄 Loaded {len(developers)} developers from CSV")
            
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return []
        
        return self.register_from_list(developers)
    
    def interactive_registration(self) -> List[Dict]:
        """Interactive developer registration"""
        developers = []
        successful_registrations = []
        
        print("\n👥 Interactive Developer Registration")
        print("Enter developer details (press Enter with empty name to finish)")
        print("-" * 60)
        
        while True:
            name = input("\nDeveloper name: ").strip()
            if not name:
                break
            
            email = input("Email (optional): ").strip() or None
            
            developers.append({'name': name, 'email': email})
        
        if developers:
            successful_registrations = self.register_from_list(developers)
        
        return successful_registrations
    
    def generate_all_configs(self, output_dir: str = "./developer_configs") -> bool:
        """Generate ActivityWatch configs for all registered developers"""
        try:
            # Get all registered developers
            response = requests.get(
                f"{self.api_base}/developers",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Cannot fetch developers: HTTP {response.status_code}")
                return False
            
            developers_data = response.json()
            developers = developers_data.get('developers', [])
            
            if not developers:
                print("❌ No developers registered yet")
                return False
            
            print(f"\n🔧 Generating configs for {len(developers)} developers...")
            
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            generated_count = 0
            
            for developer in developers:
                developer_id = developer['developer_id']
                
                try:
                    # Get config for this developer
                    config_response = requests.get(
                        f"{self.api_base}/activitywatch/config/{developer_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if config_response.status_code == 200:
                        config_data = config_response.json()
                        
                        # Save config file
                        config_file = Path(output_dir) / f"{developer_id}_config.toml"
                        with open(config_file, 'w', encoding='utf-8') as f:
                            f.write(config_data['config_toml'])
                        
                        # Save instructions
                        instructions_file = Path(output_dir) / f"{developer_id}_instructions.txt"
                        instructions_content = f"""
Setup Instructions for {config_data['developer_name']}
{'=' * 50}

1. Find your ActivityWatch config directory:
   Windows: %APPDATA%\\activitywatch\\aw-server\\config.toml
   Linux:   ~/.config/activitywatch/aw-server/config.toml
   macOS:   ~/Library/Application Support/activitywatch/aw-server/config.toml

2. Replace the config.toml file with the contents from:
   {config_file.name}

3. Restart ActivityWatch completely:
   - Close ActivityWatch
   - Wait 10 seconds  
   - Start ActivityWatch again

4. Your data will automatically sync every 30 minutes

Your Details:
- Developer ID: {developer_id}
- Name: {config_data['developer_name']}
- Team Dashboard: {self.server_url}/team

Troubleshooting:
- Check ActivityWatch logs for webhook messages
- Verify internet connection to: {self.server_url}
- Contact admin if issues persist
"""
                        
                        with open(instructions_file, 'w', encoding='utf-8') as f:
                            f.write(instructions_content.strip())
                        
                        print(f"✅ Generated config for {config_data['developer_name']}")
                        generated_count += 1
                        
                    else:
                        print(f"❌ Failed to get config for {developer_id}")
                        
                except Exception as e:
                    print(f"❌ Error generating config for {developer_id}: {e}")
            
            # Create master README
            readme_file = Path(output_dir) / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"""# ActivityWatch Team Configuration Files

## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
## Server: {self.server_url}
## Developers: {generated_count}

## Distribution Instructions

Each developer needs:
1. Their specific `*_config.toml` file
2. Their `*_instructions.txt` file  
3. 2 minutes to replace one file and restart ActivityWatch

## Files Generated
""")
                
                for developer in developers:
                    if Path(output_dir / f"{developer['developer_id']}_config.toml").exists():
                        f.write(f"""
### {developer['name']} ({developer['developer_id']})
- Config: `{developer['developer_id']}_config.toml`
- Instructions: `{developer['developer_id']}_instructions.txt`
""")
                
                f.write(f"""
## Support
- Team Dashboard: {self.server_url}/team
- Contact your system administrator for issues
""")
            
            print(f"\n✅ Generated {generated_count} configuration packages")
            print(f"📁 Output directory: {Path(output_dir).absolute()}")
            print(f"📖 Distribution guide: {readme_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating configs: {e}")
            return False

def create_sample_csv():
    """Create a sample CSV file for bulk registration"""
    sample_csv = """name,email
John Doe,john@company.com
Alice Smith,alice@company.com
Bob Johnson,bob@company.com
Sarah Wilson,sarah@company.com
Mike Davis,mike@company.com"""
    
    with open('sample_developers.csv', 'w', encoding='utf-8') as f:
        f.write(sample_csv)
    
    print("📄 Created sample_developers.csv")
    print("Edit this file with your actual developer information")

def main():
    print("👥 Bulk Developer Registration & Config Generator")
    print("=" * 55)
    
    # Get configuration
    server_url = input("Server URL (e.g., https://timesheet.company.com): ").strip()
    if not server_url:
        print("❌ Server URL is required")
        sys.exit(1)
    
    admin_token = input("Admin Token: ").strip()
    if not admin_token:
        print("❌ Admin token is required")
        sys.exit(1)
    
    # Initialize manager
    manager = DeveloperRegistrationManager(server_url, admin_token)
    
    # Test connection
    print("\n🔍 Testing server connection...")
    if not manager.test_server_connection():
        sys.exit(1)
    
    # Registration options
    print("\n📋 Registration Options:")
    print("1. Interactive registration (enter developers manually)")
    print("2. CSV file registration (bulk import)")
    print("3. Create sample CSV file")
    print("4. Skip registration (just generate configs for existing developers)")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    successful_registrations = []
    
    if choice == "1":
        successful_registrations = manager.interactive_registration()
    elif choice == "2":
        csv_file = input("CSV file path (default: developers.csv): ").strip()
        if not csv_file:
            csv_file = "developers.csv"
        successful_registrations = manager.register_from_csv(csv_file)
    elif choice == "3":
        create_sample_csv()
        print("\nEdit the CSV file and run this script again with option 2")
        sys.exit(0)
    elif choice == "4":
        print("Skipping registration...")
    else:
        print("❌ Invalid option")
        sys.exit(1)
    
    # Generate configurations
    if choice != "3":
        output_dir = input("\nOutput directory (default: ./developer_configs): ").strip()
        if not output_dir:
            output_dir = "./developer_configs"
        
        if manager.generate_all_configs(output_dir):
            print("\n🎉 Success! Configuration files generated")
            print(f"📧 Distribute files from: {Path(output_dir).absolute()}")
            print("📊 Team dashboard will show data after developers set up ActivityWatch")
        else:
            print("\n❌ Failed to generate configuration files")
            sys.exit(1)

if __name__ == "__main__":
    main()
