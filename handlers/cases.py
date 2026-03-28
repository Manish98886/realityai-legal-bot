from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from database import (
    create_case, get_user_cases, count_user_cases, get_case, get_case_with_details,
    update_case_status, delete_case, log_stat, get_or_create_user
)
from utils import format_case_list, format_case_detail, split_message
import logging

logger = logging.getLogger(__name__)

NEWCASE_TITLE, NEWCASE_TYPE, NEWCASE_COURT, NEWCASE_PARTIES, NEWCASE_FIR, NEWCASE_SECTIONS, NEWCASE_DESC = range(7)

TYPE_KEYBOARD = [["Criminal", "Civil"]]


async def newcase_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_or_create_user(update.effective_user.id)
    log_stat(update.effective_user.id, "newcase_start")
    await update.message.reply_text("📋 **New Case Creation**\n\nCase ka title daalein:")
    return NEWCASE_TITLE


async def newcase_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["case_title"] = update.message.text
    reply_markup = ReplyKeyboardMarkup(TYPE_KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Case type select karein:", reply_markup=reply_markup)
    return NEWCASE_TYPE


async def newcase_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text not in ["criminal", "civil"]:
        text = "criminal"
    context.user_data["case_type"] = text
    await update.message.reply_text("Court ka naam daalein (ya 'N/A'):", reply_markup=ReplyKeyboardRemove())
    return NEWCASE_COURT


async def newcase_court(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["case_court"] = update.message.text
    await update.message.reply_text("Parties ki details daalein (petitioner vs respondent):")
    return NEWCASE_PARTIES


async def newcase_parties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["case_parties"] = update.message.text
    await update.message.reply_text("FIR number daalein (criminal case ke liye, ya 'N/A'):")
    return NEWCASE_FIR


async def newcase_fir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["case_fir"] = update.message.text
    await update.message.reply_text("Applicable sections daalein (jaise: 498A, 304B, 376 — comma separated):")
    return NEWCASE_SECTIONS


async def newcase_sections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["case_sections"] = update.message.text
    await update.message.reply_text("Case ki brief description daalein:")
    return NEWCASE_DESC


async def newcase_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    case_id = create_case(
        user_id,
        context.user_data["case_title"],
        context.user_data["case_type"],
        context.user_data["case_court"],
        context.user_data["case_parties"],
        context.user_data["case_fir"],
        context.user_data["case_sections"],
        update.message.text
    )
    log_stat(user_id, "case_created", str(case_id))
    context.user_data.clear()
    await update.message.reply_text(
        f"✅ **Case #{case_id} created successfully!**\n\n"
        f"Ab /case {case_id} se details dekh sakte hain.\n"
        f"/strategy {case_id} se legal strategy paayein.\n"
        f"/hearing {case_id} [date] se hearing set karein."
    )
    return ConversationHandler.END


async def newcase_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Case creation cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


newcase_conv = ConversationHandler(
    entry_points=[CommandHandler("newcase", newcase_start)],
    states={
        NEWCASE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_title)],
        NEWCASE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_type)],
        NEWCASE_COURT: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_court)],
        NEWCASE_PARTIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_parties)],
        NEWCASE_FIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_fir)],
        NEWCASE_SECTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_sections)],
        NEWCASE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, newcase_desc)],
    },
    fallbacks=[CommandHandler("cancel", newcase_cancel)],
)


async def cases_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    page = 1
    if context.args:
        try:
            page = int(context.args[0])
        except ValueError:
            pass
    offset = (page - 1) * 5
    total = count_user_cases(user_id)
    cases = get_user_cases(user_id, offset=offset, limit=5)
    log_stat(user_id, "cases_list")
    text = format_case_list(cases, page, total)
    if total > 5:
        text += f"\n\n/cases {page + 1} — Next page"
    await update.message.reply_text(text)


async def case_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /case [case_id]\n\n/cases se ID dekhein.")
        return
    try:
        case_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid case ID.")
        return
    data = get_case_with_details(case_id)
    if not data or data["case"]["user_id"] != user_id:
        await update.message.reply_text("Case not found ya aapke access mein nahi hai.")
        return
    log_stat(user_id, "case_view", str(case_id))
    text = format_case_detail(data)
    for chunk in split_message(text):
        await update.message.reply_text(chunk)


async def closecase_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /closecase [case_id]")
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
    update_case_status(case_id, "closed")
    log_stat(user_id, "case_closed", str(case_id))
    await update.message.reply_text(f"✅ Case #{case_id} ({case['title']}) marked as **closed**.")


async def deletecase_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /deletecase [case_id]")
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
    delete_case(case_id)
    log_stat(user_id, "case_deleted", str(case_id))
    await update.message.reply_text(f"🗑️ Case #{case_id} ({case['title']}) permanently deleted.")
