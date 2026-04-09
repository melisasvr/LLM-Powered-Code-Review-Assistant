"""
github_fetcher.py
-----------------
Fetches unified diffs from GitHub Pull Request URLs.
Works with public repos — no GitHub token required.
For private repos, set GITHUB_TOKEN in your .env file.
"""

import re
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# GitHub API base
GITHUB_API = "https://api.github.com"


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """
    Parse a GitHub PR URL into (owner, repo, pr_number).

    Supports formats:
      https://github.com/owner/repo/pull/123
      https://github.com/owner/repo/pull/123/files
    
    Returns:
        (owner, repo, pr_number) tuple
    
    Raises:
        ValueError if the URL format is not recognized
    """
    url = url.strip().rstrip("/")
    pattern = r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(
            f"Could not parse GitHub PR URL: {url}\n"
            "Expected format: https://github.com/owner/repo/pull/123"
        )
    owner, repo, pr_num = match.groups()
    return owner, repo, int(pr_num)


def fetch_pr_diff(url: str) -> dict:
    """
    Fetch the unified diff for a GitHub Pull Request.

    Args:
        url: Full GitHub PR URL

    Returns:
        dict with keys:
          - diff (str): unified diff content
          - title (str): PR title
          - description (str): PR body
          - author (str): PR author login
          - pr_number (int): PR number
          - repo (str): owner/repo
          - url (str): original PR URL
          - files_changed (int): number of files changed
          - additions (int): lines added
          - deletions (int): lines deleted

    Raises:
        ValueError: for bad URLs or API errors
        requests.HTTPError: for HTTP failures
    """
    owner, repo, pr_number = parse_pr_url(url)

    # Build headers — add token if available for higher rate limits
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CodeAudit-App/1.0",
    }
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    # ── 1. Fetch PR metadata ────────────────────────────────────────────
    meta_url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    meta_resp = requests.get(meta_url, headers=headers, timeout=15)

    if meta_resp.status_code == 404:
        raise ValueError(
            f"PR not found: {owner}/{repo}#{pr_number}\n"
            "Make sure the repo is public and the PR number is correct."
        )
    elif meta_resp.status_code == 403:
        raise ValueError(
            "GitHub API rate limit exceeded. "
            "Add a GITHUB_TOKEN to your .env file for higher limits."
        )
    meta_resp.raise_for_status()
    meta = meta_resp.json()

    # ── 2. Fetch the unified diff ───────────────────────────────────────
    diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
    diff_resp = requests.get(meta_url, headers=diff_headers, timeout=30)
    diff_resp.raise_for_status()
    diff_content = diff_resp.text

    if not diff_content.strip():
        raise ValueError("This PR has no diff content (possibly already merged or empty).")

    # ── 3. Truncate very large diffs to avoid token limits ──────────────
    MAX_DIFF_CHARS = 12_000  # ~3000 tokens — safe for all Groq models
    truncated = False
    if len(diff_content) > MAX_DIFF_CHARS:
        diff_content = diff_content[:MAX_DIFF_CHARS]
        # Try to cut at a clean line boundary
        last_newline = diff_content.rfind("\n")
        if last_newline > MAX_DIFF_CHARS * 0.8:
            diff_content = diff_content[:last_newline]
        diff_content += "\n\n[... diff truncated for length — showing first ~300 lines ...]"
        truncated = True

    return {
        "diff": diff_content,
        "title": meta.get("title", "Unknown"),
        "description": meta.get("body") or "",
        "author": meta.get("user", {}).get("login", "unknown"),
        "pr_number": pr_number,
        "repo": f"{owner}/{repo}",
        "url": url,
        "files_changed": meta.get("changed_files", 0),
        "additions": meta.get("additions", 0),
        "deletions": meta.get("deletions", 0),
        "state": meta.get("state", "unknown"),
        "truncated": truncated,
    }