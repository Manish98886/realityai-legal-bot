from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from database import get_or_create_user, update_user, log_stat
import logging

logger = logging.getLogger(__name__)

REGISTER_NAME, REGISTER_BAR, REGISTER_SPEC = range(3)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id)
    log_stat(user.id, "start")
    await update.message.reply_text(
        f"🧑‍⚖️ **RealityAi Legal Assistant**\n\n"
        f"Namaste {user.first_name}! Main aapka AI legal assistant hoon.\n"
        f"Indian law mein 50+ saal ka experience — Criminal, Civil, drafting, strategy, sab kuch.\n\n"
        f"**Quick Commands:**\n"
        f"/help — Sab commands dekho\n"
        f"/newcase — Nayi case register karo\n"
        f"/register — Advocate ke roop mein register karo\n"
        f"/search [query] — Kanoon ya judgment search karo\n\n"
        f"Ya seedha koi legal question pucho!\n\n"
        f"⚠️ यह AI सहायता है, योग्य वकील का विकल्प नहीं।"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🧑‍⚖️ **RealityAi Legal Assistant — Commands**

📋 **Case Management:**
/newcase — Nayi case create karo
/cases — Sab cases ki list
/case [ID] — Case ki puri details
/closecase [ID] — Case close karo
/deletecase [ID] — Case delete karo

📝 **Drafting:**
/draft [type] — Legal document draft karo
/linkcase [ID] — Current draft ko case se link karo
Types: bail, plaint, ws, fir, rti, appeal, vakalatnama, notice, agreement, affidavit, complaint

🧠 **Strategy & Research:**
/strategy [case_id] — Legal strategy generate karo
/search [query] — Kanoon/judgment search karo
/section [number] — IPC/CrPC/CPC section dekho

📎 **Evidence & Hearings:**
/evidence [case_id] — Evidence checklist dekho
/addevidence [case_id] [desc] — Evidence add karo
/evidencestatus [id] [status] — Status update karo
/hearing [case_id] [YYYY-MM-DD] [time] [purpose] — Hearing set karo
/cancelhearing [id] — Hearing cancel karo
/calendar — Upcoming hearings dekho

📊 **Summary:**
/summary — Aaj ka overview
/weekly — Weekly summary

👤 **Profile:**
/register — Advocate registration
/profile — Apna profile dekho

💬 Sirf message bhejo — Legal advice milega automatically!"""
    await update.message.reply_text(help_text)


async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id)
    log_stat(user.id, "profile")
    lines = [
        f"👤 **Profile**",
        f"**Name:** {db_user.get('name') or 'Not set'}",
        f"**Bar Council No:** {db_user.get('bar_council_number') or 'Not set'}",
        f"**Specialization:** {db_user.get('specialization') or 'Not set'}",
        f"**Registered:** {db_user.get('registered_at', '')[:10]}",
        f"**Last Active:** {db_user.get('last_active', '')[:19] if db_user.get('last_active') else 'Now'}",
    ]
    await update.message.reply_text("\n".join(lines))


# --- Registration Conversation Handler ---
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Advocate Registration\n\nPehle apna naam bataiye:")
    return REGISTER_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text
    await update.message.reply_text(f"✅ Name: {update.message.text}\n\nAb apna Bar Council Number daalein (ya 'skip' dabayein):")
    return REGISTER_BAR


async def register_bar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["reg_bar"] = None if text.lower() == "skip" else text
    await update.message.reply_text("✅ Ab apni specialization bataiye (jaise Criminal, Civil, Family, etc.) ya 'skip':")
    return REGISTER_SPEC


async def register_spec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    spec = None if text.lower() == "skip" else text
    name = context.user_data.get("reg_name", "Advocate")
    bar = context.user_data.get("reg_bar")
    update_user(user.id, name=name, bar_council_number=bar, specialization=spec)
    log_stat(user.id, "register")
    await update.message.reply_text(
        f"✅ **Registration Complete!**\n\n"
        f"**Name:** {name}\n"
        f"**Bar Council:** {bar or 'N/A'}\n"
        f"**Specialization:** {spec or 'N/A'}\n\n"
        f"Ab aap cases create kar sakte hain — /newcase"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def register_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


register_conv = ConversationHandler(
    entry_points=[CommandHandler("register", register_start)],
    states={
        REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        REGISTER_BAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_bar)],
        REGISTER_SPEC: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_spec)],
    },
    fallbacks=[CommandHandler("cancel", register_cancel)],
)
