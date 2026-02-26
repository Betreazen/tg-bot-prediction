"""Main entry point for the Telegram bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config.settings import settings
from bot.db.session import init_db, close_db
from bot.middlewares import DatabaseMiddleware, AdminMiddleware
from bot.handlers.user import start_router, prediction_router
from bot.handlers.admin import menu_router, create_router
from bot.scheduler import setup_scheduler, shutdown_scheduler


def setup_logging() -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Reduce noise from libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


async def on_startup(bot: Bot) -> None:
    """Startup handler."""
    logger = logging.getLogger(__name__)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Setup scheduler
    setup_scheduler(bot)
    logger.info("Scheduler initialized")
    
    # Get bot info
    bot_info = await bot.get_me()
    logger.info(f"Bot started: @{bot_info.username}")


async def on_shutdown(bot: Bot) -> None:
    """Shutdown handler."""
    logger = logging.getLogger(__name__)
    
    # Shutdown scheduler
    await shutdown_scheduler()
    logger.info("Scheduler stopped")
    
    # Close database
    await close_db()
    logger.info("Database connections closed")


async def main() -> None:
    """Main function to run the bot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Create dispatcher with memory storage for FSM
    # In production, consider using Redis storage
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    
    # Register routers
    dp.include_router(start_router)
    dp.include_router(prediction_router)
    dp.include_router(menu_router)
    dp.include_router(create_router)
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("Starting bot...")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
