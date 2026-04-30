"""Run SentimentAnalyst over the 12-ticker universe and save per-stock JSON files."""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "claude_alpha"))

from agents.sentiment_agent import analyze_sentiment  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "output"
TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD",
           "CRM", "ORCL", "ADBE", "ZS", "CRWD", "CSCO"]
RISK_PROFILE = "risk-averse"
AGENT_NAME = "SentimentAnalyst"


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []

    for ticker in TICKERS:
        print(f"\n--- {ticker} ---", flush=True)
        try:
            result = analyze_sentiment(ticker, RISK_PROFILE)
        except Exception as e:
            print(f"ERROR for {ticker}: {e}", flush=True)
            result = {
                "recommendation": "SELL",
                "confidence": "low",
                "reasoning": f"Analysis failed for {ticker}: {e}. Defaulting to low-conviction SELL.",
                "key_factors": ["Analysis error", "No usable signal", "Default low-conviction call"],
            }

        record = {
            "agent": AGENT_NAME,
            "ticker": ticker,
            "recommendation": result["recommendation"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "key_factors": result.get("key_factors", []),
            "risk_profile": RISK_PROFILE,
        }

        out_path = OUTPUT_DIR / f"{ticker}_{AGENT_NAME}.json"
        out_path.write_text(json.dumps(record, indent=2))
        print(f"Saved {out_path} | {record['recommendation']} ({record['confidence']})", flush=True)
        summary.append({
            "ticker": ticker,
            "recommendation": record["recommendation"],
            "confidence": record["confidence"],
            "key_factors": record["key_factors"],
        })

    summary_path = OUTPUT_DIR / "sentiment_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\nSummary saved: {summary_path}", flush=True)


if __name__ == "__main__":
    main()
