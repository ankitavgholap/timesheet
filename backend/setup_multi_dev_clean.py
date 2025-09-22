import os
import sys
import secrets
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def main():
    print("Setting up multi-developer tracking...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Creating database tables...")
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_activity_records_developer_id ON activity_records(developer_id);
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS activity_sessions (
                id SERIAL PRIMARY KEY,
                developer_id VARCHAR NOT NULL,
                session_start TIMESTAMP WITH TIME ZONE NOT NULL,
                session_end TIMESTAMP WITH TIME ZONE,
                total_active_time INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
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
    
    print("Database setup complete!")
    print("Next steps:")
    print("1. Restart your backend: python main.py")
    print("2. Create tokens: python setup_multi_dev.py create-token")

def create_token():
    developer_name = input("Enter developer name: ").strip()
    if not developer_name:
        print("Developer name is required!")
        return
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            token = f"AWToken_{secrets.token_urlsafe(32)}"
            
            conn.execute(text("""
                INSERT INTO developer_api_tokens (developer_id, api_token, token_name)
                VALUES (:dev_id, :token, :name)
            """), {
                "dev_id": developer_name,
                "token": token,
                "name": f"{developer_name} Token"
            })
            
            conn.commit()
            
            print(f"Token created for {developer_name}:")
            print(f"   {token}")
    
    except Exception as e:
        print(f"Error creating token: {e}")

def list_tokens():
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT developer_id, api_token, token_name, created_at, is_active
                FROM developer_api_tokens 
                ORDER BY created_at DESC
            """))
            
            tokens = result.fetchall()
            
            if not tokens:
                print("No tokens found.")
                return
            
            print("Existing API Tokens:")
            print("=" * 80)
            
            for token in tokens:
                status = "Active" if token[4] else "Inactive"
                print(f"Developer: {token[0]}")
                print(f"Token: {token[1]}")
                print(f"Status: {status}")
                print("-" * 80)
    
    except Exception as e:
        print(f"Error listing tokens: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create-token":
            create_token()
        elif command == "list-tokens":
            list_tokens()
        else:
            print("Usage:")
            print("  python setup_multi_dev.py              - Set up database tables")
            print("  python setup_multi_dev.py create-token - Create token")
            print("  python setup_multi_dev.py list-tokens  - Show tokens")
    else:
        main()
