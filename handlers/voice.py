import os
import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database import log_stat, get_or_create_user, add_conversation
from ai_engine import ask_ai
from utils import split_message

logger = logging.getLogger(__name__)


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages — transcribe and respond as legal query."""
    user_id = update.effective_user.id
    get_or_create_user(user_id)
    log_stat(user_id, "voice_received")

    voice = update.message.voice
    if not voice:
        return

    await update.message.reply_text("🎤 Voice note sun raha hoon... ⏳")

    try:
        # Download voice file
        tg_file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
            await tg_file.download_to_drive(tmp.name)
            tmp_path = tmp.name

        # Transcribe
        text = transcribe_audio(tmp_path)
        os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        await update.message.reply_text("❌ Voice note process nahi ho paya. Text mein puchein?")
        return

    if not text:
        await update.message.reply_text("❌ Voice se text nahi mil paya. Dobara try karein ya text likhein.")
        return

    await update.message.reply_text(f"🎤 *Aapne kaha:*\n\n\"{text}\"")

    # Process as legal query
    add_conversation(user_id, "user", text)
    from database import get_conversation_history, trim_conversation_history, check_rate_limit
    if not check_rate_limit(user_id):
        await update.message.reply_text("⏳ Rate limit. Thodi der baad phir puchein.")
        return

    history = get_conversation_history(user_id)
    result = await ask_ai(history)
    add_conversation(user_id, "assistant", result)
    trim_conversation_history(user_id)

    for chunk in split_message(result):
        await update.message.reply_text(chunk)


def transcribe_audio(file_path: str) -> str:
    """Transcribe audio file using speech_recognition."""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="hi-IN")
        return text.strip()
    except ImportError:
        logger.warning("speech_recognition not installed")
        return ""
    except sr.UnknownValueError:
        logger.warning("Speech not recognized")
        return ""
    except sr.RequestError as e:
        logger.error(f"Speech recognition API error: {e}")
        return ""
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        # Try converting ogg to wav first
        try:
            import subprocess
            wav_path = file_path.replace(".ogg", ".wav")
            subprocess.run(["ffmpeg", "-i", file_path, "-ar", "16000", "-ac", "1", wav_path],
                         capture_output=True, timeout=30)
            if os.path.exists(wav_path):
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="hi-IN")
                os.unlink(wav_path)
                return text.strip()
        except Exception:
            pass
        return ""
