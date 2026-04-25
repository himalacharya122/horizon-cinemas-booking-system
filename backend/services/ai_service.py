# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import text  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

log = logging.getLogger(__name__)

from backend.core.exceptions import ValidationError
from config.settings import GROQ_API_KEY, GROQ_MODEL_PRIMARY

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are Horizon, an AI assistant built into the Horizon Cinemas Booking System (HCBS). \
You help cinema managers and staff explore their data through natural conversation.

PERSONALITY:
- Talk like a knowledgeable colleague, not a formal report writer.
- Be concise and direct — no "Welcome to..." or "Here are the results:" openers.
- Answer the way a person would, not like a system generating a report.

BEHAVIOUR:
- For greetings or casual chat, respond warmly in 1-2 sentences only.
- For data questions, generate a MySQL SELECT query wrapped in <sql></sql> tags.
- Only SELECT queries — never modify, delete, or create data.
- If a question is completely unrelated to cinema operations, politely steer back.

DATABASE SCHEMA:
{schema}
"""

SUMMARY_PROMPT = """You are Horizon, an AI assistant for cinema managers. \
Answer the user's question naturally based on the data below.

RULES:
- Write like a person talking, not a report. Skip all preamble ("Based on the data...", \
"Here are the results:", "Welcome to...").
- Get straight to the point. Example: "Spider-Man: No Way Home brought in £28.80 across 3 bookings."
- Use <b> to emphasise key names and numbers.
- Use <ul>/<li> only if there are 3 or more items to list.
- Use <table> only when comparing multiple attributes across 5+ rows — not for simple lists.
- For 1-2 items, write 1-2 natural sentences — no table needed.
- Always use £ for currency. Never use $.
- If the data is empty, say so briefly (e.g., "No bookings found for that period.").
- Keep it concise unless the data genuinely warrants more detail.

QUESTION: {query}
DATA: {data}
"""


def _get_schema_context() -> str:
    """Loads the schema from database/schema.sql to provide context to the LLM."""
    try:
        from pathlib import Path

        schema_path = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"
        with open(schema_path, "r") as f:
            return f.read()
    except Exception:
        return (
            "Schema unavailable. Assume tables: cities, cinemas, screens, seats, "
            "users, films, listings, showings, bookings, booked_seats."
        )


def validate_sql(sql: str):
    """
    Strict validation to ensure the generated SQL is safe and read-only.
    """
    forbidden_keywords = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "GRANT",
        "REVOKE",
        "REPLACE",
        "SET",
        "USE",
    ]

    clean_sql = sql.strip().upper()

    if not clean_sql.startswith("SELECT") and not clean_sql.startswith("WITH"):
        raise ValidationError(
            "AI generated an invalid query type. Only SELECT queries are allowed."
        )

    for kw in forbidden_keywords:
        # Use word boundaries to avoid catching words like 'UpdateAt'
        pattern = rf"\b{kw}\b"
        if re.search(pattern, clean_sql):
            raise ValidationError(f"AI generated a restricted query containing: {kw}")


async def call_groq(
    messages: List[Dict[str, str]],
    model: str = GROQ_MODEL_PRIMARY,
    temperature: float = 0.1,
    max_retries: int = 4,
) -> str:
    """
    Send a request to the Groq API.
    On 429 (rate-limit), read the Retry-After header and wait before retrying.
    Retries up to max_retries times with exponential back-off as a fallback.
    """
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        for attempt in range(max_retries):
            resp = await client.post(GROQ_URL, headers=headers, json=payload)

            if resp.status_code == 429:
                # Groq returns Retry-After in seconds (may be fractional)
                retry_after_raw = resp.headers.get("retry-after") or resp.headers.get(
                    "x-ratelimit-reset-requests"
                )
                try:
                    wait = float(retry_after_raw) + 0.5
                except (TypeError, ValueError):
                    # Fallback: exponential back-off (2s, 4s, 8s, …)
                    wait = 2.0 ** (attempt + 1)

                log.warning(
                    "Groq 429 on attempt %d/%d — waiting %.1fs before retry.",
                    attempt + 1,
                    max_retries,
                    wait,
                )
                await asyncio.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    raise RuntimeError(
        "Groq rate limit: all retries exhausted. Please wait a moment and try again."
    )


async def execute_ai_query(
    db: Session,
    user_query: str,
    history: Optional[List[Dict[str, str]]] = None,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Main entry point for AI analytics:
    1. Generates SQL from natural language.
    2. Validates and executes SQL.
    3. Summarizes the results.
    4. Saves messages to session if provided.
    """
    from backend.services.ai_sessions_service import add_message, update_session_title

    schema = _get_schema_context()

    # If session provided, save user message
    if session_id:
        add_message(db, session_id, "user", user_query)

    # 1. Generate SQL
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(schema=schema)},
    ]

    # Add limited history for context
    if history:
        messages.extend(history[-6:])  # Keep last 3 turns

    messages.append({"role": "user", "content": user_query})

    ai_response = await call_groq(messages)

    # Extract SQL
    sql_match = re.search(r"<sql>(.*?)</sql>", ai_response, re.DOTALL)
    generated_sql = None

    if not sql_match:
        # Fallback if tags are missing but looks like SQL
        if "SELECT" in ai_response.upper():
            generated_sql = ai_response.strip()
            # Summary not needed if it's just a refusal or talk
        else:
            answer = ai_response
            if session_id:
                add_message(db, session_id, "assistant", answer)
            return {"answer": answer, "data": None}
    else:
        generated_sql = sql_match.group(1).strip()

    # 2. Validate and Execute
    validate_sql(generated_sql)

    try:
        result = db.execute(text(generated_sql))
        rows = [dict(row._mapping) for row in result.all()]
    except Exception:
        answer = "Sorry, I had trouble fetching that data. Could you try rephrasing the question?"
        if session_id:
            add_message(db, session_id, "assistant", answer)
        return {"answer": answer}

    # 3. Summarize Result — brief pause so the two calls don't hit back-to-back
    await asyncio.sleep(0.4)

    summary_messages = [
        {"role": "system", "content": "You are a professional cinema analyst."},
        {
            "role": "user",
            "content": SUMMARY_PROMPT.format(query=user_query, data=json.dumps(rows, default=str)),
        },
    ]

    summary = await call_groq(summary_messages, model=GROQ_MODEL_PRIMARY, temperature=0.4)

    # Save assistant message to session
    if session_id:
        add_message(db, session_id, "assistant", summary)

        # If this is the first message (history empty), update title based on result
        if not history or len(history) == 0:
            title = user_query[:40] + "..." if len(user_query) > 40 else user_query
            update_session_title(db, session_id, title)

    return {"answer": summary, "sql": generated_sql, "data_count": len(rows)}
