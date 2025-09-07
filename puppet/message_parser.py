from telethon import types
import logging
import re

logger = logging.getLogger(__name__)

def parse_message(message):
    """
    Parse backend bot message and determine action type
    Returns: (message_type, data)
    """
    try:
        # Check for buttons first
        if hasattr(message, 'buttons') and message.buttons:
            buttons_data = extract_buttons(message)
            return 'buttons', buttons_data
        
        # Check for join requests
        join_data = detect_join_request(message.text)
        if join_data:
            return 'join_request', join_data
        
        # Check for error messages
        error_data = detect_error(message.text)
        if error_data:
            return 'error', error_data
        
        # Check for files
        if message.media:
            file_data = extract_file_data(message)
            if file_data:
                return 'file', file_data
        
        # Default to text message
        return 'text', {'text': message.text}
        
    except Exception as e:
        logger.error(f"Error parsing message: {e}")
        return 'unknown', {}

def extract_buttons(message):
    """Extract button data from message"""
    buttons_data = []
    
    try:
        for row in message.buttons:
            for button in row:
                if hasattr(button, 'data') and button.data:
                    buttons_data.append({
                        'text': button.text,
                        'data': button.data,
                        'same_peer': getattr(button, 'same_peer', False)
                    })
                elif hasattr(button, 'url'):
                    buttons_data.append({
                        'text': button.text,
                        'url': button.url,
                        'same_peer': getattr(button, 'same_peer', False)
                    })
        
        logger.info(f"Extracted {len(buttons_data)} buttons")
        return buttons_data
        
    except Exception as e:
        logger.error(f"Error extracting buttons: {e}")
        return []

def detect_join_request(text):
    """Detect join channel requests"""
    if not text:
        return None
    
    join_patterns = [
        r'join.*channel',
        r'subscribe.*channel',
        r'channel.*join',
        r'first.*join',
        r'join.*first'
    ]
    
    text_lower = text.lower()
    
    for pattern in join_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            # Try to extract channel username
            channel_match = re.search(r'@([a-zA-Z0-9_]+)', text)
            if channel_match:
                return {'channel': channel_match.group(1)}
            else:
                return {'channel': None}
    
    return None

def detect_error(text):
    """Detect error messages"""
    if not text:
        return None
    
    error_patterns = [
        r'could not find',
        r'not found',
        r'not released',
        r'not available',
        r'error',
        r'failed',
        r'unavailable'
    ]
    
    text_lower = text.lower()
    
    for pattern in error_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return {'error_message': text}
    
    return None

def extract_file_data(message):
    """Extract file data from message"""
    try:
        media = message.media
        file_data = {
            'type': 'unknown',
            'file_id': None,
            'file_name': 'Unknown',
            'file_size': 0
        }
        
        if isinstance(media, types.MessageMediaDocument):
            file_data['type'] = 'document'
            if media.document:
                file_data['file_id'] = media.document.id
                for attr in media.document.attributes:
                    if hasattr(attr, 'file_name'):
                        file_data['file_name'] = attr.file_name
                file_data['file_size'] = media.document.size
        
        elif isinstance(media, types.MessageMediaVideo):
            file_data['type'] = 'video'
            if media.video:
                file_data['file_id'] = media.video.id
                file_data['file_size'] = media.video.size
        
        elif isinstance(media, types.MessageMediaAudio):
            file_data['type'] = 'audio'
            if media.audio:
                file_data['file_id'] = media.audio.id
                file_data['file_size'] = media.audio.size
        
        elif isinstance(media, types.MessageMediaPhoto):
            file_data['type'] = 'photo'
            if media.photo:
                file_data['file_id'] = media.photo.id
        
        # For Telegram bot API, we need to get the file_id differently
        # This is a placeholder - actual implementation depends on how files are handled
        file_data['telegram_file_id'] = f"await message.download_media()"
        
        return file_data
        
    except Exception as e:
        logger.error(f"Error extracting file data: {e}")
        return None