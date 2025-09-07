import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Frontend Bot Configuration
    FRONTEND_BOT_TOKEN = os.getenv('FRONTEND_BOT_TOKEN')
    
    # Puppet Configuration
    PUPPET_API_ID = int(os.getenv('PUPPET_API_ID', 0))
    PUPPET_API_HASH = os.getenv('PUPPET_API_HASH')
    PUPPET_PHONE_NUMBER = os.getenv('PUPPET_PHONE_NUMBER')
    PUPPET_SESSION_NAME = os.getenv('PUPPET_SESSION_NAME', 'puppet_session')
    
    # Backend Bot Configuration
    BACKEND_BOT_USERNAME = os.getenv('BACKEND_BOT_USERNAME', 'YourBackendBot')
    
    # Database Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    USE_REDIS = os.getenv('USE_REDIS', 'true').lower() == 'true'
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 300))  # 5 minutes
    
    # Validate required environment variables
    @classmethod
    def validate(cls):
        missing_vars = []
        
        if not cls.FRONTEND_BOT_TOKEN:
            missing_vars.append('FRONTEND_BOT_TOKEN')
        if not cls.PUPPET_API_ID:
            missing_vars.append('PUPPET_API_ID')
        if not cls.PUPPET_API_HASH:
            missing_vars.append('PUPPET_API_HASH')
        if not cls.PUPPET_PHONE_NUMBER:
            missing_vars.append('PUPPET_PHONE_NUMBER')
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file or environment variables")
