import json
import re
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import text  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.core.exceptions import ValidationError
from config.settings import GROQ_API_KEY, GROQ_MODEL_PRIMARY

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# System prompt to restrict the AI and provide context
SYSTEM_PROMPT = """
You are the "Horizon AI Assistant", a friendly and helpful data expert for the
Horizon Cinemas Booking System (HCBS).
Your goal is to help managers and staff understand cinema operations and data.

PERSONALITY:
- Be helpful, warm, and professional.
- Refer to yourself as the "Horizon Assistant".
- Engage naturally in basic conversation (greetings, "how are you", thanking, etc.).

GUARDRAILS:
1. For data questions, ONLY answer based on Horizon Cinemas data and the provided schema.
2. If a user asks a totally unrelated general question (e.g., "cooking tips"),
   politely bridge back to your cinema role.
3. If the input is a simple greeting or non-query (e.g., "hi", "thanks"), respond
   with a warm, friendly message without immediately mentioning data constraints.
3. You have access to the database schema of HCBS.

SCHEMA CONTEXT:
{schema}

When a user asks a DATA-DRIVEN question:
1. Generate an optimized MySQL SELECT query to fetch the data.
2. Return ONLY the SQL query inside <sql></sql> tags.
3. Do NOT use any destructive commands (DELETE, UPDATE, DROP, etc.).
"""

SUMMARY_PROMPT = """
You are the Horizon AI Assistant, a friendly cinema data analyst.
Based on the user's question and the raw data provided, write a warm,
human-like, and helpful summary.

FORMATTING RULES:
1. Use HTML tags for structure (e.g., <b>, <ul>, <li>, <i>).
2. For lists of data, use <ul> and <li>.
3. If there are many values, you can use a simple <table>.
4. Avoid markdown (like ** or *) - use HTML instead.
5. If the data is empty, explain it kindly.

USER QUESTION: {query}
RAW DATA: {data}
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


async def call_groq(messages: List[Dict[str, str]], model: str = GROQ_MODEL_PRIMARY) -> str:
    """Sends a request to the Groq API."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,  # Low temperature for consistent SQL generation
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GROQ_URL, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"]


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

    messages.append({"role": "user", "content": f"Generate SQL for: {user_query}"})

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
    except Exception as e:
        answer = f"I generated a query but it failed to execute: {str(e)}"
        if session_id:
            add_message(db, session_id, "assistant", answer)
        return {
            "answer": answer,
            "sql": generated_sql,
        }

    # 3. Summarize Result
    summary_messages = [
        {"role": "system", "content": "You are a professional cinema analyst."},
        {
            "role": "user",
            "content": SUMMARY_PROMPT.format(query=user_query, data=json.dumps(rows, default=str)),
        },
    ]

    summary = await call_groq(summary_messages, model=GROQ_MODEL_PRIMARY)

    # Save assistant message to session
    if session_id:
        add_message(db, session_id, "assistant", summary)

        # If this is the first message (history empty), update title based on result
        if not history or len(history) == 0:
            title = user_query[:40] + "..." if len(user_query) > 40 else user_query
            update_session_title(db, session_id, title)

    return {"answer": summary, "sql": generated_sql, "data_count": len(rows)}
