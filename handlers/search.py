from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import log_stat
from ai_engine import ask_ai
from prompts import SEARCH_PROMPT
from utils import split_message
import logging

logger = logging.getLogger(__name__)


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /search [query]\n\nExamples:\n/search IPC 498A\n/search landlord tenant eviction\n/search bail application crpc")
        return
    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching: \"{query}\"... ⏳")
    prompt = SEARCH_PROMPT.format(query=query)
    log_stat(user_id, "search", query)
    result = await ask_ai([{"role": "user", "content": prompt}])
    for chunk in split_message(result):
        await update.message.reply_text(chunk)


async def section_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /section [number]\n\nExamples:\n/section 498A\n/section 302\n/section 144 crpc")
        return
    query = " ".join(context.args)
    await update.message.reply_text(f"📖 Looking up section: {query}... ⏳")
    prompt = SEARCH_PROMPT.format(query=f"Section {query} of Indian law - detailed explanation with punishment, bailable/non-bailable, cognizable status, and relevant judgments")
    log_stat(user_id, "section_lookup", query)
    result = await ask_ai([{"role": "user", "content": prompt}])
    for chunk in split_message(result):
        await update.message.reply_text(chunk)
