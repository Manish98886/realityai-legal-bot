import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "z-ai/glm-5-turbo")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/lawyer_bot.db")

REMINDER_ENABLED = os.getenv("REMINDER_ENABLED", "true").lower() == "true"
REMINDER_DAYS_BEFORE = int(os.getenv("REMINDER_DAYS_BEFORE", "2"))

MAX_AI_CALLS_PER_HOUR = 20
CONVERSATION_HISTORY_LIMIT = 10
CASES_PER_PAGE = 5
MAX_MESSAGE_LENGTH = 4096
