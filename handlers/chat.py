from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database import (
    get_or_create_user, add_conversation, get_conversation_history,
    trim_conversation_history, check_rate_limit, log_stat,
    get_case_with_details, get_case
)
from ai_engine import ask_ai
from prompts import CASE_CONTEXT_PROMPT
from utils import split_message
import logging

logger = logging.getLogger(__name__)


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle general text messages as legal queries."""
    user_id = update.effective_user.id
    text = update.message.text
    if not text or not text.strip():
        return

    get_or_create_user(user_id)
    log_stat(user_id, "message")

    # Rate limit check
    if not check_rate_limit(user_id):
        await update.message.reply_text("⏳ Aapne bahut zyada queries bhej di hain. Thodi der baad phir puchein (max 20/hour).")
        return

    # Add user message to history
    add_conversation(user_id, "user", text)

    # Build messages with conversation history
    history = get_conversation_history(user_id)

    # If linked case, add case context as system message
    linked_case_id = context.user_data.get("linked_case_id")
    if linked_case_id:
        data = get_case_with_details(linked_case_id)
        if data:
            c = data["case"]
            case_context = CASE_CONTEXT_PROMPT.format(
                case_id=c["case_id"], title=c["title"], case_type=c.get("case_type", "N/A"),
                court=c.get("court", "N/A"), fir_number=c.get("fir_number", "N/A"),
                sections=c.get("sections", "N/A"), parties=c.get("parties", "N/A"),
                description=c.get("description", "N/A"), status=c["status"],
                evidence=str(data.get("evidence", [])),
                hearings=str(data.get("hearings", []))
            )
            # Insert case context before history
            history = [{"role": "user", "content": case_context}, {"role": "assistant", "content": "Case context loaded. I'll keep this in mind while answering."}] + history

    # Call AI
    log_stat(user_id, "ai_call")
    result = await ask_ai(history)

    # Save assistant response
    add_conversation(user_id, "assistant", result)
    trim_conversation_history(user_id)

    # Send response (split if too long)
    for chunk in split_message(result):
        try:
            await update.message.reply_text(chunk)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            await update.message.reply_text("Response bhejne mein error aaya. Dobara try karein.")
