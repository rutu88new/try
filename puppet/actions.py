from telethon import TelegramClient
from telethon.tl.types import Message
import logging
import asyncio

logger = logging.getLogger(__name__)

async def click_button(client, message, button_data):
    """Click a button on a message"""
    try:
        if 'data' in button_data:
            # Inline button with callback data
            await client.callback_query(
                message=message.id,
                data=button_data['data']
            )
            logger.info(f"Clicked button: {button_data['text']}")
            return True
        
        elif 'url' in button_data:
            # URL button - can't click programmatically
            logger.warning(f"URL button cannot be clicked: {button_data['text']}")
            return False
        
        else:
            logger.warning(f"Unknown button type: {button_data}")
            return False
            
    except Exception as e:
        logger.error(f"Error clicking button: {e}")
        return False

async def join_channel(client, channel_username):
    """Join a channel"""
    try:
        if not channel_username:
            logger.error("No channel username provided")
            return False
        
        entity = await client.get_entity(channel_username)
        await client.join_channel(entity)
        logger.info(f"Joined channel: {channel_username}")
        
        # Wait a moment for the join to process
        await asyncio.sleep(2)
        return True
        
    except Exception as e:
        logger.error(f"Error joining channel {channel_username}: {e}")
        return False

async def resend_original_request(client, backend_bot_username, original_query):
    """Resend original search request"""
    try:
        await client.send_message(backend_bot_username, original_query)
        logger.info(f"Resent request: {original_query}")
        return True
    except Exception as e:
        logger.error(f"Error resending request: {e}")
        return False