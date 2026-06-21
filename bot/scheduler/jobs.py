"""Scheduler jobs for broadcasting predictions."""

import logging
from typing import Optional, Set

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.db.session import async_session_maker
from bot.db.models import PredictionStatus
from bot.services.prediction_service import PredictionService
from bot.services.user_service import UserService
from bot.services.broadcast_service import BroadcastService
from bot.keyboards.user import get_prediction_keyboard
from bot.utils.timezone import get_tz, now as tz_now

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

# In-flight broadcasts, to prevent the same prediction being broadcast twice
# concurrently (e.g. the 1-minute checker firing while a broadcast still runs).
_broadcasts_in_progress: Set[int] = set()


async def broadcast_prediction_job(bot: Bot, prediction_id: int) -> None:
    """Broadcast a prediction to all users.

    Safe to call for a SCHEDULED prediction (it activates it first) or to resume
    an ACTIVE prediction whose broadcast was interrupted. Idempotent against
    concurrent invocations via an in-process guard.
    """
    if prediction_id in _broadcasts_in_progress:
        logger.warning(f"Broadcast for prediction {prediction_id} already in progress, skipping")
        return

    _broadcasts_in_progress.add(prediction_id)
    logger.info(f"Starting broadcast job for prediction {prediction_id}")

    try:
        async with async_session_maker() as session:
            try:
                prediction_service = PredictionService(session)
                user_service = UserService(session)

                prediction = await prediction_service.get_prediction_by_id(prediction_id)

                if not prediction:
                    logger.error(f"Prediction {prediction_id} not found")
                    return

                if prediction.broadcast_completed:
                    logger.info(f"Prediction {prediction_id} already broadcast, skipping")
                    return

                if prediction.status == PredictionStatus.SCHEDULED:
                    # First run: activate (archives any current active prediction).
                    await prediction_service.activate_prediction(prediction)
                    await session.commit()
                elif prediction.status == PredictionStatus.ACTIVE:
                    # Resuming an interrupted broadcast.
                    logger.info(f"Resuming interrupted broadcast for prediction {prediction_id}")
                else:
                    logger.warning(
                        f"Prediction {prediction_id} not broadcastable (status: {prediction.status})"
                    )
                    return

                user_ids = await user_service.get_all_user_telegram_ids()

                if not user_ids:
                    logger.info("No users to broadcast to")
                    await prediction_service.mark_broadcast_completed(prediction)
                    await session.commit()
                    return

                logger.info(f"Broadcasting to {len(user_ids)} users")

                keyboard = get_prediction_keyboard(prediction)
                broadcast_service = BroadcastService(bot)
                result = await broadcast_service.broadcast_prediction(
                    prediction=prediction,
                    user_ids=user_ids,
                    keyboard=keyboard,
                )

                await prediction_service.mark_broadcast_completed(prediction)
                await session.commit()

                logger.info(
                    f"Broadcast completed for prediction {prediction_id}: "
                    f"{result['success_count']} success, {result['failure_count']} failed"
                )

            except Exception as e:
                logger.exception(f"Error in broadcast job for prediction {prediction_id}: {e}")
                await session.rollback()
    finally:
        _broadcasts_in_progress.discard(prediction_id)


async def resume_incomplete_broadcasts(bot: Bot) -> None:
    """On startup, finish any broadcasts that were interrupted by a restart."""
    async with async_session_maker() as session:
        prediction_service = PredictionService(session)
        incomplete = await prediction_service.get_incomplete_broadcasts()

    for prediction in incomplete:
        logger.warning(
            f"Found incomplete broadcast for prediction {prediction.id}, resuming"
        )
        await broadcast_prediction_job(bot, prediction.id)


async def check_scheduled_predictions(bot: Bot) -> None:
    """Check for scheduled predictions and schedule their broadcast jobs."""
    logger.debug("Checking for scheduled predictions...")
    
    async with async_session_maker() as session:
        try:
            prediction_service = PredictionService(session)
            scheduled = await prediction_service.get_scheduled_prediction()
            
            if not scheduled:
                return

            now = tz_now()

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

    scheduler = AsyncIOScheduler(timezone=get_tz())
    
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
