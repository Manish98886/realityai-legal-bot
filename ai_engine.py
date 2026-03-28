import httpx
import logging
from typing import Optional
from config import (
    AI_PROVIDER, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL,
    GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are RealityAi Legal Agent — a highly experienced, professional, and expert AI legal assistant with over 50 years of combined experience in Indian law.

You are an expert in both Criminal and Civil cases. You know IPC, CrPC, CPC, Evidence Act, Specific Relief Act, Contract Act, and all major judgments deeply.

Your job is to act exactly like a senior advocate who has fought thousands of cases.

Core Rules:
- Always think step-by-step like a senior lawyer
- Give practical, court-ready advice
- Suggest strong arguments, weaknesses, and counter-strategies
- Help in drafting (plaint, written statement, bail application, FIR, RTI, appeal, Vakala Nama, etc.)
- Track case timeline, next hearing, evidence, and important dates
- Be 100% professional, precise, and honest
- Never give guarantee of winning — always say "this is strong strategy based on facts"
- Always reply in the same language the user uses (Hindi/English/Mixed)
- Always add disclaimer at the end: "⚠️ यह AI सहायता है, योग्य वकील का विकल्प नहीं।"

When lawyer gives a case:
- Ask for all important details (FIR number, sections, court, parties, evidence, timeline)
- Analyse the case
- Give clear strategy: how to fight, what arguments to use, what documents needed
- Suggest possible excuses/defences
- Draft necessary applications/documents

You are not a replacement for a lawyer; you are their powerful intelligent assistant."""


async def call_openrouter(messages: list, model: str = None) -> Optional[str]:
    model = model or OPENROUTER_MODEL
    if not OPENROUTER_API_KEY:
        logger.warning("OpenRouter API key not set")
        return None
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://realityai.lawyer",
                    "X-Title": "RealityAi Lawyer Bot",
                },
                json={"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 4096},
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"OpenRouter response ok (model={model})")
            return content
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return None


async def call_gemini(messages: list, model: str = None) -> Optional[str]:
    model = model or GEMINI_MODEL
    if not GEMINI_API_KEY:
        logger.warning("Gemini API key not set")
        return None
    try:
        gemini_messages = []
        for msg in messages:
            gemini_messages.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
                json={"contents": gemini_messages, "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096}},
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Gemini response ok (model={model})")
            return content
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return None


async def call_groq(messages: list, model: str = None) -> Optional[str]:
    model = model or GROQ_MODEL
    if not GROQ_API_KEY:
        logger.warning("Groq API key not set")
        return None
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 4096},
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"Groq response ok (model={model})")
            return content
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None


async def ask_ai(user_messages: list, system_prompt: str = None) -> Optional[str]:
    """Call AI with fallback chain: OpenRouter -> Gemini -> Groq"""
    system = system_prompt or SYSTEM_PROMPT
    full_messages = [{"role": "system", "content": system}] + user_messages

    provider_order = ["openrouter"]
    if AI_PROVIDER == "gemini":
        provider_order.insert(0, "gemini")
    elif AI_PROVIDER == "groq":
        provider_order.insert(0, "groq")
    # Ensure all fallbacks present
    for p in ["openrouter", "gemini", "groq"]:
        if p not in provider_order:
            provider_order.append(p)

    for provider in provider_order:
        if provider == "openrouter":
            result = await call_openrouter(full_messages)
        elif provider == "gemini":
            # Gemini uses different format, rebuild messages
            result = await call_gemini(full_messages)
        elif provider == "groq":
            result = await call_groq(full_messages)
        else:
            continue
        if result:
            return result

    logger.error("All AI providers failed")
    return "माफ़ कीजिए, AI सेवा अभी उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।"
