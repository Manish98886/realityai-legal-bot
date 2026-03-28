import json
import io
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import (
    get_all_users, get_all_cases, get_stats, log_stat,
    get_user, get_case_with_details
)
from config import OWNER_ID
from utils import split_message
import logging

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin only command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast [message]")
        return
    message = " ".join(context.args)
    users = get_all_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=f"📢 **Announcement**\n\n{message}")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"📢 Broadcast complete\n✅ Sent: {sent}\n❌ Failed: {failed}")
    log_stat(user_id, "broadcast", f"sent:{sent}")


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin only command.")
        return
    stats = get_stats()
    text = (
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"📋 Total Cases: {stats['total_cases']}\n"
        f"🟢 Active Cases: {stats['active_cases']}\n"
        f"💬 Total Messages: {stats['total_messages']}\n"
        f"🤖 AI Calls: {stats['ai_calls']}"
    )
    await update.message.reply_text(text)
    log_stat(user_id, "stats_view")


async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin only command.")
        return
    users = get_all_users()
    cases = get_all_cases()
    export_data = {"users": users, "cases": []}
    for c in cases:
        detail = get_case_with_details(c["case_id"])
        if detail:
            export_data["cases"].append(detail)

    json_str = json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
    # Send as document if too long
    if len(json_str) > 4000:
        file = io.BytesIO(json_str.encode("utf-8"))
        file.name = "realityai_lawyer_backup.json"
        await update.message.reply_document(document=file, caption="📦 Full database backup")
    else:
        for chunk in split_message(f"📦 **Export Data:**\n\n```json\n{json_str}\n```"):
            await update.message.reply_text(chunk)
    log_stat(user_id, "export")


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Admin only command.")
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("No registered users yet.")
        return
    lines = ["👥 **Registered Advocates:**\n"]
    for u in users:
        name = u.get("name") or "Unregistered"
        spec = u.get("specialization") or ""
        bar = u.get("bar_council_number") or ""
        reg_date = u.get("registered_at", "")[:10]
        lines.append(f"  **{name}** (ID: {u['user_id']})")
        if spec:
            lines.append(f"    Specialization: {spec}")
        if bar:
            lines.append(f"    Bar Council: {bar}")
        lines.append(f"    Registered: {reg_date}\n")
    for chunk in split_message("\n".join(lines)):
        await update.message.reply_text(chunk)
    log_stat(user_id, "users_list")
