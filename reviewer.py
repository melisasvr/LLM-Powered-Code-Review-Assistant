"""
reviewer.py
-----------
Core code review logic.
- Builds a rich system prompt (acts as a senior engineer persona)
- Sends the diff to Groq
- Returns structured Markdown output with bugs, security issues, anti-patterns, etc.
"""

from groq import Groq
from model_client import DEFAULT_MODEL

# ---------------------------------------------------------------------------
# System Prompt — the "fine-tuning" replacement
# Strong prompt engineering produces structured, professional reviews
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are **CodeAudit**, an elite senior software engineer and security expert with 15+ years of experience across backend, frontend, and infrastructure. Your specialty is performing meticulous, actionable code reviews on pull request diffs.

When given a code diff (unified diff / patch format), you analyze it with the following priorities:
1. Correctness and logic bugs
2. Security vulnerabilities (OWASP Top 10 awareness)
3. Performance issues
4. Code smells and anti-patterns
5. Maintainability and readability
6. Best practices for the detected language

---

## Output Format

You MUST respond with a structured Markdown report in EXACTLY this format — no deviations:

---

## 🔍 Code Review Summary

**Language/Framework Detected:** <detected language>
**Files Changed:** <list of files if identifiable>
**Diff Size:** <approximate lines added/removed>

---

## 🐛 Bugs

| Severity | Line(s) | Description | Suggested Fix |
|----------|---------|-------------|---------------|
| 🔴 High | L42 | Example: Off-by-one error in loop bound | Change `< len` to `<= len` |
| 🟡 Medium | L18 | Example: Unhandled None return | Add null check before calling `.strip()` |
| 🟢 Low | L7 | Example: Unused variable `tmp` | Remove or use the variable |

*(If no bugs found, write: ✅ No bugs detected.)*

---

## 🔐 Security Issues

| Severity | Line(s) | Vulnerability | Recommendation |
|----------|---------|--------------|----------------|
| 🔴 Critical | L55 | SQL Injection via f-string | Use parameterized queries |

*(If none: ✅ No security issues detected.)*

---

## 🚨 Anti-Patterns & Code Smells

- **[Pattern Name]** (Line X): Description of the smell and why it's problematic.
- **[Pattern Name]** (Line Y): ...

*(If none: ✅ Code follows clean patterns.)*

---

## 💡 Improvement Suggestions

1. **[Category]**: Concrete, actionable suggestion with example if helpful.
2. **[Category]**: ...

---

## 📊 Overall Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Correctness | X/10 | |
| Security | X/10 | |
| Readability | X/10 | |
| Performance | X/10 | |
| **Overall** | **X/10** | |

**Verdict:** <one of: ✅ Approve | ⚠️ Approve with Minor Changes | 🔄 Request Changes | ❌ Reject>

**Summary:** 2–3 sentence plain-English summary of the diff's quality, what it does well, and the most important thing to fix.

---

## Rules:
- Be specific: always reference line numbers when visible in the diff.
- Be actionable: every finding must have a suggested fix or next step.
- Be calibrated: don't invent problems that aren't there. If the diff is clean, say so.
- Use the severity emojis exactly as shown.
- Never truncate the output — complete every section.
"""

# ---------------------------------------------------------------------------
# Few-shot example (injected as a user/assistant pair to prime the model)
# This significantly improves output consistency without fine-tuning
# ---------------------------------------------------------------------------
FEW_SHOT_USER = """\
Review this diff:

```diff
--- a/auth.py
+++ b/auth.py
@@ -10,7 +10,10 @@ def login(username, password):
-    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
     result = db.execute(query)
     if result:
+        token = username + str(time.time())
         return {"status": "ok", "token": token}
```
"""

FEW_SHOT_ASSISTANT = """\
## 🔍 Code Review Summary

**Language/Framework Detected:** Python (Database / Auth module)
**Files Changed:** `auth.py`
**Diff Size:** ~4 lines changed

---

## 🐛 Bugs

| Severity | Line(s) | Description | Suggested Fix |
|----------|---------|-------------|---------------|
| 🟡 Medium | L13 | `token` variable used before it is defined in the `+` branch, causing a potential `NameError` if the old code path is hit | Ensure `token` is always assigned before the `return` statement |

---

## 🔐 Security Issues

| Severity | Line(s) | Vulnerability | Recommendation |
|----------|---------|--------------|----------------|
| 🔴 Critical | L11 | **SQL Injection** — the f-string interpolation is functionally identical to the string concatenation it replaces; both are vulnerable | Use parameterized queries: `db.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))` |
| 🔴 Critical | L14 | **Weak session token** — `username + timestamp` is trivially guessable and forgeable | Use `secrets.token_urlsafe(32)` and store a hashed version server-side |

---

## 🚨 Anti-Patterns & Code Smells

- **Plain-text password comparison** (L11): Passwords should never be compared in raw SQL. Use hashed passwords with `bcrypt` or `argon2`.
- **No input validation** (L10): `username` and `password` are used directly with no length or character checks.

---

## 💡 Improvement Suggestions

1. **Use an ORM or parameterized queries**: Replace raw SQL with SQLAlchemy or at minimum use `?` placeholders.
2. **Hash passwords**: Store and compare `bcrypt.checkpw(password.encode(), stored_hash)`.
3. **Secure token generation**: Replace the weak token with `secrets.token_urlsafe(32)`.
4. **Add rate limiting**: Login endpoints should be protected against brute-force attacks.

---

## 📊 Overall Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Correctness | 5/10 | Logic mostly works but token bug exists |
| Security | 1/10 | Critical SQLi and weak token |
| Readability | 6/10 | Clean structure |
| Performance | 7/10 | No issues |
| **Overall** | **3/10** | |

**Verdict:** ❌ Reject

**Summary:** This diff changes string concatenation to an f-string in a SQL query, which does not fix the underlying SQL injection vulnerability — it's equally dangerous. The new session token is cryptographically weak. Both issues are critical security flaws that must be addressed before merging.
"""


def review_diff(
    diff: str,
    model: str = DEFAULT_MODEL,
    client: Groq = None,
    temperature: float = 0.2,  # Low temp = more consistent, deterministic output
    max_tokens: int = 4096,
) -> str:
    """
    Send a code diff to Groq and return a structured Markdown review.

    Args:
        diff:        The unified diff / patch string to review.
        model:       Groq model ID (see model_client.MODELS).
        client:      Groq client instance (created if not provided).
        temperature: Lower = more consistent output. Keep at 0.1–0.3 for reviews.
        max_tokens:  Max tokens for the response (4096 is enough for most diffs).

    Returns:
        Markdown-formatted review string.
    """
    if client is None:
        from model_client import get_client
        client = get_client()

    if not diff or not diff.strip():
        return "⚠️ **Error:** Empty diff provided. Please paste a valid unified diff."

    messages = [
        # Few-shot priming: shows the model exactly what output format we expect
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        # Actual user request
        {"role": "user", "content": f"Review this diff:\n\n```diff\n{diff}\n```"},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )

    return response.choices[0].message.content


def review_diff_stream(
    diff: str,
    model: str = DEFAULT_MODEL,
    client: Groq = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
):
    """
    Streaming version of review_diff.
    Yields text chunks as they arrive — used by the Streamlit UI for live output.
    """
    if client is None:
        from model_client import get_client
        client = get_client()

    if not diff or not diff.strip():
        yield "⚠️ **Error:** Empty diff provided. Please paste a valid unified diff."
        return

    messages = [
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        {"role": "user", "content": f"Review this diff:\n\n```diff\n{diff}\n```"},
    ]

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,  # Enable streaming
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta