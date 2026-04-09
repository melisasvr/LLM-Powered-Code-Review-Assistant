"""
history_manager.py
------------------
Manages review history stored in Streamlit session state.
History persists for the duration of the browser session.

Each history entry contains:
  - id: unique identifier
  - timestamp: when the review was run
  - source: "manual" | "github" | "sample"
  - source_label: human-readable label (PR URL, sample name, etc.)
  - diff: the original diff
  - review: the full review markdown
  - score: extracted overall score (float or None)
  - verdict: extracted verdict string or None
  - model: model used
"""

import re
import streamlit as st
from datetime import datetime


def init_history():
    """Initialize history list in session state if not present."""
    if "review_history" not in st.session_state:
        st.session_state.review_history = []
    if "history_counter" not in st.session_state:
        st.session_state.history_counter = 0


def extract_score(review_text: str) -> float | None:
    """
    Extract the overall score from a review markdown string.
    Looks for patterns like '**Overall** | **8.5/10**' or 'Overall | 7/10'.
    """
    patterns = [
        r"\*\*Overall\*\*\s*\|\s*\*\*([\d.]+)/10\*\*",  # **Overall** | **8.5/10**
        r"Overall\s*\|\s*([\d.]+)/10",                    # Overall | 7/10
        r"Overall.*?([\d.]+)/10",                          # Overall ... 8/10
    ]
    for pattern in patterns:
        match = re.search(pattern, review_text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def extract_verdict(review_text: str) -> str | None:
    """
    Extract the verdict line from the review.
    Looks for: Verdict: ✅ Approve | ⚠️ Approve with Minor Changes | 🔄 Request Changes | ❌ Reject
    """
    match = re.search(r"\*\*Verdict:\*\*\s*(.+?)(?:\n|$)", review_text)
    if match:
        return match.group(1).strip()
    return None


def add_review(
    diff: str,
    review: str,
    model: str,
    source: str = "manual",
    source_label: str = "Manual Diff",
) -> dict:
    """
    Add a completed review to history.

    Args:
        diff: the diff that was reviewed
        review: the full review markdown output
        model: model ID used
        source: "manual", "github", or "sample"
        source_label: display label (e.g. PR URL or sample name)

    Returns:
        The created history entry dict
    """
    init_history()
    st.session_state.history_counter += 1

    score = extract_score(review)
    verdict = extract_verdict(review)

    entry = {
        "id": st.session_state.history_counter,
        "timestamp": datetime.now(),
        "source": source,
        "source_label": source_label,
        "diff": diff,
        "review": review,
        "score": score,
        "verdict": verdict,
        "model": model,
    }

    # Prepend so newest is first
    st.session_state.review_history.insert(0, entry)
    return entry


def get_history() -> list[dict]:
    """Return the full review history list (newest first)."""
    init_history()
    return st.session_state.review_history


def clear_history():
    """Clear all review history."""
    st.session_state.review_history = []
    st.session_state.history_counter = 0


def score_color(score: float | None) -> str:
    """Return a hex color based on the score value."""
    if score is None:
        return "#8b949e"
    if score >= 8:
        return "#3fb950"   # green
    if score >= 6:
        return "#d29922"   # yellow
    return "#f85149"       # red


def verdict_emoji(verdict: str | None) -> str:
    """Return just the emoji part of the verdict."""
    if not verdict:
        return "❓"
    if "Reject" in verdict:
        return "❌"
    if "Request" in verdict:
        return "🔄"
    if "Minor" in verdict:
        return "⚠️"
    if "Approve" in verdict:
        return "✅"
    return "❓"