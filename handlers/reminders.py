from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import (
    get_upcoming_hearings, get_user_cases, get_case_evidence, count_user_cases,
    get_case_with_details, log_stat
)
from ai_engine import ask_ai
from prompts import SUMMARY_PROMPT
from utils import split_message
import logging

logger = logging.getLogger(__name__)


async def summary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_stat(user_id, "summary")

    # Get user's cases
    user_cases = get_user_cases(user_id, offset=0, limit=9999)
    case_ids = [c["case_id"] for c in user_cases]
    active_cases = [c for c in user_cases if c["status"] == "active"]

    if not active_cases:
        await update.message.reply_text("📊 Koi active case nahi hai.")
        return

    # Get upcoming hearings (next 3 days)
    hearings = get_upcoming_hearings(days=3)
    my_hearings = [h for h in hearings if h["case_id"] in case_ids]

    # Get pending evidence for active cases
    evidence_summary = []
    for c in active_cases[:10]:
        evidence = get_case_evidence(c["case_id"])
        pending = [e for e in evidence if e["status"] == "pending"]
        if pending:
            evidence_summary.append(f"Case #{c['case_id']} ({c['title']}): {len(pending)} items pending")

    data = f"Active Cases: {len(active_cases)}\n"
    data += f"Total Cases: {len(user_cases)}\n"
    if my_hearings:
        data += "\nUpcoming Hearings:\n"
        for h in my_hearings:
            data += f"- {h['hearing_date']}: Case #{h['case_id']} - {h['title']} ({h.get('purpose', 'N/A')})\n"
    if evidence_summary:
        data += "\nPending Evidence:\n"
        data += "\n".join(evidence_summary)

    prompt = SUMMARY_PROMPT.format(data=data)
    result = await ask_ai([{"role": "user", "content": prompt}])
    for chunk in split_message(result):
        await update.message.reply_text(chunk)


async def weekly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_stat(user_id, "weekly_summary")

    user_cases = get_user_cases(user_id, offset=0, limit=9999)
    case_ids = [c["case_id"] for c in user_cases]
    active = len([c for c in user_cases if c["status"] == "active"])
    closed = len([c for c in user_cases if c["status"] == "closed"])

    hearings = get_upcoming_hearings(days=7)
    my_hearings = [h for h in hearings if h["case_id"] in case_ids]

    evidence_all_pending = 0
    for c in user_cases[:20]:
        evidence = get_case_evidence(c["case_id"])
        evidence_all_pending += len([e for e in evidence if e["status"] == "pending"])

    text = (
        f"📊 **Weekly Summary**\n\n"
        f"**Total Cases:** {len(user_cases)}\n"
        f"🟢 Active: {active} | 🔴 Closed: {closed}\n\n"
    )
    if my_hearings:
        text += "**Upcoming Hearings (7 days):**\n"
        for h in my_hearings:
            text += f"  📅 {h['hearing_date']}: Case #{h['case_id']} - {h['title']}\n"
        text += "\n"
    text += f"**Pending Evidence Items:** {evidence_all_pending}\n"

    for chunk in split_message(text):
        await update.message.reply_text(chunk)
