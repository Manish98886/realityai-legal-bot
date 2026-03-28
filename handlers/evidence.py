from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import get_case, add_evidence, get_case_evidence, update_evidence_status, log_stat
from utils import format_evidence_list
import logging

logger = logging.getLogger(__name__)


async def evidence_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /evidence [case_id]\n\nCase ka evidence checklist dekhta hai.")
        return
    try:
        case_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid case ID.")
        return
    case = get_case(case_id)
    if not case or case["user_id"] != user_id:
        await update.message.reply_text("Case not found ya aapke access mein nahi hai.")
        return
    evidence = get_case_evidence(case_id)
    log_stat(user_id, "evidence_list", str(case_id))
    text = format_evidence_list(evidence, case_id)
    await update.message.reply_text(text)


async def addevidence_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addevidence [case_id] [description]\n\nExample:\n/addevidence 1 FIR Copy")
        return
    try:
        case_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid case ID.")
        return
    case = get_case(case_id)
    if not case or case["user_id"] != user_id:
        await update.message.reply_text("Case not found.")
        return
    desc = " ".join(context.args[1:])
    ev_id = add_evidence(case_id, desc, item_type="document")
    log_stat(user_id, "evidence_added", f"{case_id}:{ev_id}")
    await update.message.reply_text(f"✅ Evidence added — **#{ev_id}**: {desc}\n\nStatus: pending\n\n/evidencestatus {ev_id} collected — Jab collect ho jaye")


async def evidencestatus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /evidencestatus [evidence_id] [status]\n\nStatus: pending / collected / submitted")
        return
    try:
        ev_id = int(context.args[0])
        status = context.args[1].lower()
    except (ValueError, IndexError):
        await update.message.reply_text("Invalid arguments.")
        return
    if status not in ("pending", "collected", "submitted"):
        await update.message.reply_text("Invalid status. Use: pending, collected, or submitted")
        return
    update_evidence_status(ev_id, status)
    log_stat(user_id, "evidence_status_update", f"{ev_id}:{status}")
    emoji = {"pending": "⏳", "collected": "✅", "submitted": "📨"}.get(status, "")
    await update.message.reply_text(f"{emoji} Evidence #{ev_id} status updated to **{status}**")
