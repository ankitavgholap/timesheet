# backend/config.py - Enhanced configuration with python-dotenv
import os
import socket
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv('.env.local', override=True)  # Load local first
load_dotenv('.env.production', override=False)  # Fallback to production
load_dotenv()  # Load default .env if exists

class Config:
    # Environment detection
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')  # 'local' or 'production'
    
    # Local developer settings
    LOCAL_DEVELOPER_NAME = os.getenv('LOCAL_DEVELOPER_NAME', socket.gethostname())
    
    # ActivityWatch settings
    ACTIVITYWATCH_HOST = os.getenv('ACTIVITYWATCH_HOST', 'http://localhost:5600')
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./timesheet.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Multi-developer settings
    ENABLE_NETWORK_DISCOVERY = os.getenv('ENABLE_NETWORK_DISCOVERY', 'false').lower() == 'true'
    DISCOVERY_CACHE_HOURS = int(os.getenv('DISCOVERY_CACHE_HOURS', '1'))
    MAX_NETWORK_SCAN_RANGE = int(os.getenv('MAX_NETWORK_SCAN_RANGE', '2'))  # Max networks to scan
    
    # Production-specific settings
    PRODUCTION_DOMAIN = os.getenv('PRODUCTION_DOMAIN', 'your-production-domain.com')
    PRODUCTION_DATABASE_URL = os.getenv('PRODUCTION_DATABASE_URL', DATABASE_URL)
    
    @classmethod
    def is_local(cls):
        """Check if running in local environment"""
        return cls.ENVIRONMENT.lower() in ['local', 'development', 'dev']
    
    @classmethod 
    def is_production(cls):
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() in ['production', 'prod']
    
    @classmethod
    def get_database_url(cls):
        """Get appropriate database URL based on environment"""
        if cls.is_production():
            return cls.PRODUCTION_DATABASE_URL
        return cls.DATABASE_URL
    
    @classmethod
    def get_local_developer_info(cls):
        """Get local developer information"""
        return {
            'name': cls.LOCAL_DEVELOPER_NAME,
            'hostname': socket.gethostname(),
            'environment': cls.ENVIRONMENT
        }
    
    @classmethod
    def should_enable_network_discovery(cls):
        """Check if network discovery should be enabled"""
        # Only enable in production or if explicitly set
        return cls.is_production() or cls.ENABLE_NETWORK_DISCOVERY
    
    @classmethod
    def get_cors_origins(cls):
        """Get CORS origins based on environment"""
        if cls.is_local():
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        else:
            return [
                "http://localhost:3000",  # For development
                f"https://{cls.PRODUCTION_DOMAIN}",
                f"http://{cls.PRODUCTION_DOMAIN}"
            ]

# Print debug info
print(f"DEBUG: ENVIRONMENT = {Config.ENVIRONMENT}")
print(f"DEBUG: DATABASE_URL = {Config.DATABASE_URL}")
print(f"DEBUG: LOCAL_DEVELOPER_NAME = {Config.LOCAL_DEVELOPER_NAME}")
