import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_app_config

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    """Create and start the APScheduler with configured jobs."""
    global scheduler
    config = get_app_config()

    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        "app.tasks.jobs:auto_archive_cards",
        "interval",
        hours=config.archive_interval_hours,
        id="auto_archive_cards",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with archive interval: %dh", config.archive_interval_hours)


def stop_scheduler() -> None:
    """Shutdown the running scheduler."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    scheduler = None
