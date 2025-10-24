"""
Scheduler for automated tasks: daily reports and database cleanup.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from db import Database
from bot import TelegramAnalyticsBot

logger = logging.getLogger(__name__)


class BotScheduler:
    def __init__(self, bot: TelegramAnalyticsBot, database: Database, target_chat_id: int = None):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.db = database
        self.target_chat_id = target_chat_id

    async def cleanup_task(self):
        """Scheduled task to clean up old messages."""
        logger.info("⏰ Running scheduled cleanup task...")
        try:
            deleted_count = await self.db.cleanup_old_messages()
            logger.info(f"✅ Cleanup completed: {deleted_count} messages deleted")
        except Exception as e:
            logger.error(f"❌ Cleanup task failed: {e}")

    async def daily_report_task(self):
        """Scheduled task to send daily analytics report."""
        logger.info("⏰ Running scheduled daily report task...")
        
        if not self.target_chat_id:
            logger.warning("No target chat ID configured for daily reports")
            return
        
        try:
            await self.bot.send_daily_report(self.target_chat_id)
        except Exception as e:
            logger.error(f"❌ Daily report task failed: {e}")

    def start(self):
        """Start the scheduler with configured jobs."""
        # Daily report at 23:59
        self.scheduler.add_job(
            self.daily_report_task,
            CronTrigger(hour=23, minute=59),
            id='daily_report',
            name='Daily Analytics Report',
            replace_existing=True
        )
        logger.info("📅 Scheduled: Daily report at 23:59")
        
        # Daily cleanup at 00:30 (30 minutes after midnight)
        self.scheduler.add_job(
            self.cleanup_task,
            CronTrigger(hour=0, minute=30),
            id='daily_cleanup',
            name='Database Cleanup',
            replace_existing=True
        )
        logger.info("📅 Scheduled: Database cleanup at 00:30")
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("✅ Scheduler started successfully")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def set_target_chat(self, chat_id: int):
        """Set the target chat ID for daily reports."""
        self.target_chat_id = chat_id
        logger.info(f"Target chat ID set to: {chat_id}")
