"""Run the valuation agent for the team's 12-ticker universe and save
per-stock JSONs in the schema required by CLAUDE.md."""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "claude_alpha"))

from agents.valuation_agent import analyze_valuation  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "output"
TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD",
           "CRM", "ORCL", "ADBE", "ZS", "CRWD", "CSCO"]
RISK_PROFILE = "risk-neutral"
AGENT = "ValuationAnalyst"


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for ticker in TICKERS:
        try:
            raw = analyze_valuation(ticker, RISK_PROFILE)
        except Exception as exc:
            print(f"[ERROR] {ticker}: {exc}", flush=True)
            continue

        record = {
            "agent": AGENT,
            "ticker": ticker,
            "recommendation": raw["recommendation"],
            "confidence": raw["confidence"],
            "reasoning": raw["reasoning"],
            "key_factors": raw.get("key_factors", []),
            "risk_profile": RISK_PROFILE,
        }

        out_path = OUTPUT_DIR / f"{ticker}_ValuationAnalyst.json"
        out_path.write_text(json.dumps(record, indent=2))
        print(f"[OK] {ticker}: {record['recommendation']} ({record['confidence']})", flush=True)
        results.append(record)

    summary_path = OUTPUT_DIR / "_valuation_phase1_summary.json"
    summary_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved phase 1 summary: {summary_path}", flush=True)


if __name__ == "__main__":
    main()
