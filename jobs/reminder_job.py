import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_hearings_for_reminder, mark_hearing_reminder_sent, get_case
from config import REMINDER_DAYS_BEFORE

logger = logging.getLogger(__name__)


def setup_reminder_job(app):
    """Setup APScheduler job for hearing reminders."""
    scheduler = AsyncIOScheduler()

    async def send_reminders():
        """Check and send hearing reminders."""
        try:
            hearings = get_hearings_for_reminder(REMINDER_DAYS_BEFORE)
            for h in hearings:
                user_id = h["user_id"]
                case = get_case(h["case_id"])
                if not case:
                    continue
                msg = (
                    f"⏰ **Hearing Reminder!**\n\n"
                    f"Case #{h['case_id']}: {case['title']}\n"
                    f"📅 Date: {h['hearing_date']}\n"
                    f"{'🕐 Time: ' + h['hearing_time'] if h.get('hearing_time') else ''}\n"
                    f"📌 Purpose: {h.get('purpose', 'N/A')}\n"
                    f"🏢 Court: {case.get('court', 'N/A')}\n\n"
                    f"2 din baad hearing hai — tayyari ensure karein!"
                )
                try:
                    await app.bot.send_message(chat_id=user_id, text=msg)
                    mark_hearing_reminder_sent(h["id"])
                    logger.info(f"Reminder sent: hearing #{h['id']} to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send reminder to {user_id}: {e}")
        except Exception as e:
            logger.error(f"Reminder job error: {e}")

    # Run every 2 hours
    scheduler.add_job(send_reminders, 'interval', hours=2, id='hearing_reminder')
    scheduler.start()
    logger.info(f"Reminder scheduler started (every 2h, {REMINDER_DAYS_BEFORE} days before hearing)")
