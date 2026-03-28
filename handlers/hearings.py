from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import get_case, create_hearing, cancel_hearing, get_upcoming_hearings, get_case_hearings, log_stat
from utils import format_hearing_calendar
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def hearing_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /hearing [case_id] [YYYY-MM-DD] [time] [purpose]\n\n"
            "Examples:\n/hearing 1 2026-04-05 10:30 Bail hearing\n/hearing 1 2026-04-10 Arguments"
        )
        return
    try:
        case_id = int(context.args[0])
        hearing_date = context.args[1]
        # Validate date
        datetime.strptime(hearing_date, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("Invalid case ID or date format. Use YYYY-MM-DD.")
        return
    case = get_case(case_id)
    if not case or case["user_id"] != user_id:
        await update.message.reply_text("Case not found.")
        return
    hearing_time = context.args[2] if len(context.args) > 2 else None
    purpose = " ".join(context.args[3:]) if len(context.args) > 3 else (" ".join(context.args[2:]) if len(context.args) > 2 else "Hearing")
    # If time looks like purpose (no colon), shift
    if hearing_time and ":" not in hearing_time:
        purpose = " ".join(context.args[2:])
        hearing_time = None

    h_id = create_hearing(case_id, hearing_date, hearing_time, purpose)
    log_stat(user_id, "hearing_set", f"{case_id}:{h_id}:{hearing_date}")
    await update.message.reply_text(
        f"📅 **Hearing Set!**\n\n"
        f"Case #{case_id}: {case['title']}\n"
        f"Date: {hearing_date}\n"
        f"Time: {hearing_time or 'Not specified'}\n"
        f"Purpose: {purpose}\n\n"
        f"2 din pehle automatic reminder milega."
    )


async def cancelhearing_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /cancelhearing [hearing_id]\n\n/calendar se hearing ID dekhein.")
        return
    try:
        hearing_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid hearing ID.")
        return
    cancel_hearing(hearing_id)
    log_stat(user_id, "hearing_cancelled", str(hearing_id))
    await update.message.reply_text(f"❌ Hearing #{hearing_id} cancelled.")


async def calendar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    days = 7
    if context.args:
        try:
            days = int(context.args[0])
        except ValueError:
            pass
    hearings = get_upcoming_hearings(days)
    # Filter to user's cases only
    from database import get_user_cases
    user_cases = get_user_cases(user_id, offset=0, limit=9999)
    user_case_ids = {c["case_id"] for c in user_cases}
    my_hearings = [h for h in hearings if h["case_id"] in user_case_ids]
    log_stat(user_id, "calendar_view")
    text = format_hearing_calendar(my_hearings)
    await update.message.reply_text(text)
