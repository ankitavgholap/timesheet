#!/usr/bin/env python3
"""
ActivityWatch TOML Configuration Generator
Generates config.toml files for each developer with webhook integration
"""

import requests
import json
import os
import sys
from pathlib import Path

def get_developer_config(server_url, admin_token, developer_id):
    """Get ActivityWatch configuration for a developer from server"""
    try:
        response = requests.get(
            f"{server_url}/api/v1/activitywatch/config/{developer_id}",
            headers={"Admin-Token": admin_token},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error getting config for {developer_id}: {e}")
        return None

def save_config_file(config_data, output_dir):
    """Save TOML configuration file"""
    developer_id = config_data['developer_id']
    developer_name = config_data['developer_name']
    config_toml = config_data['config_toml']
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save TOML file
    config_file = Path(output_dir) / f"{developer_id}_config.toml"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_toml)
    
    # Save installation instructions
    instructions_file = Path(output_dir) / f"{developer_id}_instructions.txt"
    instructions = f"""
ActivityWatch Configuration Setup for {developer_name}
=====================================================

1. Locate your ActivityWatch configuration directory:
   - Windows: %APPDATA%\\activitywatch\\aw-server\\config.toml
   - Linux: ~/.config/activitywatch/aw-server/config.toml
   - macOS: ~/Library/Application Support/activitywatch/aw-server/config.toml

2. Replace or create the config.toml file with the contents from {developer_id}_config.toml

3. Restart ActivityWatch completely:
   - Close ActivityWatch
   - Wait 10 seconds
   - Start ActivityWatch again

4. Verify the integration is working:
   - Check ActivityWatch logs for webhook messages
   - After 30 minutes of activity, check the team dashboard
   - Look for your name in the developer list

Troubleshooting:
- If webhook fails, check your internet connection
- Verify the server URL is accessible
- Check ActivityWatch logs in the ActivityWatch installation directory
- Contact your system administrator if issues persist

Your Developer ID: {developer_id}
Team Dashboard: {config_data.get('server_url', 'https://your-server.com')}/team
"""
    
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    return config_file, instructions_file

def main():
    print("🔧 ActivityWatch Configuration Generator")
    print("=" * 50)
    
    # Configuration
    server_url = input("Enter your timesheet server URL (e.g., https://timesheet.company.com): ").strip()
    if not server_url:
        print("❌ Server URL is required")
        sys.exit(1)
    
    admin_token = input("Enter admin token: ").strip()
    if not admin_token:
        print("❌ Admin token is required")
        sys.exit(1)
    
    output_dir = input("Enter output directory (default: ./aw_configs): ").strip()
    if not output_dir:
        output_dir = "./aw_configs"
    
    # Get list of developers
    print("\n📋 Fetching developer list...")
    try:
        response = requests.get(
            f"{server_url}/api/v1/developers",
            headers={"Admin-Token": admin_token},
            timeout=10
        )
        response.raise_for_status()
        developers_data = response.json()
        developers = developers_data.get('developers', [])
    except requests.RequestException as e:
        print(f"❌ Error fetching developers: {e}")
        sys.exit(1)
    
    if not developers:
        print("❌ No developers found. Please register developers first.")
        sys.exit(1)
    
    print(f"✅ Found {len(developers)} developers")
    
    # Generate configurations
    generated_configs = []
    
    for developer in developers:
        developer_id = developer['developer_id']
        developer_name = developer['name']
        
        print(f"\n🔨 Generating config for {developer_name} ({developer_id})")
        
        config_data = get_developer_config(server_url, admin_token, developer_id)
        if not config_data:
            print(f"⚠️  Skipping {developer_id}")
            continue
        
        try:
            config_file, instructions_file = save_config_file(config_data, output_dir)
            generated_configs.append({
                'developer_id': developer_id,
                'developer_name': developer_name,
                'config_file': config_file,
                'instructions_file': instructions_file
            })
            print(f"✅ Generated configuration files for {developer_name}")
        except Exception as e:
            print(f"❌ Error saving config for {developer_id}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Configuration Generation Complete!")
    print(f"📁 Output directory: {Path(output_dir).absolute()}")
    print(f"✅ Generated {len(generated_configs)} configurations")
    
    print("\n📋 Generated Files:")
    for config in generated_configs:
        print(f"  👤 {config['developer_name']}:")
        print(f"     - Configuration: {config['config_file']}")
        print(f"     - Instructions: {config['instructions_file']}")
    
    print("\n📧 Distribution Instructions:")
    print("1. Send each developer their specific config.toml and instructions")
    print("2. Developers need to replace their ActivityWatch config.toml")
    print("3. Developers must restart ActivityWatch completely")
    print("4. Data will automatically sync every 30 minutes")
    print("5. Check the team dashboard after developers are set up")
    
    # Create a master distribution README
    readme_file = Path(output_dir) / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"""# ActivityWatch Team Integration Setup

## Overview
This directory contains ActivityWatch configuration files for team members to automatically sync their activity data to the central timesheet system.

## Server Information
- **Server URL**: {server_url}
- **Team Dashboard**: {server_url}/team
- **Generated**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Developer Configurations
""")
        for config in generated_configs:
            f.write(f"""
### {config['developer_name']} ({config['developer_id']})
- **Configuration File**: `{config['config_file'].name}`
- **Instructions**: `{config['instructions_file'].name}`
""")
        
        f.write("""
## Setup Process
1. Each developer receives their specific config files
2. Follow the instructions in their individual instruction file
3. Replace ActivityWatch config.toml with the provided configuration
4. Restart ActivityWatch completely
5. Verify integration in team dashboard after 30 minutes

## Support
If developers have issues:
1. Check ActivityWatch logs
2. Verify internet connection to server
3. Ensure ActivityWatch is completely restarted
4. Contact system administrator with error messages
""")
    
    print(f"\n📖 Created master README: {readme_file}")
    print("\n🚀 Ready to distribute to team members!")

if __name__ == "__main__":
    main()
