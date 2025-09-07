from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from database import redis_client
from puppet.client import puppet_client
from utils.helpers import generate_session_id
from config import Config

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = (
        "🤖 Welcome to File Helper Bot!\n\n"
        "Send me a filename or search query and I'll find it for you.\n"
        "Examples:\n"
        "• matrix reloaded\n"
        "• s05e09\n"
        "• document_final.pdf\n\n"
        "Just type what you're looking for!"
    )
    
    await update.message.reply_text(welcome_message)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages"""
    user_id = update.effective_user.id
    query = update.message.text.strip()
    
    if not query:
        await update.message.reply_text("Please provide a search query.")
        return
    
    # Generate session ID for this request
    session_id = generate_session_id()
    
    # Store user session
    session_data = {
        'user_id': user_id,
        'original_query': query,
        'current_index': 0,
        'total_files': 0,
        'buttons_data': [],
        'session_id': session_id
    }
    
    if not redis_client.set_user_session(user_id, session_data):
        await update.message.reply_text("❌ System busy. Please try again in a moment.")
        return
    
    # Notify user that search is in progress
    await update.message.reply_text(f"🔍 Searching for: '{query}'...")
    
    # Forward request to puppet system
    success = await puppet_client.send_search_request(user_id, query, session_id)
    
    if not success:
        await update.message.reply_text("❌ Service temporarily unavailable. Please try again later.")
        redis_client.delete_user_session(user_id)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    # Parse callback data (format: next_userId_index)
    if callback_data.startswith('next_'):
        try:
            parts = callback_data.split('_')
            target_user_id = int(parts[1])
            next_index = int(parts[2])
            
            # Verify the callback is from the correct user
            if user_id != target_user_id:
                await query.edit_message_text("❌ This action is not authorized.")
                return
            
            # Get user session
            session_data = redis_client.get_user_session(user_id)
            if not session_data:
                await query.edit_message_text("❌ Session expired. Please start a new search.")
                return
            
            # Check if there are more files
            if next_index >= session_data.get('total_files', 0):
                await query.edit_message_text(
                    f"📭 No more files found for: '{session_data['original_query']}'\n\n"
                    "Try a different search query."
                )
                return
            
            # Update session with new index
            session_data['current_index'] = next_index
            redis_client.set_user_session(user_id, session_data)
            
            # Request next file via puppet
            success = await puppet_client.request_next_file(
                user_id, 
                session_data['session_id'],
                next_index
            )
            
            if not success:
                await query.edit_message_text("❌ Error fetching next file. Please try a new search.")
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing callback data: {e}")
            await query.edit_message_text("❌ Invalid request. Please start a new search.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or contact support if the issue persists."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

async def send_file_to_user(user_id, file_data, session_data, context: ContextTypes.DEFAULT_TYPE):
    """Send file to user with next button"""
    try:
        caption = (
            f"📁 File {session_data['current_index'] + 1} of {session_data['total_files']}\n"
            f"🔍 Search: {session_data['original_query']}\n\n"
            "⚠️ Files are temporary, please save them immediately.\n"
            "Use 'Next' for more options."
        )
        
        # Create next button if there are more files
        keyboard = None
        if session_data['current_index'] + 1 < session_data['total_files']:
            next_index = session_data['current_index'] + 1
            callback_data = f"next_{user_id}_{next_index}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Next ➡️", callback_data=callback_data)
            ]])
        
        # Send the file based on type
        if file_data['type'] == 'document':
            await context.bot.send_document(
                chat_id=user_id,
                document=file_data['file_id'],
                caption=caption,
                reply_markup=keyboard
            )
        elif file_data['type'] == 'video':
            await context.bot.send_video(
                chat_id=user_id,
                video=file_data['file_id'],
                caption=caption,
                reply_markup=keyboard
            )
        elif file_data['type'] == 'audio':
            await context.bot.send_audio(
                chat_id=user_id,
                audio=file_data['file_id'],
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Received file: {file_data.get('file_name', 'Unknown')}\n\n{caption}",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Error sending file to user {user_id}: {e}")
        raise
