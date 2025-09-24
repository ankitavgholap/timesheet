# backend/test_env.py
import os
from dotenv import load_dotenv

print("=== Testing Environment Loading ===")

# Load environment files
load_dotenv('.env.local', override=True)
load_dotenv('.env.production', override=False)
load_dotenv()

# Print all relevant environment variables
env_vars = [
    'ENVIRONMENT',
    'DATABASE_URL', 
    'LOCAL_DEVELOPER_NAME',
    'SECRET_KEY',
    'ACTIVITYWATCH_HOST'
]

for var in env_vars:
    value = os.getenv(var)
    print(f"{var}: {value}")

print("\n=== File Check ===")
import os.path
files_to_check = ['.env', '.env.local', '.env.production']
for file in files_to_check:
    exists = os.path.exists(file)
    print(f"{file}: {'EXISTS' if exists else 'NOT FOUND'}")

if os.path.exists('.env.local'):
    print("\n=== .env.local Contents ===")
    with open('.env.local', 'r') as f:
        print(f.read())
