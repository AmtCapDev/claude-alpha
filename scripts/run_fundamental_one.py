"""Run the fundamental agent for a single ticker, save in CLAUDE.md schema."""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "claude_alpha"))

from agents.fundamental_agent import analyze_fundamentals  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "output"
RISK_PROFILE = "risk-neutral"
AGENT = "FundamentalAnalyst"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_fundamental_one.py TICKER")
    ticker = sys.argv[1].upper()

    load_dotenv(PROJECT_ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{ticker}_FundamentalAnalyst.json"
    if out_path.exists():
        print(f"[SKIP] {ticker}: already exists", flush=True)
        return

    raw = analyze_fundamentals(ticker, RISK_PROFILE)
    record = {
        "agent": AGENT,
        "ticker": ticker,
        "recommendation": raw["recommendation"],
        "confidence": raw["confidence"],
        "reasoning": raw["reasoning"],
        "key_factors": raw.get("key_factors", []),
        "risk_profile": RISK_PROFILE,
    }
    out_path.write_text(json.dumps(record, indent=2))
    print(f"[OK] {ticker}: {record['recommendation']} ({record['confidence']})", flush=True)


if __name__ == "__main__":
    main()
