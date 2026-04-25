import json
import re
from typing import Dict, List

from backend.services.ai_service import call_groq

SUGGESTION_PROMPT = """You are a cinema analytics assistant. \
Based on the conversation below, suggest exactly 4 short follow-up questions the user might want to ask next.

Rules:
- Max 6 words each
- Relevant to what was just discussed, or useful cinema topics if no history
- Return ONLY a JSON array of 4 strings, nothing else

Example: ["Top films this month", "Staff performance", "Occupancy rate", "Weekly revenue"]

CONVERSATION:
{history}"""


async def get_dynamic_suggestions(history: List[Dict[str, str]]) -> List[str]:
    """Generates 4 dynamic follow-up suggestions based on chat context."""
    history_text = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in history[-4:]])

    prompt = SUGGESTION_PROMPT.format(history=history_text or "No history yet.")

    try:
        response = await call_groq(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        match = re.search(r"\[.*\]", response, re.DOTALL)
        if match:
            suggestions = json.loads(match.group(0))
            return suggestions[:4]
    except Exception:
        pass

    return ["Weekly Revenue", "Staff Performance", "Occupancy Rate", "Top Films"]
