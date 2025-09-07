#!/usr/bin/env python3
"""
Main entry point for the Telegram File Helper Bot
"""
import asyncio
import signal
import sys
import logging
from config import Config
from frontend.bot import frontend_bot
from puppet.client import puppet_client
from utils.logger import setup_logging, get_logger

logger = get_logger(__name__)

class BotManager:
    """Manager for both frontend and puppet bots"""
    
    def __init__(self):
        self.is_running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signals = [signal.SIGINT, signal.SIGTERM]
        for sig in signals:
            signal.signal(sig, self.handle_shutdown_signal)
    
    def handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received shutdown signal {signum}")
        self.is_running = False
        asyncio.create_task(self.shutdown())
    
    async def startup(self):
        """Initialize and start all bot components"""
        try:
            logger.info("Starting bot system...")
            
            # Connect puppet client first
            logger.info("Connecting puppet client...")
            await puppet_client.connect()
            
            # Start frontend bot
            logger.info("Starting frontend bot...")
            await frontend_bot.run()
            
            self.is_running = True
            logger.info("Bot system started successfully!")
            logger.info("Press Ctrl+C to stop the bot")
            
            # Keep the bot running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start bot system: {e}")
            await self.shutdown()
            sys.exit(1)
    
    async def shutdown(self):
        """Shutdown all bot components gracefully"""
        try:
            logger.info("Shutting down bot system...")
            
            # Stop frontend bot
            if hasattr(frontend_bot, 'stop'):
                await frontend_bot.stop()
            
            # Disconnect puppet client
            if hasattr(puppet_client, 'disconnect'):
                await puppet_client.disconnect()
            
            logger.info("Bot system shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Ensure event loop stops
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            asyncio.get_event_loop().stop()

async def main():
    """Main async function"""
    # Setup logging
    setup_logging()
    
    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create and run bot manager
    bot_manager = BotManager()
    await bot_manager.startup()

if __name__ == "__main__":
    try:
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)