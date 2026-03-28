import json
import logging
from datetime import datetime, date
from config import MAX_MESSAGE_LENGTH, CASES_PER_PAGE

logger = logging.getLogger(__name__)


def split_message(text: str, max_length: int = None) -> list:
    """Split a long message into Telegram-compatible chunks."""
    max_len = max_length or MAX_MESSAGE_LENGTH
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at newline
        split_at = text.rfind('\n', 0, max_len)
        if split_at <= 0:
            split_at = text.rfind(' ', 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    return chunks


def escape_markdown(text: str) -> str:
    """Escape special markdown characters."""
    special = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special:
        text = text.replace(char, f'\\{char}')
    return text


def format_case_list(cases: list, page: int, total: int) -> str:
    """Format a paginated case list."""
    if not cases:
        return "कोई केस नहीं मिला।\n\nNo cases found."
    lines = [f"📋 **Cases** (Page {page}/{((total - 1) // CASES_PER_PAGE) + 1})\n"]
    for c in cases:
        status_emoji = {"active": "🟢", "closed": "🔴", "dismissed": "🟡"}.get(c["status"], "⚪")
        type_label = c.get("case_type", "N/A") or "N/A"
        updated = c.get("updated_at", "")[:10] if c.get("updated_at") else ""
        lines.append(f"{status_emoji} **#{c['case_id']}** {c['title']}")
        lines.append(f"   Type: {type_label} | Status: {c['status']} | Updated: {updated}\n")
    lines.append(f"Total: {total} cases")
    return "\n".join(lines)


def format_case_detail(data: dict) -> str:
    """Format full case details."""
    c = data["case"]
    lines = [
        f"🔍 **Case #{c['case_id']}: {c['title']}**",
        f"**Type:** {c.get('case_type') or 'N/A'}",
        f"**Status:** {c['status']}",
        f"**Court:** {c.get('court') or 'N/A'}",
        f"**FIR:** {c.get('fir_number') or 'N/A'}",
        f"**Sections:** {c.get('sections') or 'N/A'}",
        f"**Parties:** {c.get('parties') or 'N/A'}",
        f"**Description:** {c.get('description') or 'N/A'}",
        f"**Created:** {c.get('created_at', '')[:19]}",
        f"**Updated:** {c.get('updated_at', '')[:19]}",
    ]

    if data.get("hearings"):
        lines.append("\n📅 **Upcoming Hearings:**")
        for h in data["hearings"]:
            time_str = f" at {h['hearing_time']}" if h.get("hearing_time") else ""
            lines.append(f"  - {h['hearing_date']}{time_str}: {h.get('purpose', 'N/A')}")

    if data.get("evidence"):
        lines.append("\n📎 **Evidence:**")
        for e in data["evidence"]:
            status_emoji = {"collected": "✅", "submitted": "📨", "pending": "⏳"}.get(e["status"], "❓")
            lines.append(f"  {status_emoji} {e['item_name']} ({e['status']})")

    return "\n".join(lines)


def format_evidence_list(evidence: list, case_id: int) -> str:
    """Format evidence checklist."""
    if not evidence:
        return f"📎 Case #{case_id} - No evidence items yet."
    collected = sum(1 for e in evidence if e["status"] == "collected")
    submitted = sum(1 for e in evidence if e["status"] == "submitted")
    pending = sum(1 for e in evidence if e["status"] == "pending")
    lines = [f"📎 **Evidence - Case #{case_id}**"]
    lines.append(f"✅ Collected: {collected} | 📨 Submitted: {submitted} | ⏳ Pending: {pending}\n")
    for e in evidence:
        status_emoji = {"collected": "✅", "submitted": "📨", "pending": "⏳"}.get(e["status"], "❓")
        etype = f" [{e.get('item_type')}]" if e.get('item_type') else ""
        notes = f" - {e['notes']}" if e.get('notes') else ""
        lines.append(f"  {status_emoji} **#{e['id']}** {e['item_name']}{etype}{notes} ({e['status']})")
    return "\n".join(lines)


def format_hearing_calendar(hearings: list) -> str:
    """Format upcoming hearings calendar."""
    if not hearings:
        return "📅 No upcoming hearings in the next 7 days."
    lines = ["📅 **Upcoming Hearings (7 days)**\n"]
    today = date.today()
    current_date = None
    for h in hearings:
        h_date = h["hearing_date"]
        if h_date != current_date:
            current_date = h_date
            try:
                d = datetime.strptime(h_date, "%Y-%m-%d").date()
                day_label = " (Today)" if d == today else ""
            except:
                day_label = ""
            lines.append(f"📌 **{h_date}{day_label}**")
        time_str = f" at {h['hearing_time']}" if h.get('hearing_time') else ""
        lines.append(f"  → Case #{h['case_id']}: {h['title']}{time_str}")
        lines.append(f"    Purpose: {h.get('purpose', 'N/A')}\n")
    return "\n".join(lines)


def parse_json_field(text: str) -> str:
    """Safely parse a JSON field that might be stored as string."""
    if not text:
        return ""
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return ", ".join(str(x) for x in data)
        return str(data)
    except (json.JSONDecodeError, TypeError):
        return text
