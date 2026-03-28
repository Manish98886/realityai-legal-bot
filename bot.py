import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters
from config import BOT_TOKEN, OWNER_ID, REMINDER_ENABLED
from database import init_db, get_or_create_user, log_stat
from ai_engine import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Handlers
from handlers.start import start_cmd, help_cmd, register_conv, profile_cmd
from handlers.cases import newcase_conv, cases_cmd, case_cmd, closecase_cmd, deletecase_cmd
from handlers.drafting import draft_conv, linkcase_cmd
from handlers.strategy import strategy_cmd
from handlers.search import search_cmd, section_cmd
from handlers.evidence import evidence_cmd, addevidence_cmd, evidencestatus_cmd
from handlers.hearings import hearing_cmd, cancelhearing_cmd, calendar_cmd
from handlers.documents import document_handler
from handlers.voice import voice_handler
from handlers.reminders import summary_cmd, weekly_cmd
from handlers.admin import broadcast_cmd, stats_cmd, export_cmd, users_cmd
from handlers.chat import chat_handler
from jobs.reminder_job import setup_reminder_job


async def error_handler(update, context):
    """Global error handler."""
    logger.error(f"Error: {context.error}", exc_info=context.error)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ एक त्रुटि हुई। कृपया पुनः प्रयास करें।")
        except:
            pass


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Check .env file.")
        sys.exit(1)

    logger.info("Initializing database...")
    init_db()

    logger.info("Building application...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- Conversation Handlers ---
    app.add_handler(register_conv)
    app.add_handler(newcase_conv)
    app.add_handler(draft_conv)

    # --- Command Handlers ---
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("cases", cases_cmd))
    app.add_handler(CommandHandler("case", case_cmd))
    app.add_handler(CommandHandler("closecase", closecase_cmd))
    app.add_handler(CommandHandler("deletecase", deletecase_cmd))
    app.add_handler(CommandHandler("linkcase", linkcase_cmd))
    app.add_handler(CommandHandler("strategy", strategy_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("section", section_cmd))
    app.add_handler(CommandHandler("evidence", evidence_cmd))
    app.add_handler(CommandHandler("addevidence", addevidence_cmd))
    app.add_handler(CommandHandler("evidencestatus", evidencestatus_cmd))
    app.add_handler(CommandHandler("hearing", hearing_cmd))
    app.add_handler(CommandHandler("cancelhearing", cancelhearing_cmd))
    app.add_handler(CommandHandler("calendar", calendar_cmd))
    app.add_handler(CommandHandler("summary", summary_cmd))
    app.add_handler(CommandHandler("weekly", weekly_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("export", export_cmd))
    app.add_handler(CommandHandler("users", users_cmd))

    # --- Message Handlers ---
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    # --- Error Handler ---
    app.add_error_handler(error_handler)

    # --- Background Jobs ---
    if REMINDER_ENABLED:
        setup_reminder_job(app)
        logger.info("Reminder job enabled")

    logger.info("Bot starting... RealityAi Lawyer is live!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
