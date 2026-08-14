"""
Section 3 — Integrated AI Quick-Add.

Contains:
  - build_parse_prompt():   role-based (system + user) message structure
  - mock_parse_task_description(): the required, keyless, deterministic
    baseline parser. Zero network calls, zero API keys. This is what
    POST /tasks/quick-add uses by default.
  - call_real_llm():        optional enhancement, only used when the
    USE_REAL_LLM environment flag is explicitly set to "true" AND an
    API key is present; falls back to the mock otherwise.
"""

import os
import re
from typing import List, Dict, Optional

# =========================================================
# Feature flag (Task 5 — optional real-LLM enhancement)
# =========================================================
USE_REAL_LLM = os.getenv("USE_REAL_LLM", "false").lower() == "true"


# =========================================================
# Task 2 — role-based prompt structure
# =========================================================
def build_parse_prompt(description: str) -> List[Dict[str, str]]:
    """
    Builds the standard role-based message list for this feature: a
    system-role instruction describing the parsing behavior expected,
    and a user-role message carrying the free-text description.

    Built (and passed through) regardless of whether the mock or a real
    model ends up answering it, so the code is structured identically
    either way.
    """
    system_message = {
        "role": "system",
        "content": (
            "You are a task-parsing assistant for the TaskFlow app. Given a "
            "free-text task description, extract exactly three fields: "
            "title (the description with any priority/date keywords "
            "removed, trimmed; use \"Untitled task\" if nothing remains), "
            "priority (exactly one of \"low\", \"medium\", \"high\"), and "
            "due_date_hint (the raw date phrase found in the text, in "
            "lower-case, or null if none is present). Respond with only "
            "those three fields."
        ),
    }
    user_message = {"role": "user", "content": description}
    return [system_message, user_message]


# =========================================================
# Task 3 — required, keyless, deterministic mock parser
# =========================================================
_GROUP_I_KEYWORDS = ["urgent", "asap"]             # -> priority = "high"
_GROUP_II_KEYWORDS = ["whenever", "low priority"]  # -> priority = "low"

_WEEKDAYS_IN_ORDER = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]
_NEXT_WEEKDAY_PHRASES = [f"next {day}" for day in _WEEKDAYS_IN_ORDER]

# Checked in this exact order; first match wins (per Task 3, step c).
_DATE_KEYWORDS_IN_ORDER = ["today", "tomorrow", "next week"] + _NEXT_WEEKDAY_PHRASES + _WEEKDAYS_IN_ORDER


def _contains_keyword(lower_text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, lower_text) is not None


def _strip_all_occurrences(text: str, keyword: str) -> str:
    """
    Removes every occurrence of `keyword` (word-boundary, case-insensitive)
    from `text`, consuming one trailing whitespace character with each
    match if present, so removals don't leave doubled internal spaces.
    """
    pattern = r"\b" + re.escape(keyword) + r"\b\s?"
    return re.sub(pattern, "", text, flags=re.IGNORECASE)


def mock_parse_task_description(description: str) -> Dict[str, Optional[str]]:
    """
    Deterministic, rule-based mock parser. Zero network calls, zero API
    keys. Any two correct implementations of this exact algorithm must
    produce identical output for any given input.

    Returns {"title": str, "priority": "low"|"medium"|"high", "due_date_hint": str|None}
    """
    # a. lower-cased working copy for keyword matching only; original-cased
    #    description is kept untouched for the title step.
    working_text = description.lower()

    # b. priority — check group (i) then group (ii), in that order; if
    #    both are present, group (i) wins. Track every matched keyword
    #    from EITHER group (not just the deciding one) for title-stripping.
    matched_priority_keywords = []
    found_group_i = False
    found_group_ii = False

    for kw in _GROUP_I_KEYWORDS:
        if _contains_keyword(working_text, kw):
            matched_priority_keywords.append(kw)
            found_group_i = True

    for kw in _GROUP_II_KEYWORDS:
        if _contains_keyword(working_text, kw):
            matched_priority_keywords.append(kw)
            found_group_ii = True

    if found_group_i:
        priority = "high"
    elif found_group_ii:
        priority = "low"
    else:
        priority = "medium"

    # c. due-date hint — checked in the fixed order above, stop at first match.
    due_date_hint = None
    for kw in _DATE_KEYWORDS_IN_ORDER:
        if _contains_keyword(working_text, kw):
            due_date_hint = kw
            break

    # d. title — start from the ORIGINAL-cased description, remove every
    #    occurrence of every matched priority keyword, plus every
    #    occurrence of the matched date phrase (if any), then strip().
    title = description
    for kw in matched_priority_keywords:
        title = _strip_all_occurrences(title, kw)
    if due_date_hint:
        title = _strip_all_occurrences(title, due_date_hint)

    title = title.strip()
    if not title:
        title = "Untitled task"

    return {
        "title": title,
        "priority": priority,
        "due_date_hint": due_date_hint,
    }


# =========================================================
# Task 5 — optional real-LLM enhancement (never required)
# =========================================================
def call_real_llm(messages: List[Dict[str, str]]) -> Dict[str, Optional[str]]:
    """
    Optional enhancement layered on top of the mock — never a
    replacement for it. Only reached when USE_REAL_LLM=true AND an API
    key is present; any failure here must fall back to the mock (see
    routers/tasks.py). Not required for grading — grading runs with the
    flag off and no key present.

    This is a minimal example wired to the Anthropic API. Swap in
    whatever provider you already have a key for.
    """
    import json
    from anthropic import Anthropic  # optional dependency — only imported here

    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=messages[0]["content"],
        messages=[{"role": "user", "content": messages[1]["content"]}],
    )
    return json.loads(response.content[0].text)


# =========================================================
# Dispatcher — the one function routers/tasks.py actually calls
# =========================================================
def parse_task_description(description: str, messages: List[Dict[str, str]]) -> Dict[str, Optional[str]]:
    """
    Uses the real LLM only when USE_REAL_LLM=true AND an API key is
    present; any failure, or the flag/key being absent, falls back to
    the required mock automatically — the endpoint never crashes and
    never requires a paid service.
    """
    if USE_REAL_LLM and os.getenv("ANTHROPIC_API_KEY"):
        try:
            return call_real_llm(messages)
        except Exception:
            return mock_parse_task_description(description)
    return mock_parse_task_description(description)