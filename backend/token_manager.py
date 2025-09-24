#!/usr/bin/env python3
"""
Enhanced Token Generator for Developer Registration
"""

import os
import sys
import secrets
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment
load_dotenv('.env.local')
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:asdf1234@localhost:5432/timesheet")

class TokenManager:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.ensure_tables_exist()
    
    def ensure_tables_exist(self):
        """Create token table if it doesn't exist"""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS developer_api_tokens (
                    id SERIAL PRIMARY KEY,
                    developer_id VARCHAR NOT NULL,
                    api_token VARCHAR UNIQUE NOT NULL,
                    token_name VARCHAR DEFAULT 'Default Token',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            conn.commit()
    
    def create_token(self, developer_name: str, token_name: str = None) -> str:
        """Create a new access token for a developer"""
        if not developer_name or not developer_name.strip():
            raise ValueError("Developer name is required!")
        
        developer_name = developer_name.strip()
        token_name = token_name or f"{developer_name} Token"
        
        # Generate secure token
        token = f"AWToken_{secrets.token_urlsafe(32)}"
        
        with self.engine.connect() as conn:
            # Check if developer already has a token
            existing = conn.execute(text("""
                SELECT api_token FROM developer_api_tokens 
                WHERE developer_id = :dev_id AND is_active = true
            """), {"dev_id": developer_name}).fetchone()
            
            if existing:
                print(f"⚠️  Developer '{developer_name}' already has an active token:")
                print(f"   {existing[0]}")
                
                overwrite = input("Create new token anyway? (y/N): ").lower().strip()
                if overwrite != 'y':
                    return existing[0]
                
                # Deactivate old token
                conn.execute(text("""
                    UPDATE developer_api_tokens 
                    SET is_active = false 
                    WHERE developer_id = :dev_id
                """), {"dev_id": developer_name})
            
            # Insert new token
            conn.execute(text("""
                INSERT INTO developer_api_tokens (developer_id, api_token, token_name)
                VALUES (:dev_id, :token, :name)
            """), {
                "dev_id": developer_name,
                "token": token,
                "name": token_name
            })
            
            conn.commit()
            
        return token
    
    def list_tokens(self, show_inactive=False):
        """List all tokens"""
        with self.engine.connect() as conn:
            query = """
                SELECT developer_id, api_token, token_name, created_at, is_active
                FROM developer_api_tokens 
                WHERE is_active = true OR :show_inactive = true
                ORDER BY created_at DESC
            """
            
            result = conn.execute(text(query), {"show_inactive": show_inactive})
            tokens = result.fetchall()
            
            if not tokens:
                print("📝 No tokens found.")
                return []
            
            return tokens
    
    def delete_token(self, developer_name: str):
        """Deactivate a token"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE developer_api_tokens 
                SET is_active = false 
                WHERE developer_id = :dev_id AND is_active = true
            """), {"dev_id": developer_name})
            
            conn.commit()
            
            if result.rowcount > 0:
                print(f"✅ Token deactivated for {developer_name}")
            else:
                print(f"❌ No active token found for {developer_name}")

def interactive_create_token():
    """Interactive token creation"""
    print("\n🔑 Create New Access Token")
    print("=" * 40)
    
    developer_name = input("Enter developer name: ").strip()
    if not developer_name:
        print("❌ Developer name is required!")
        return
    
    token_name = input(f"Token name (default: '{developer_name} Token'): ").strip()
    
    try:
        manager = TokenManager()
        token = manager.create_token(developer_name, token_name)
        
        print(f"\n🎉 Token created successfully!")
        print("=" * 50)
        print(f"Developer: {developer_name}")
        print(f"Token: {token}")
        print("=" * 50)
        print(f"\n📋 Give this token to {developer_name}:")
        print(f"   They should visit: http://localhost:8000/register-developer")
        print(f"   And paste this token: {token}")
        
    except Exception as e:
        print(f"❌ Error creating token: {e}")

def list_all_tokens():
    """List all tokens in a nice format"""
    try:
        manager = TokenManager()
        tokens = manager.list_tokens(show_inactive=False)
        
        if not tokens:
            print("📝 No active tokens found.")
            return
        
        print(f"\n🔑 Active Access Tokens ({len(tokens)} total)")
        print("=" * 80)
        
        for i, token in enumerate(tokens, 1):
            developer_id = token[0]
            api_token = token[1]
            token_name = token[2]
            created_at = token[3]
            is_active = token[4]
            
            status_icon = "✅" if is_active else "❌"
            
            print(f"{i}. {status_icon} {developer_id}")
            print(f"   Token: {api_token}")
            print(f"   Name: {token_name}")
            print(f"   Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 80)
    
    except Exception as e:
        print(f"❌ Error listing tokens: {e}")

def bulk_create_tokens():
    """Create tokens for multiple developers at once"""
    print("\n🔄 Bulk Token Creation")
    print("=" * 40)
    print("Enter developer names (one per line, empty line to finish):")
    
    developers = []
    while True:
        name = input(f"Developer {len(developers) + 1}: ").strip()
        if not name:
            break
        developers.append(name)
    
    if not developers:
        print("❌ No developers entered!")
        return
    
    print(f"\n📝 Creating tokens for {len(developers)} developers...")
    
    try:
        manager = TokenManager()
        tokens = {}
        
        for dev_name in developers:
            token = manager.create_token(dev_name)
            tokens[dev_name] = token
            print(f"✅ {dev_name}: {token}")
        
        print(f"\n🎉 Created {len(tokens)} tokens successfully!")
        
        # Save to file for easy sharing
        filename = f"tokens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write("Developer Access Tokens\n")
            f.write("=" * 50 + "\n\n")
            for dev_name, token in tokens.items():
                f.write(f"Developer: {dev_name}\n")
                f.write(f"Token: {token}\n")
                f.write(f"Registration URL: http://localhost:8000/register-developer\n")
                f.write("-" * 50 + "\n\n")
        
        print(f"📄 Tokens saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error creating tokens: {e}")

def main():
    parser = argparse.ArgumentParser(description='Developer Token Manager')
    parser.add_argument('action', nargs='?', choices=[
        'create', 'list', 'bulk', 'interactive'
    ], help='Action to perform')
    parser.add_argument('--name', help='Developer name (for create action)')
    parser.add_argument('--token-name', help='Custom token name')
    
    args = parser.parse_args()
    
    if not args.action:
        # Interactive menu
        print("\n🔑 Developer Token Manager")
        print("=" * 40)
        print("1. Create single token")
        print("2. List all tokens") 
        print("3. Bulk create tokens")
        print("4. Exit")
        
        while True:
            try:
                choice = input("\nSelect option (1-4): ").strip()
                
                if choice == "1":
                    interactive_create_token()
                elif choice == "2":
                    list_all_tokens()
                elif choice == "3":
                    bulk_create_tokens()
                elif choice == "4":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-4.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
    
    else:
        # Command line mode
        try:
            manager = TokenManager()
            
            if args.action == 'create':
                if not args.name:
                    print("❌ --name is required for create action")
                    return
                
                token = manager.create_token(args.name, args.token_name)
                print(f"✅ Token created for {args.name}: {token}")
                
            elif args.action == 'list':
                list_all_tokens()
                
            elif args.action == 'bulk':
                bulk_create_tokens()
                
            elif args.action == 'interactive':
                interactive_create_token()
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
