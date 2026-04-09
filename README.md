# 🧠 CodeAudit — LLM-Powered Code Review Assistant

> A portfolio-grade AI tool that reviews GitHub-style PR diffs and produces structured, actionable feedback powered by Groq's ultra-fast inference API.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-orange?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

---

## ✨ What It Does

Paste any unified diff (from `git diff`, GitHub PRs, etc.) and get back a **structured code review** in seconds:

| Section | Details |
|---|---|
| 🐛 **Bugs** | Severity (High/Medium/Low), line numbers, suggested fixes |
| 🔐 **Security Issues** | OWASP-aware vulnerability detection |
| 🚨 **Anti-Patterns** | Code smells, bad practices, style issues |
| 💡 **Suggestions** | Concrete improvement recommendations |
| 📊 **Score & Verdict** | Dimension scores (1–10) + Approve/Reject verdict |

---

## 🏗️ Project Structure

```
code-review-assistant/
├── app.py              # Streamlit UI — paste diff or fetch GitHub PR
├── reviewer.py         # Core logic: system prompt + Groq API call
├── model_client.py     # Groq client initialization + model registry
├── github_fetcher.py   # GitHub PR URL → unified diff fetcher
├── history_manager.py  # Session-based review history with scores
├── sample_diffs.py     # Sample diffs for testing & demo
├── cli_review.py       # CLI runner (no UI needed)
├── requirements.txt    # Dependencies
├── .env.example        # API key template
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & install
```bash
git clone https://github.com/your-username/code-review-assistant
cd code-review-assistant
pip install -r requirements.txt
```

### 2. Set up your API key
```bash
cp .env.example .env
# Edit .env and paste your Groq key:
# GROQ_API_KEY=gsk_...
```
Get a **free** key at [console.groq.com/keys](https://console.groq.com/keys)

### 3. Launch the UI
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🔗 GitHub PR URL Feature

Paste any **public GitHub PR URL** directly into CodeAudit — no copy-pasting diffs needed:

```
https://github.com/psf/requests/pull/6710
https://github.com/tiangolo/fastapi/pull/11879
```

CodeAudit fetches the diff automatically via the GitHub API and shows:
- PR title, author, repo
- Files changed, lines added/removed
- Collapsible diff preview
- Then runs the full AI review with one click

> **Private repos**: Add a `GITHUB_TOKEN` in the sidebar for access.

---

## 🖥️ CLI Usage

```bash
# Run on a sample diff
python cli_review.py --sample 1

# Review a patch file
python cli_review.py --file my_changes.diff

# Use a specific model
python cli_review.py --sample 2 --model qwen-qwq-32b

# List available models
python cli_review.py --list-models

# Interactive paste mode
python cli_review.py
```

---

## 🤖 Supported Models (via Groq)

| Model | Quality | Speed | Best For |
|---|---|---|---|
| `llama-3.3-70b-versatile` | ⭐⭐⭐⭐⭐ | Fast | Best overall reviews |
| `qwen-qwq-32b` | ⭐⭐⭐⭐⭐ | Fast | Strong code reasoning |
| `deepseek-r1-distill-llama-70b` | ⭐⭐⭐⭐ | Fast | Chain-of-thought analysis |
| `llama-3.1-8b-instant` | ⭐⭐⭐ | Ultra-fast | Quick/cheap checks |

All models run on **Groq's LPU hardware** — no local GPU needed.

---

## 🧠 How It Works (No Fine-Tuning!)

Instead of expensive fine-tuning, this project uses smart prompt engineering:

1. **Rich system prompt** — CodeAudit persona with explicit structured output instructions
2. **Few-shot examples** — A worked example is injected into every request to anchor the output format
3. **Low temperature (0.2)** — Reduces hallucinations, keeps reviews consistent
4. **Structured output spec** — The prompt mandates exact Markdown tables and sections

This approach matches the quality of fine-tuned models for structured tasks at **zero training cost**.

---

## 🧪 Testing Your Setup

```bash
# Quick smoke test — reviews a sample diff in the terminal
python cli_review.py --sample 1

# Test all 4 built-in sample diffs
python sample_diffs.py
```

---

## 💡 Extending This Project

| Idea | How |
|---|---|
| LoRA fine-tuning | Use `peft` + `trl` on a PR diff dataset from GitHub |
| Persistent history | Store reviews in SQLite instead of session state |
| Export to PDF | Use `weasyprint` or `pdfkit` |
| Batch review | Loop `review_diff()` over multiple diffs |
| GitHub Actions bot | Post CodeAudit reviews as PR comments automatically |
| VS Code extension | Wrap the CLI into a VS Code sidebar panel |

---

## 📦 Requirements

```
groq>=0.9.0
streamlit>=1.35.0
python-dotenv>=1.0.0
requests>=2.31.0
```

Python 3.11+ recommended.

---

## 🤝 Contributing

Contributions are welcome and appreciated! Here's how to get started:

### Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/code-review-assistant
   cd code-review-assistant
   ```
3. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** and test them:
   ```bash
   python cli_review.py --sample 1   # quick test
   streamlit run app.py              # UI test
   ```
5. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add support for GitLab MR URLs."
   ```
6. **Push** and open a **Pull Request** against `main`

### Contribution Ideas

- 🌐 Add support for GitLab or Bitbucket MR URLs
- 🌍 Add multi-language UI support
- 🗄️ Persistent review history with SQLite
- 📤 Export reviews to PDF or HTML
- 🤖 GitHub Actions bot that posts reviews as PR comments
- 🎨 UI themes (light mode, high contrast)
- 📊 Review analytics dashboard

### Code Style

- Follow **PEP 8** for Python code
- Add **docstrings** to all functions
- Keep modules **single-responsibility** (one file per concern)
- Write **comments** for non-obvious logic

### Reporting Issues

Found a bug or have a feature request? [Open an issue](https://github.com/your-username/code-review-assistant/issues) with:
- A clear title and description
- Steps to reproduce (for bugs)
- Expected vs. actual behavior
- Your Python version and OS

---

## 📄 License

```
MIT License

Copyright (c) 2026 CodeAudit Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including, without limitation, the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">
  <p>Built with ❤️ using Groq · Streamlit · Python</p>
  <p>⭐ Star this repo if you found it useful!</p>
</div>
