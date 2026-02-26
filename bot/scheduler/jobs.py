"""Scheduler jobs for broadcasting predictions."""

import logging
from datetime import datetime, timedelta
from typing import Optional

import pytz
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.config.settings import settings
from bot.db.session import async_session_maker
from bot.db.models import Prediction, PredictionStatus
from bot.services.prediction_service import PredictionService
from bot.services.user_service import UserService
from bot.services.broadcast_service import BroadcastService
from bot.keyboards.user import get_prediction_keyboard

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def broadcast_prediction_job(bot: Bot, prediction_id: int) -> None:
    """Job to broadcast a scheduled prediction to all users."""
    logger.info(f"Starting broadcast job for prediction {prediction_id}")
    
    async with async_session_maker() as session:
        try:
            prediction_service = PredictionService(session)
            user_service = UserService(session)
            
            # Get the prediction
            prediction = await prediction_service.get_prediction_by_id(prediction_id)
            
            if not prediction:
                logger.error(f"Prediction {prediction_id} not found")
                return
            
            if prediction.status != PredictionStatus.SCHEDULED:
                logger.warning(
                    f"Prediction {prediction_id} is not scheduled (status: {prediction.status})"
                )
                return
            
            if prediction.broadcast_started and not prediction.broadcast_completed:
                logger.warning(f"Broadcast for prediction {prediction_id} already in progress")
                return
            
            # Activate the prediction
            await prediction_service.activate_prediction(prediction)
            await session.commit()
            
            # Get all users
            user_ids = await user_service.get_all_user_telegram_ids()
            
            if not user_ids:
                logger.info("No users to broadcast to")
                await prediction_service.mark_broadcast_completed(prediction)
                await session.commit()
                return
            
            logger.info(f"Broadcasting to {len(user_ids)} users")
            
            # Create keyboard
            keyboard = get_prediction_keyboard(prediction)
            
            # Broadcast
            broadcast_service = BroadcastService(bot)
            result = await broadcast_service.broadcast_prediction(
                prediction=prediction,
                user_ids=user_ids,
                keyboard=keyboard,
            )
            
            # Mark as completed
            await prediction_service.mark_broadcast_completed(prediction)
            await session.commit()
            
            logger.info(
                f"Broadcast completed for prediction {prediction_id}: "
                f"{result['success_count']} success, {result['failure_count']} failed"
            )
            
        except Exception as e:
            logger.exception(f"Error in broadcast job for prediction {prediction_id}: {e}")
            await session.rollback()


async def check_scheduled_predictions(bot: Bot) -> None:
    """Check for scheduled predictions and schedule their broadcast jobs."""
    logger.debug("Checking for scheduled predictions...")
    
    async with async_session_maker() as session:
        try:
            prediction_service = PredictionService(session)
            scheduled = await prediction_service.get_scheduled_prediction()
            
            if not scheduled:
                return
            
            tz = pytz.timezone(settings.scheduler_timezone)
            now = datetime.now(tz)
            
            # If scheduled time has passed, broadcast immediately
            if scheduled.scheduled_at <= now:
                if not scheduled.broadcast_started:
                    logger.info(
                        f"Scheduled prediction {scheduled.id} is due, triggering broadcast"
                    )
                    await broadcast_prediction_job(bot, scheduled.id)
            else:
                # Schedule the job if not already scheduled
                job_id = f"broadcast_{scheduled.id}"
                existing_job = scheduler.get_job(job_id) if scheduler else None
                
                if not existing_job and scheduler:
                    scheduler.add_job(
                        broadcast_prediction_job,
                        trigger=DateTrigger(run_date=scheduled.scheduled_at),
                        id=job_id,
                        args=[bot, scheduled.id],
                        replace_existing=True,
                    )
                    logger.info(
                        f"Scheduled broadcast job for prediction {scheduled.id} "
                        f"at {scheduled.scheduled_at}"
                    )
                    
        except Exception as e:
            logger.exception(f"Error checking scheduled predictions: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Set up and start the scheduler."""
    global scheduler
    
    tz = pytz.timezone(settings.scheduler_timezone)
    
    scheduler = AsyncIOScheduler(timezone=tz)
    
    # Add a job to check for scheduled predictions every minute
    scheduler.add_job(
        check_scheduled_predictions,
        trigger=IntervalTrigger(minutes=1),
        id="check_scheduled_predictions",
        args=[bot],
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Scheduler started")
    
    return scheduler


async def shutdown_scheduler() -> None:
    """Shutdown the scheduler."""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
        scheduler = None
