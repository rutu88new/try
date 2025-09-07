import hashlib
import time
import random
import string
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_session_id(length: int = 8) -> str:
    """Generate a unique session ID"""
    timestamp = str(time.time_ns())
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    hash_input = timestamp + random_str
    
    return hashlib.md5(hash_input.encode()).hexdigest()[:length].upper()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove invalid characters"""
    if not filename:
        return "unknown"
    
    # Remove invalid characters for filenames
    invalid_chars = '<>:"/\\|?*\'"'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename.strip()

def extract_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    if not filename or '.' not in filename:
        return ''
    
    return filename.split('.')[-1].lower()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.2f} {size_names[i]}"

def parse_callback_data(callback_data: str) -> Optional[Dict[str, Any]]:
    """Parse callback data string into components"""
    if not callback_data:
        return None
    
    try:
        if callback_data.startswith('next_'):
            parts = callback_data.split('_')
            if len(parts) >= 3:
                return {
                    'type': 'next',
                    'user_id': int(parts[1]),
                    'next_index': int(parts[2])
                }
        
        elif callback_data in ['retry', 'new_search']:
            return {
                'type': callback_data
            }
        
        return None
        
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing callback data '{callback_data}': {e}")
        return None

def create_callback_data(action: str, **kwargs) -> str:
    """Create callback data string"""
    if action == 'next':
        if 'user_id' in kwargs and 'next_index' in kwargs:
            return f"next_{kwargs['user_id']}_{kwargs['next_index']}"
    
    elif action in ['retry', 'new_search']:
        return action
    
    raise ValueError(f"Invalid callback data parameters for action '{action}'")

def is_valid_user_id(user_id: Any) -> bool:
    """Check if user ID is valid"""
    try:
        user_id_int = int(user_id)
        return user_id_int > 0
    except (ValueError, TypeError):
        return False

def get_timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate_timeout(base_timeout: int, retry_count: int) -> int:
    """Calculate timeout with exponential backoff"""
    return min(base_timeout * (2 ** retry_count), 300)  # Max 5 minutes