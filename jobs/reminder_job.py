import asyncio
import logging
from database import get_hearings_for_reminder, mark_hearing_reminder_sent, get_case
from config import REMINDER_DAYS_BEFORE

logger = logging.getLogger(__name__)


def setup_reminder_job(app):
    """Setup reminder job using python-telegram-bot's built-in job_queue."""
    async def job_callback(context):
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
                    await context.bot.send_message(chat_id=user_id, text=msg)
                    mark_hearing_reminder_sent(h["id"])
                    logger.info(f"Reminder sent: hearing #{h['id']} to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send reminder to {user_id}: {e}")
        except Exception as e:
            logger.error(f"Reminder job error: {e}")

    # Use telegram-bot's built-in job queue (runs every 2 hours)
    app.job_queue.run_repeating(job_callback, interval=7200, first=10, name="hearing_reminder")
    logger.info(f"Reminder job registered (every 2h, {REMINDER_DAYS_BEFORE} days before hearing)")
