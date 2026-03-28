import os
import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database import get_case, save_document, log_stat, get_or_create_user
from ai_engine import ask_ai
from prompts import DOCUMENT_ANALYSIS_PROMPT
from utils import split_message

logger = logging.getLogger(__name__)


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded documents (PDF, images)."""
    user_id = update.effective_user.id
    get_or_create_user(user_id)
    doc = update.message.document or update.message.photo
    if not doc:
        return

    # Get file
    if update.message.document:
        file = update.message.document
        file_id = file.file_id
        file_name = file.file_name or "document"
        mime = file.mime_type or ""
    elif update.message.photo:
        # Get largest photo
        file = update.message.photo[-1]
        file_id = file.file_id
        file_name = "photo.jpg"
        mime = "image/jpeg"
    else:
        return

    await update.message.reply_text(f"📄 Document received: {file_name}\nAnalyzing... ⏳")

    # Download file
    text_content = ""
    try:
        tg_file = await context.bot.get_file(file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1] or ".tmp") as tmp:
            await tg_file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        # Extract text based on file type
        if "pdf" in mime or file_name.lower().endswith(".pdf"):
            text_content = extract_pdf_text(tmp_path)
        elif "image" in mime or file_name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")):
            text_content = extract_image_text(tmp_path)

        os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Document download/extract error: {e}")
        await update.message.reply_text("❌ Document process karne mein error aaya.")
        return

    if not text_content or len(text_content.strip()) < 10:
        await update.message.reply_text(
            "❌ Document se text extract nahi ho paya. Kya ye scanned document hai?\n"
            "Handwritten ya poor quality scanned documents mein OCR kam kaam karta hai."
        )
        return

    # Analyze with AI
    prompt = DOCUMENT_ANALYSIS_PROMPT.format(document_text=text_content[:6000])
    # Check for linked case
    case_id = context.user_data.get("linked_case_id")
    if not case_id and context.args:
        try:
            case_id = int(context.args[0])
        except (ValueError, IndexError):
            pass

    analysis = await ask_ai([{"role": "user", "content": prompt}])
    if analysis:
        # Save to DB
        save_document(case_id, user_id, file_id, file_name, mime, doc_type="legal_document", analysis=analysis[:10000])
        log_stat(user_id, "document_analyzed", f"{file_name}:{case_id}")

    for chunk in split_message(analysis):
        await update.message.reply_text(chunk)


def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""


def extract_image_text(file_path: str) -> str:
    """Extract text from image using OCR."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang='hin+eng')
        return text.strip()
    except ImportError:
        logger.warning("pytesseract or Pillow not installed")
        return ""
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""
