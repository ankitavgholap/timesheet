# backend/check_database_structure.py
import psycopg2
from database import DATABASE_URL
from sqlalchemy import create_engine, text

def check_activity_records_table():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Get table structure
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'activity_records'
                ORDER BY ordinal_position;
            """))
            
            print("=== Current activity_records table structure ===")
            for row in result:
                print(f"{row[0]}: {row[1]} (nullable: {row[2]})")
            
            # Check for data
            result = conn.execute(text("SELECT COUNT(*) FROM activity_records;"))
            count = result.scalar()
            print(f"\nTotal records: {count}")
            
            # Check developer_id values
            result = conn.execute(text("""
                SELECT DISTINCT developer_id, COUNT(*) 
                FROM activity_records 
                WHERE developer_id IS NOT NULL 
                GROUP BY developer_id 
                LIMIT 10;
            """))
            
            print("\nExisting developer_id values:")
            for row in result:
                print(f"  {row[0]}: {row[1]} records")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_activity_records_table()
