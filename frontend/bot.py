from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import logging
from config import Config
from .handlers import start_handler, message_handler, callback_handler, error_handler

logger = logging.getLogger(__name__)

class FrontendBot:
    def __init__(self):
        self.application = Application.builder().token(Config.FRONTEND_BOT_TOKEN).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all message and callback handlers"""
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        self.application.add_handler(CallbackQueryHandler(callback_handler))
        self.application.add_error_handler(error_handler)
    
    async def run(self):
        """Start the bot"""
        logger.info("Starting Frontend Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Frontend Bot is now running!")
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping Frontend Bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Frontend Bot stopped successfully!")

# Global bot instance
frontend_bot = FrontendBot()