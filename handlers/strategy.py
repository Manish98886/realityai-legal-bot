from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import get_case_with_details, log_stat, get_case
from ai_engine import ask_ai
from prompts import STRATEGY_PROMPT
from utils import split_message
import logging

logger = logging.getLogger(__name__)


async def strategy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /strategy [case_id]\n\nCase ki complete legal strategy generate karta hai.")
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
    await update.message.reply_text(f"🧠 Case #{case_id} ki strategy generate ho rahi hai... ⏳")
    data = get_case_with_details(case_id)
    c = data["case"]
    evidence_str = "\n".join([f"- {e['item_name']} ({e['status']})" for e in data.get("evidence", [])]) or "No evidence"
    hearings_str = "\n".join([f"- {h['hearing_date']}: {h.get('purpose')}" for h in data.get("hearings", [])]) or "No hearings"
    prompt = STRATEGY_PROMPT.format(
        title=c['title'], case_type=c.get('case_type', 'N/A'), court=c.get('court', 'N/A'),
        fir_number=c.get('fir_number', 'N/A'), sections=c.get('sections', 'N/A'),
        parties=c.get('parties', 'N/A'), description=c.get('description', 'N/A')
    )
    # Add evidence and hearings context
    prompt += f"\n\nEvidence: {evidence_str}\nHearings: {hearings_str}"
    log_stat(user_id, "strategy", str(case_id))
    result = await ask_ai([{"role": "user", "content": prompt}])
    for chunk in split_message(result):
        await update.message.reply_text(chunk)
