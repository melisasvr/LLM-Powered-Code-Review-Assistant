"""
cli_review.py
-------------
Quick CLI tool for testing the reviewer from the terminal.
No Streamlit needed — great for rapid iteration.

Usage:
    python cli_review.py                        # interactive prompt
    python cli_review.py --sample 1             # run sample diff #1
    python cli_review.py --file my_patch.diff   # review a diff file
    python cli_review.py --model llama-3.1-8b-instant  # pick model
"""

import argparse
import sys
from model_client import get_client, MODELS, DEFAULT_MODEL
from reviewer import review_diff
from sample_diffs import SAMPLES


def print_models():
    print("\nAvailable models:")
    for model_id, info in MODELS.items():
        tag = " ← default" if info["recommended"] else ""
        print(f"  {model_id:<45} {info['label']}{tag}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="CodeAudit CLI — LLM-powered code review",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--sample", type=int, help="Load a sample diff by number (1–4)")
    parser.add_argument("--file", type=str, help="Path to a .diff or .patch file")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Groq model ID to use")
    parser.add_argument("--list-models", action="store_true", help="List available models and exit")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature (default: 0.2)")
    args = parser.parse_args()

    if args.list_models:
        print_models()
        sys.exit(0)

    # ── Load diff content ──────────────────────────────────────────────────
    diff = None

    if args.sample:
        sample_list = list(SAMPLES.items())
        if args.sample < 1 or args.sample > len(sample_list):
            print(f"❌ Sample must be 1–{len(sample_list)}")
            sys.exit(1)
        name, diff = sample_list[args.sample - 1]
        print(f"\n📋 Using sample: {name}")

    elif args.file:
        try:
            with open(args.file, "r") as f:
                diff = f.read()
            print(f"\n📂 Loaded: {args.file}")
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            sys.exit(1)

    else:
        # Interactive paste mode
        print("\n🧠 CodeAudit CLI — Paste your diff below.")
        print("   (Type or paste the diff, then press Ctrl+D / Ctrl+Z to submit)\n")
        print("─" * 60)
        try:
            diff = sys.stdin.read()
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)

    if not diff or not diff.strip():
        print("❌ Empty diff. Nothing to review.")
        sys.exit(1)

    # ── Run review ────────────────────────────────────────────────────────
    print(f"\n🤖 Model: {args.model}")
    print(f"🌡  Temperature: {args.temperature}")
    print("─" * 60)
    print("⏳ Reviewing...\n")

    try:
        client = get_client()
        review = review_diff(diff, model=args.model, client=client, temperature=args.temperature)
        print(review)
        print("\n" + "─" * 60)
        print("✅ Review complete.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()