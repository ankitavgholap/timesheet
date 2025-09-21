#!/usr/bin/env python3
"""
Integration Script - Add ActivityWatch Webhook Support
This script helps integrate the ActivityWatch webhook endpoints into your existing application
"""

import os
import sys
from pathlib import Path

def update_main_py():
    """Update main.py to include ActivityWatch webhook endpoints"""
    main_py_path = Path("backend/main.py")
    
    if not main_py_path.exists():
        print(f"❌ {main_py_path} not found")
        return False
    
    # Read current main.py
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already integrated
    if "activitywatch_webhook" in content:
        print("✅ ActivityWatch webhook already integrated in main.py")
        return True
    
    # Add import and router
    import_line = "from activitywatch_webhook import router as aw_webhook_router\n"
    router_line = 'app.include_router(aw_webhook_router, prefix="/api/v1", tags=["activitywatch"])\n'
    
    # Find where to add import (after other imports)
    import_insertion_point = content.find("models.Base.metadata.create_all(bind=engine)")
    if import_insertion_point == -1:
        print("❌ Could not find insertion point in main.py")
        return False
    
    # Find where to add router (after app creation)
    router_insertion_point = content.find('app.add_middleware(')
    if router_insertion_point == -1:
        router_insertion_point = content.find('oauth2_scheme = OAuth2PasswordBearer')
    
    if router_insertion_point == -1:
        print("❌ Could not find router insertion point in main.py")
        return False
    
    # Insert import
    content = content[:import_insertion_point] + import_line + content[import_insertion_point:]
    
    # Adjust router insertion point due to added content
    router_insertion_point = content.find('oauth2_scheme = OAuth2PasswordBearer')
    router_insertion_point = content.find('\n', router_insertion_point) + 1
    
    # Insert router
    content = content[:router_insertion_point] + router_line + '\n' + content[router_insertion_point:]
    
    # Write updated content
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated main.py with ActivityWatch webhook integration")
    return True

def update_models_py():
    """Update models.py to include Developer model if not already present"""
    models_py_path = Path("backend/models.py")
    
    if not models_py_path.exists():
        print(f"❌ {models_py_path} not found")
        return False
    
    # Read current models.py
    with open(models_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if Developer model already exists
    if "class Developer(Base):" in content:
        print("✅ Developer model already exists in models.py")
        return True
    
    # Read developer model addition
    dev_model_path = Path("backend/developer_model_addition.py")
    if not dev_model_path.exists():
        print("❌ developer_model_addition.py not found")
        return False
    
    with open(dev_model_path, 'r', encoding='utf-8') as f:
        dev_model_content = f.read()
    
    # Extract the Developer model class
    start_marker = "class Developer(Base):"
    end_marker = "activities = relationship"
    
    start_idx = dev_model_content.find(start_marker)
    end_idx = dev_model_content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("❌ Could not extract Developer model")
        return False
    
    # Get the full Developer model
    end_idx = dev_model_content.find('\n', end_idx + len(end_marker)) + 1
    developer_model = dev_model_content[start_idx:end_idx]
    
    # Add to models.py
    content += "\n\n# Developer model for multi-developer support\n" + developer_model
    
    # Also add developer_id field to ActivityRecord if not present
    if "developer_id = Column" not in content and "class ActivityRecord(Base):" in content:
        # Find ActivityRecord class and add developer fields
        ar_class_start = content.find("class ActivityRecord(Base):")
        ar_class_end = content.find("user = relationship", ar_class_start)
        
        if ar_class_start != -1 and ar_class_end != -1:
            # Insert developer fields before user relationship
            developer_fields = """    
    # Multi-developer support
    developer_id = Column(String, ForeignKey("developers.developer_id"), nullable=True)
    developer = relationship("Developer", back_populates="activities")
    
"""
            content = content[:ar_class_end] + developer_fields + content[ar_class_end:]
            print("✅ Added developer fields to ActivityRecord")
    
    # Write updated content
    with open(models_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated models.py with Developer model")
    return True

def check_dependencies():
    """Check if all required files exist"""
    required_files = [
        "backend/activitywatch_webhook.py",
        "backend/multi_developer_api.py", 
        "database_migration.py",
        "generate_aw_configs.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    return True

def main():
    print("🔧 ActivityWatch Integration Script")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the timesheet project root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot proceed without required files")
        sys.exit(1)
    
    print("\n📝 Integrating ActivityWatch webhook support...")
    
    # Update main.py
    if not update_main_py():
        print("❌ Failed to update main.py")
        sys.exit(1)
    
    # Update models.py
    if not update_models_py():
        print("❌ Failed to update models.py")
        sys.exit(1)
    
    print("\n🗃️ Running database migration...")
    
    # Run database migration
    try:
        import subprocess
        result = subprocess.run([sys.executable, "database_migration.py"], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Database migration completed successfully")
        else:
            print(f"⚠️  Database migration had issues:\n{result.stdout}\n{result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not run database migration automatically: {e}")
        print("Please run: python database_migration.py")
    
    print("\n" + "=" * 40)
    print("🎉 Integration Complete!")
    print("\nNext Steps:")
    print("1. Restart your backend server (PM2 restart or manual)")
    print("2. Register developers: python -c \"import requests; print('Use /api/v1/register-developer')\"")
    print("3. Generate configs: python generate_aw_configs.py")
    print("4. Distribute config files to developers")
    print("5. Check team dashboard after developers set up")
    
    print(f"\n📋 New API Endpoints Available:")
    print("- POST /api/v1/activitywatch/webhook (receives AW data)")
    print("- GET  /api/v1/activitywatch/config/{developer_id} (generates config)")
    print("- POST /api/v1/register-developer (registers new developer)")
    print("- GET  /api/v1/developers (lists all developers)")
    print("- GET  /api/v1/team-dashboard (team productivity view)")

if __name__ == "__main__":
    main()
