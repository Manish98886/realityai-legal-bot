import re
import logging
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Common Hindi/Hinglish patterns
HINDI_CHARS = re.compile(r'[\u0900-\u097F]')
HINDI_WORDS = {'hai', 'hain', 'kya', 'kaise', 'ki', 'ka', 'ke', 'ko', 'mein', 'par', 'se', 'toh',
               'bhi', 'ye', 'wo', 'aur', 'lekin', 'nahi', 'haan', 'theek', 'acha', 'bhai', 'sir',
               'karo', 'karna', 'hoga', 'sakte', 'sakta', 'diya', 'liya', 'kuch', 'sab', 'abhi',
               ' FIR', 'case', 'court', 'judge', 'lawyer', 'section', 'advocate', 'bail', 'appeal'}


def detect_language(text: str) -> str:
    """Detect if text is Hindi, Hinglish, or English."""
    if not text or not text.strip():
        return "en"

    # Check for Hindi script
    if HINDI_CHARS.search(text):
        return "hi"

    # Check for Hinglish (Roman script Hindi)
    words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    hindi_count = len(words & HINDI_WORDS)
    if hindi_count >= 2 or (hindi_count >= 1 and len(words) <= 5):
        return "hi"

    # Use langdetect for remaining cases
    try:
        result = detect(text[:500])
        if result == "hi":
            return "hi"
    except LangDetectException:
        pass

    return "en"


def get_disclaimer(lang: str = None) -> str:
    """Return legal disclaimer in appropriate language."""
    if lang == "hi":
        return "\n\n⚠️ यह AI सहायता है, योग्य वकील का विकल्प नहीं।"
    return "\n\n⚠️ This is AI assistance, not a substitute for a qualified lawyer."
