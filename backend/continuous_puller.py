#!/usr/bin/env python3
"""
Continuous Data Puller for Windows
Runs the data puller every 10 seconds in a loop
"""

import time
import subprocess
import sys
from datetime import datetime

def run_data_puller():
    """Run the data puller script"""
    try:
        result = subprocess.run([
            sys.executable, 
            'automated_data_puller.py'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️  Data puller failed: {result.stderr}")
        
    except Exception as e:
        print(f"❌ Error running data puller: {e}")

def main():
    print("🚀 Starting continuous ActivityWatch data pulling...")
    print("📊 Pulling data every 10 seconds")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"🔄 [{timestamp}] Running data puller...")
            
            run_data_puller()
            
            print(f"✅ [{timestamp}] Complete. Waiting 10 seconds...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Data puller stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
