from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from database import get_case, get_case_with_details, log_stat
from ai_engine import ask_ai
from prompts import DRAFTING_PROMPT
from utils import split_message
import logging

logger = logging.getLogger(__name__)

DRAFT_TYPE, DRAFT_CASEID, DRAFT_DETAILS = range(3)

DOC_TYPES = {
    "bail": "Bail Application",
    "plaint": "Plaint (Civil Suit)",
    "ws": "Written Statement",
    "fir": "FIR Draft",
    "rti": "RTI Application",
    "appeal": "Appeal",
    "vakalatnama": "Vakalatnama",
    "notice": "Legal Notice",
    "agreement": "Agreement",
    "affidavit": "Affidavit",
    "complaint": "Complaint",
}

TYPE_KEYS = [["bail", "plaint", "ws"], ["fir", "rti", "appeal"], ["vakalatnama", "notice", "agreement"], ["affidavit", "complaint"]]
TYPE_KEYBOARD = ReplyKeyboardMarkup(TYPE_KEYS, one_time_keyboard=True, resize_keyboard=True)


async def draft_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_stat(update.effective_user.id, "draft_start")
    await update.message.reply_text(
        "📝 **Legal Document Drafting**\n\nDocument type select karein:",
        reply_markup=TYPE_KEYBOARD
    )
    return DRAFT_TYPE


async def draft_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text not in DOC_TYPES:
        await update.message.reply_text("Invalid type. Please select from the keyboard:", reply_markup=TYPE_KEYBOARD)
        return DRAFT_TYPE
    context.user_data["draft_type"] = text
    await update.message.reply_text(
        f"Selected: **{DOC_TYPES[text]}**\n\n"
        f"Koi existing case link karna hai? Case ID daalein ya 'no':",
        reply_markup=ReplyKeyboardRemove()
    )
    return DRAFT_CASEID


async def draft_caseid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["draft_case_id"] = None
    if text.lower() != "no":
        try:
            case_id = int(text)
            case = get_case(case_id)
            if case:
                context.user_data["draft_case_id"] = case_id
                await update.message.reply_text(f"✅ Case #{case_id} linked.\n\nAb additional details ya instructions daalein (ya 'proceed' dabayein):")
            else:
                await update.message.reply_text("Case not found. Additional details daalein (ya 'proceed'):")
        except ValueError:
            await update.message.reply_text("Additional details ya instructions daalein (ya 'proceed' dabayein):")
    else:
        await update.message.reply_text("Additional details ya instructions daalein (ya 'proceed' dabayein):")
    return DRAFT_DETAILS


async def draft_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc_type = DOC_TYPES[context.user_data["draft_type"]]
    case_details = "No case linked"
    if context.user_data.get("draft_case_id"):
        data = get_case_with_details(context.user_data["draft_case_id"])
        if data:
            c = data["case"]
            case_details = (
                f"Title: {c['title']}, Type: {c['case_type']}, Court: {c['court']}, "
                f"FIR: {c.get('fir_number')}, Sections: {c.get('sections')}, "
                f"Parties: {c.get('parties')}, Description: {c.get('description')}"
            )
    instructions = "" if update.message.text.strip().lower() == "proceed" else update.message.text
    prompt = DRAFTING_PROMPT.format(doc_type=doc_type, case_details=case_details, instructions=instructions)
    log_stat(user_id, "draft_generated", doc_type)
    await update.message.reply_text(f"📝 **{doc_type}** draft ban raha hai... ⏳")
    result = await ask_ai([{"role": "user", "content": prompt}])
    context.user_data.clear()
    for chunk in split_message(result):
        await update.message.reply_text(chunk)
    return ConversationHandler.END


async def draft_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Drafting cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


draft_conv = ConversationHandler(
    entry_points=[CommandHandler("draft", draft_start)],
    states={
        DRAFT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, draft_type)],
        DRAFT_CASEID: [MessageHandler(filters.TEXT & ~filters.COMMAND, draft_caseid)],
        DRAFT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, draft_details)],
    },
    fallbacks=[CommandHandler("cancel", draft_cancel)],
)


async def linkcase_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick link a case ID for context in next messages."""
    if not context.args:
        await update.message.reply_text("Usage: /linkcase [case_id]")
        return
    try:
        case_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid case ID.")
        return
    case = get_case(case_id)
    if not case:
        await update.message.reply_text("Case not found.")
        return
    context.user_data["linked_case_id"] = case_id
    await update.message.reply_text(f"✅ Case #{case_id} ({case['title']}) linked. Ab /draft ya chat mein is case ka context use hoga.")
