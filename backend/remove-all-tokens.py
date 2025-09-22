import os
import sys
import secrets
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def setup_database():
    print("Setting up multi-developer tracking...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("Creating database tables...")
        
        # Add index
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_records_developer_id ON activity_records(developer_id);"))
        
        # Create sessions table
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
        
        # Create tokens table
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
    print("1. Restart backend: python main.py")
    print("2. Create tokens: python setup_multi_dev.py create-token")

def create_token():
    name = input("Enter developer name: ").strip()
    if not name:
        print("Name required!")
        return
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            token = f"AWToken_{secrets.token_urlsafe(32)}"
            
            conn.execute(text("""
                INSERT INTO developer_api_tokens (developer_id, api_token, token_name)
                VALUES (:dev_id, :token, :name)
            """), {"dev_id": name, "token": token, "name": f"{name} Token"})
            
            conn.commit()
            print(f"Token for {name}: {token}")
    
    except Exception as e:
        print(f"Error: {e}")

def list_tokens():
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT developer_id, api_token FROM developer_api_tokens ORDER BY created_at DESC"))
            tokens = result.fetchall()
            
            if not tokens:
                print("No tokens found.")
                return
            
            print("API Tokens:")
            for token in tokens:
                print(f"Developer: {token[0]}")
                print(f"Token: {token[1]}")
                print("-" * 50)
    
    except Exception as e:
        print(f"Error: {e}")

def remove_all_tokens():
    confirm = input("Are you sure you want to delete ALL tokens? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM developer_api_tokens"))
            conn.commit()
            print(f"Deleted {result.rowcount} tokens.")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "create-token":
            create_token()
        elif cmd == "list-tokens":
            list_tokens()
        elif cmd == "remove-all-tokens":
            remove_all_tokens()
        else:
            print("Usage:")
            print("  python setup_multi_dev.py                 - Set up database")
            print("  python setup_multi_dev.py create-token    - Create token")
            print("  python setup_multi_dev.py list-tokens     - Show tokens")
            print("  python setup_multi_dev.py remove-all-tokens - Delete all tokens")
    else:
        setup_database()