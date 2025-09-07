from telethon import TelegramClient, events, types
from telethon.tl.types import Message
import logging
import asyncio
from config import Config
from .message_parser import parse_message, extract_buttons, detect_error
from .actions import click_button, join_channel
from database import redis_client
from frontend.handlers import send_file_to_user
from utils.helpers import generate_session_id

logger = logging.getLogger(__name__)

class PuppetClient:
    def __init__(self):
        self.client = TelegramClient(
            Config.PUPPET_SESSION_NAME,
            Config.PUPPET_API_ID,
            Config.PUPPET_API_HASH
        )
        self.backend_bot_username = Config.BACKEND_BOT_USERNAME
        self.is_connected = False
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup event handlers for the puppet client"""
        
        @self.client.on(events.NewMessage(from_users=self.backend_bot_username))
        async def handle_backend_message(event):
            """Handle messages from the backend bot"""
            try:
                message = event.message
                logger.info(f"Received message from backend: {message.text}")
                
                # Parse the message to determine action
                message_type, data = parse_message(message)
                
                if message_type == 'buttons':
                    # Store buttons for user session and click first one
                    user_id, session_id = await self._get_request_context(message)
                    if user_id and session_id:
                        await self._handle_buttons(message, user_id, session_id, data)
                
                elif message_type == 'join_request':
                    # Handle join channel request
                    success = await join_channel(self.client, data['channel'])
                    if success:
                        # Resend original request
                        user_id, session_id = await self._get_request_context(message)
                        if user_id and session_id:
                            await self.resend_search_request(user_id, session_id)
                
                elif message_type == 'error':
                    # Forward error to frontend
                    user_id, session_id = await self._get_request_context(message)
                    if user_id and session_id:
                        await self._forward_error_to_frontend(user_id, data['error_message'])
                
                elif message_type == 'file':
                    # Forward file to frontend
                    user_id, session_id = await self._get_request_context(message)
                    if user_id and session_id:
                        await self._forward_file_to_frontend(user_id, session_id, data)
                
            except Exception as e:
                logger.error(f"Error handling backend message: {e}")
    
    async def _get_request_context(self, message):
        """Get user_id and session_id from message context"""
        try:
            # Check if this is a reply to our request
            if message.reply_to_msg_id:
                # Look up the request state by message ID
                state = redis_client.get_request_state(Config.PUPPET_SESSION_NAME, message.reply_to_msg_id)
                if state:
                    return state['user_id'], state['session_id']
            
            # Fallback: check recent messages for context
            # This is a simplified approach - in production you might need more sophisticated tracking
            async for recent_msg in self.client.iter_messages(self.backend_bot_username, limit=10):
                if recent_msg.id == message.reply_to_msg_id:
                    # This would require more sophisticated state tracking
                    pass
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting request context: {e}")
            return None, None
    
    async def _handle_buttons(self, message, user_id, session_id, buttons_data):
        """Handle message with buttons"""
        try:
            # Store buttons in user session
            session_data = redis_client.get_user_session(user_id)
            if session_data:
                session_data['buttons_data'] = buttons_data
                session_data['total_files'] = len(buttons_data)
                redis_client.set_user_session(user_id, session_data)
            
            # Click the first button
            if buttons_data:
                success = await click_button(self.client, message, buttons_data[0])
                if not success:
                    await self._forward_error_to_frontend(user_id, "Failed to process request")
        
        except Exception as e:
            logger.error(f"Error handling buttons: {e}")
            await self._forward_error_to_frontend(user_id, f"Processing error: {str(e)}")
    
    async def _forward_error_to_frontend(self, user_id, error_message):
        """Forward error message to frontend bot"""
        try:
            from main import application
            error_text = (
                "❌ Error occurred while processing your request:\n\n"
                f"{error_message}\n\n"
                "Please check the spelling or try a different search term."
            )
            
            await application.bot.send_message(
                chat_id=user_id,
                text=error_text
            )
            
        except Exception as e:
            logger.error(f"Error forwarding error to frontend: {e}")
    
    async def _forward_file_to_frontend(self, user_id, session_id, file_data):
        """Forward received file to frontend"""
        try:
            from main import application
            
            # Get user session
            session_data = redis_client.get_user_session(user_id)
            if not session_data:
                logger.error(f"No session found for user {user_id}")
                return
            
            # Update context for sending file
            context = type('obj', (object,), {
                'bot': application.bot
            })
            
            # Send file to user
            await send_file_to_user(user_id, file_data, session_data)
            
        except Exception as e:
            logger.error(f"Error forwarding file to frontend: {e}")
            await self._forward_error_to_frontend(user_id, "Failed to deliver file")
    
    async def connect(self):
        """Connect to Telegram"""
        try:
            await self.client.start(phone=Config.PUPPET_PHONE_NUMBER)
            self.is_connected = True
            logger.info("Puppet client connected successfully")
            
            # Test backend bot connection
            try:
                await self.client.get_entity(self.backend_bot_username)
                logger.info(f"Backend bot {self.backend_bot_username} is accessible")
            except Exception as e:
                logger.warning(f"Backend bot might not be accessible: {e}")
                
        except Exception as e:
            logger.error(f"Failed to connect puppet client: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            logger.info("Puppet client disconnected")
    
    async def send_search_request(self, user_id, query, session_id):
        """Send search request to backend bot"""
        try:
            # Send message to backend bot
            message = await self.client.send_message(
                self.backend_bot_username,
                query
            )
            
            # Store request state
            state_data = {
                'user_id': user_id,
                'session_id': session_id,
                'query': query,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            redis_client.set_request_state(
                Config.PUPPET_SESSION_NAME,
                message.id,
                state_data
            )
            
            logger.info(f"Sent search request for user {user_id}: {query}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending search request: {e}")
            return False
    
    async def request_next_file(self, user_id, session_id, next_index):
        """Request next file by clicking the appropriate button"""
        try:
            # Get user session
            session_data = redis_client.get_user_session(user_id)
            if not session_data or not session_data.get('buttons_data'):
                logger.error(f"No buttons data for user {user_id}")
                return False
            
            # Get the button data for the requested index
            if next_index >= len(session_data['buttons_data']):
                logger.error(f"Invalid button index {next_index}")
                return False
            
            button_data = session_data['buttons_data'][next_index]
            
            # We need to simulate clicking the button
            # This requires the original message ID, which we might not have stored
            # For now, we'll resend the search request and handle the new response
            # In a production system, you'd want to store the original message context
            
            logger.warning("Next file request - implementation requires original message context")
            return await self.send_search_request(user_id, session_data['original_query'], session_id)
            
        except Exception as e:
            logger.error(f"Error requesting next file: {e}")
            return False
    
    async def resend_search_request(self, user_id, session_id):
        """Resend search request after joining channel"""
        try:
            session_data = redis_client.get_user_session(user_id)
            if session_data:
                return await self.send_search_request(user_id, session_data['original_query'], session_id)
            return False
        except Exception as e:
            logger.error(f"Error resending search request: {e}")
            return False

# Global puppet client instance
puppet_client = PuppetClient()