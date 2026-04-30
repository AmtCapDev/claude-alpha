import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "claude_alpha"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "claude_alpha" / "agents"))

from agents.fundamental_agent import analyze_fundamentals

OUTPUT_DIR = PROJECT_ROOT / "output"

TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "CRM", "ORCL", "ADBE", "ZS", "CRWD", "CSCO"]
RISK = "risk-averse"
AGENT_NAME = "FundamentalAnalyst"


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for ticker in TICKERS:
        try:
            raw = analyze_fundamentals(ticker, RISK)
        except Exception as exc:
            print(f"[{ticker}] ERROR: {exc}", flush=True)
            continue

        record = {
            "agent": AGENT_NAME,
            "ticker": ticker,
            "recommendation": raw.get("recommendation"),
            "confidence": raw.get("confidence"),
            "reasoning": raw.get("reasoning"),
            "key_factors": raw.get("key_factors", []),
            "risk_profile": RISK,
        }
        out_path = OUTPUT_DIR / f"{ticker}_{AGENT_NAME}.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        results.append(record)
        print(f"[{ticker}] {record['recommendation']} ({record['confidence']})", flush=True)

    summary_path = OUTPUT_DIR / f"{AGENT_NAME}_phase1.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved {len(results)} recommendations to {summary_path}", flush=True)


if __name__ == "__main__":
    main()
