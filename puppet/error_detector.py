import re
import logging

logger = logging.getLogger(__name__)

class ErrorDetector:
    """Detect error messages from backend bot"""
    
    ERROR_PATTERNS = [
        r'could not find',
        r'not found',
        r'not released',
        r'not available',
        r'error',
        r'failed',
        r'unavailable',
        r'try again',
        r'check spelling',
        r'invalid',
        r'no results',
        r'not exist'
    ]
    
    JOIN_PATTERNS = [
        r'join.*channel',
        r'subscribe.*channel',
        r'channel.*join',
        r'first.*join',
        r'join.*first',
        r'membership required'
    ]
    
    @classmethod
    def is_error_message(cls, text):
        """Check if message contains error patterns"""
        if not text:
            return False
        
        text_lower = text.lower()
        for pattern in cls.ERROR_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def is_join_request(cls, text):
        """Check if message requires joining a channel"""
        if not text:
            return False
        
        text_lower = text.lower()
        for pattern in cls.JOIN_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def extract_channel_from_message(cls, text):
        """Extract channel username from join request message"""
        if not text:
            return None
        
        # Look for @username pattern
        match = re.search(r'@([a-zA-Z0-9_]+)', text)
        if match:
            return match.group(1)
        
        # Look for t.me/username pattern
        match = re.search(r't\.me/([a-zA-Z0-9_]+)', text)
        if match:
            return match.group(1)
        
        return None