"""
app.py
------
CodeAudit — Streamlit UI
Features:
  - Manual diff input
  - GitHub PR URL auto-fetch
  - Sample diffs
  - Streaming review output
  - Review history with scores & verdicts

Run with:
    streamlit run app.py
"""

import os
import streamlit as st
from datetime import datetime

from model_client import get_client, MODELS, DEFAULT_MODEL
from reviewer import review_diff_stream
from sample_diffs import SAMPLES
from github_fetcher import fetch_pr_diff
from history_manager import (
    init_history, add_review, get_history, clear_history,
    score_color, verdict_emoji,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CodeAudit — AI Code Review",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------------------------
init_history()
if "active_history_entry" not in st.session_state:
    st.session_state.active_history_entry = None
if "loaded_diff" not in st.session_state:
    st.session_state.loaded_diff = ""
if "pr_meta" not in st.session_state:
    st.session_state.pr_meta = None

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');

  :root {
    --bg:       #0d1117;
    --surface:  #161b22;
    --surface2: #21262d;
    --border:   #30363d;
    --accent:   #58a6ff;
    --accent2:  #3fb950;
    --danger:   #f85149;
    --warn:     #d29922;
    --text:     #e6edf3;
    --muted:    #8b949e;
    --mono:     'JetBrains Mono', monospace;
    --display:  'Syne', sans-serif;
  }

  html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--display) !important;
  }

  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem !important; max-width: 1500px; }

  .hero {
    text-align: center;
    padding: 2rem 1rem 1.2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
  }
  .hero h1 {
    font-family: var(--display);
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
  }
  .hero p { color: var(--muted); font-family: var(--mono); font-size: 0.8rem; margin: 0.3rem 0 0; }

  [data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }
  [data-testid="stSidebar"] * { color: var(--text) !important; }

  .section-label {
    font-family: var(--mono);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--muted) !important;
    margin-bottom: 0.4rem;
    display: block;
  }

  .stSelectbox > div > div,
  .stTextArea textarea,
  .stTextInput input {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
  }
  .stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
  }

  .stTabs [data-baseweb="tab-list"] {
    background: var(--surface2) !important;
    border-radius: 8px !important;
    padding: 3px !important;
    gap: 2px !important;
    border: 1px solid var(--border) !important;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
    border-radius: 6px !important;
    padding: 0.4rem 1rem !important;
  }
  .stTabs [aria-selected="true"] { background: var(--accent) !important; color: white !important; }
  .stTabs [data-baseweb="tab-panel"] { padding-top: 1rem !important; }

  .stButton > button {
    background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    transition: opacity 0.15s ease;
    width: 100%;
  }
  .stButton > button:hover { opacity: 0.82 !important; }
  .stButton > button:disabled { opacity: 0.4 !important; }

  .pr-meta {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 0.8rem 1rem;
    font-family: var(--mono);
    font-size: 0.75rem;
    margin: 0.6rem 0;
  }
  .pr-meta .pr-title { font-size: 0.88rem; font-weight: 700; color: var(--text); margin-bottom: 0.4rem; font-family: var(--display); }
  .pr-pill {
    display: inline-block;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.12rem 0.55rem;
    font-size: 0.67rem;
    margin-right: 0.3rem;
    margin-top: 0.2rem;
    color: var(--muted);
  }

  .review-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.4rem 1.6rem;
    line-height: 1.7;
  }
  .review-panel h2 { color: var(--accent) !important; font-size: 1.05rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3rem; margin-top: 1.4rem; }
  .review-panel table { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 0.78rem; }
  .review-panel th { background: var(--surface2); color: var(--muted); padding: 0.35rem 0.6rem; border: 1px solid var(--border); }
  .review-panel td { padding: 0.35rem 0.6rem; border: 1px solid var(--border); vertical-align: top; }
  .review-panel code { background: var(--surface2); padding: 0.12rem 0.35rem; border-radius: 4px; font-family: var(--mono); font-size: 0.76rem; color: #79c0ff; }

  .stat-pill {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.18rem 0.7rem;
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--muted);
    margin-right: 0.3rem;
    margin-bottom: 0.4rem;
  }

  .hist-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.4rem;
  }
  .hist-card.active-card { border-color: var(--accent); border-left: 3px solid var(--accent); }
  .hist-score { font-family: var(--mono); font-size: 1rem; font-weight: 700; }
  .hist-time { font-family: var(--mono); font-size: 0.64rem; color: #6e7681; }

  .diff-hint { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); margin-top: 0.25rem; }
  .stAlert { border-radius: 6px !important; font-family: var(--mono) !important; font-size: 0.8rem !important; }
  .stSpinner > div { border-top-color: var(--accent) !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
  <h1>🧠 CodeAudit</h1>
  <p>// LLM-powered code review assistant · Groq inference · GitHub PR support · Review history</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<span class="section-label">⚙ Configuration</span>', unsafe_allow_html=True)

    api_key_input = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get a free key at console.groq.com/keys",
    )
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input

    github_token_input = st.text_input(
        "GitHub Token (optional)",
        type="password",
        placeholder="ghp_... for private repos",
        help="Optional. Needed for private repos or high-traffic usage.",
    )
    if github_token_input:
        os.environ["GITHUB_TOKEN"] = github_token_input

    st.markdown("---")
    st.markdown('<span class="section-label">🤖 Model</span>', unsafe_allow_html=True)
    model_options = {v["label"]: k for k, v in MODELS.items()}
    default_label = next(v["label"] for k, v in MODELS.items() if k == DEFAULT_MODEL)
    selected_label = st.selectbox("", list(model_options.keys()),
                                  index=list(model_options.keys()).index(default_label))
    selected_model = model_options[selected_label]

    st.markdown("---")
    st.markdown('<span class="section-label">🌡 Temperature</span>', unsafe_allow_html=True)
    temperature = st.slider("", 0.0, 1.0, 0.2, 0.05)

    st.markdown("---")
    st.markdown('<span class="section-label">📂 Sample Diffs</span>', unsafe_allow_html=True)
    sample_choice = st.selectbox("", ["— pick a sample —"] + list(SAMPLES.keys()))
    if sample_choice != "— pick a sample —":
        if st.button("Load Sample", use_container_width=True):
            st.session_state.loaded_diff = SAMPLES[sample_choice]
            st.session_state.pr_meta = None
            st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:#8b949e;line-height:1.7;">
    <b style="color:#58a6ff;">CodeAudit</b> reviews:<br>
    🐛 Bugs (High/Med/Low)<br>
    🔐 Security issues<br>
    🚨 Anti-patterns<br>
    💡 Improvement tips<br>
    📊 Score &amp; verdict<br><br>
    <b style="color:#3fb950;">Powered by Groq LPU</b><br>
    Fast · Free · No local GPU
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="large")

# Track which button was clicked and what diff to use
run_triggered = False
final_diff = ""
final_source = "manual"
final_label = "Manual Diff"

# ══════════════════════════════════════════════════════════════════════════════
# LEFT — Input tabs
# ══════════════════════════════════════════════════════════════════════════════
with col_left:
    tab_manual, tab_github = st.tabs(["📋  Paste Diff", "🔗  GitHub PR URL"])

    with tab_manual:
        diff_input = st.text_area(
            label="",
            value=st.session_state.loaded_diff,
            height=400,
            placeholder="Paste a unified diff here (git diff output, GitHub patch)...",
            key="manual_diff_area",
        )
        st.markdown('<div class="diff-hint">Standard unified diff format (git diff, GitHub PR patch)</div>',
                    unsafe_allow_html=True)

        if diff_input:
            lines = diff_input.splitlines()
            added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
            removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
            st.markdown(
                f'<div style="margin-top:0.4rem">'
                f'<span class="stat-pill">📄 {len(lines)} lines</span>'
                f'<span class="stat-pill" style="color:#3fb950">+{added} added</span>'
                f'<span class="stat-pill" style="color:#f85149">−{removed} removed</span>'
                f'</div>', unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:0.6rem'></div>", unsafe_allow_html=True)
        if st.button("🔍 Run Code Review", key="btn_manual", use_container_width=True):
            run_triggered = True
            final_diff = diff_input
            final_source = "manual"
            final_label = "Manual Diff"

    with tab_github:
        pr_url = st.text_input(
            label="",
            placeholder="https://github.com/owner/repo/pull/123",
            key="pr_url_field",
        )

        if st.button("⬇️ Fetch PR Diff", key="btn_fetch", use_container_width=True):
            if not pr_url:
                st.warning("Please enter a GitHub PR URL first.")
            else:
                with st.spinner("Fetching from GitHub API..."):
                    try:
                        pr_data = fetch_pr_diff(pr_url)
                        st.session_state.pr_meta = pr_data
                        st.success(f"✅ Fetched: PR #{pr_data['pr_number']} — {pr_data['title']}")
                    except Exception as e:
                        st.error(f"❌ {e}")
                        st.session_state.pr_meta = None

        # PR metadata card
        if st.session_state.pr_meta:
            m = st.session_state.pr_meta
            trunc = " · <span style='color:#d29922'>⚠ diff truncated</span>" if m.get("truncated") else ""
            st.markdown(f"""
            <div class="pr-meta">
              <div class="pr-title">#{m['pr_number']} — {m['title']}</div>
              <span class="pr-pill">📁 {m['repo']}</span>
              <span class="pr-pill">👤 {m['author']}</span>
              <span class="pr-pill">📂 {m['files_changed']} files</span>
              <span class="pr-pill" style="color:#3fb950">+{m['additions']}</span>
              <span class="pr-pill" style="color:#f85149">−{m['deletions']}</span>
              {trunc}
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Preview fetched diff", expanded=False):
                preview = st.session_state.pr_meta["diff"][:2500]
                if len(st.session_state.pr_meta["diff"]) > 2500:
                    preview += "\n... (preview truncated)"
                st.code(preview, language="diff")

        st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
        pr_ready = st.session_state.pr_meta is not None
        if st.button("🔍 Run Code Review", key="btn_github", use_container_width=True, disabled=not pr_ready):
            run_triggered = True
            final_diff = st.session_state.pr_meta["diff"]
            final_source = "github"
            final_label = f"PR #{st.session_state.pr_meta['pr_number']} — {st.session_state.pr_meta['repo']}"

        if not pr_ready:
            st.markdown('<div class="diff-hint">Fetch a PR first to enable the review button.</div>',
                        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT — Output & History tabs
# ══════════════════════════════════════════════════════════════════════════════
with col_right:
    history = get_history()
    tab_output, tab_history = st.tabs([
        "📊  Review Output",
        f"🕓  History  ({len(history)})",
    ])

    # ── Review Output ────────────────────────────────────────────────────
    with tab_output:
        if run_triggered:
            if not final_diff or not final_diff.strip():
                st.warning("⚠️ No diff provided. Paste one or fetch a GitHub PR.")
            elif not os.getenv("GROQ_API_KEY"):
                st.error("🔑 Groq API key missing. Add it in the sidebar.")
            else:
                try:
                    client = get_client()
                    st.markdown('<div class="review-panel">', unsafe_allow_html=True)
                    with st.spinner("CodeAudit is reviewing your diff..."):
                        review_text = st.write_stream(
                            review_diff_stream(
                                diff=final_diff,
                                model=selected_model,
                                client=client,
                                temperature=temperature,
                            )
                        )
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Auto-save to history
                    if review_text:
                        add_review(
                            diff=final_diff,
                            review=review_text,
                            model=selected_model,
                            source=final_source,
                            source_label=final_label,
                        )
                        st.session_state.active_history_entry = None

                    st.download_button(
                        label="⬇️ Download Review (.md)",
                        data=review_text or "",
                        file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.info("Check your API key and internet connection.")

        elif st.session_state.active_history_entry is not None:
            # Show a history entry selected from the History tab
            entry = st.session_state.active_history_entry
            st.markdown(
                f'<div style="font-family:var(--mono);font-size:0.7rem;color:var(--muted);margin-bottom:0.6rem;">'
                f'🕓 {entry["timestamp"].strftime("%b %d, %Y · %H:%M")} &nbsp;·&nbsp; {entry["source_label"]}'
                f'</div>', unsafe_allow_html=True,
            )
            st.markdown('<div class="review-panel">', unsafe_allow_html=True)
            st.markdown(entry["review"])
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button(
                label="⬇️ Download Review (.md)",
                data=entry["review"],
                file_name=f"code_review_{entry['id']}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            # Empty placeholder
            st.markdown("""
            <div class="review-panel" style="min-height:420px;display:flex;flex-direction:column;
                 justify-content:center;align-items:center;color:#8b949e;text-align:center;">
              <div style="font-size:2.5rem;margin-bottom:1rem;">🧠</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;line-height:2;">
                Paste a diff or fetch a GitHub PR URL<br>
                then click <b style="color:#58a6ff;">Run Code Review</b><br><br>
                <span style="font-size:0.7rem;color:#6e7681;">
                  bugs · security · anti-patterns · score
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── History tab ──────────────────────────────────────────────────────
    with tab_history:
        history = get_history()

        if not history:
            st.markdown("""
            <div style="text-align:center;padding:3rem 1rem;color:#8b949e;
                 font-family:'JetBrains Mono',monospace;font-size:0.78rem;line-height:1.9;">
              <div style="font-size:2rem;margin-bottom:0.8rem;">🕓</div>
              No reviews yet this session.<br>
              <span style="font-size:0.68rem;color:#6e7681;">
                Reviews are saved automatically after each run.
              </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                if st.button("🗑 Clear All", key="btn_clear_hist", use_container_width=True):
                    clear_history()
                    st.session_state.active_history_entry = None
                    st.rerun()
            with c2:
                avg = sum(e["score"] for e in history if e["score"]) / max(1, sum(1 for e in history if e["score"]))
                st.markdown(
                    f'<div style="font-family:var(--mono);font-size:0.7rem;color:var(--muted);padding-top:0.45rem;">'
                    f'{len(history)} reviews · avg score: <b style="color:#58a6ff">{avg:.1f}/10</b></div>',
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)

            for entry in history:
                score = entry.get("score")
                color = score_color(score)
                emoji = verdict_emoji(entry.get("verdict"))
                score_str = f"{score}/10" if score is not None else "—"
                src_icon = {"github": "🔗", "sample": "📂", "manual": "📋"}.get(entry["source"], "📋")
                is_active = (
                    st.session_state.active_history_entry is not None
                    and st.session_state.active_history_entry["id"] == entry["id"]
                )
                card_class = "hist-card active-card" if is_active else "hist-card"
                label = entry["source_label"][:48] + ("…" if len(entry["source_label"]) > 48 else "")

                st.markdown(f"""
                <div class="{card_class}">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;min-width:0;">
                      <div style="font-family:var(--mono);font-size:0.75rem;font-weight:600;
                                  color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {src_icon} {label}
                      </div>
                      <div class="hist-time">{entry['timestamp'].strftime('%H:%M:%S')} · {entry['model'].split('-instruct')[0][-20:]}</div>
                      <div style="margin-top:0.25rem;font-size:0.7rem;color:#8b949e;">
                        {emoji} {(entry.get('verdict') or 'No verdict')[:50]}
                      </div>
                    </div>
                    <div style="margin-left:0.8rem;text-align:right;flex-shrink:0;">
                      <div class="hist-score" style="color:{color};">{score_str}</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"📖 View  #{entry['id']}", key=f"view_{entry['id']}", use_container_width=True):
                    st.session_state.active_history_entry = entry
                    st.rerun()