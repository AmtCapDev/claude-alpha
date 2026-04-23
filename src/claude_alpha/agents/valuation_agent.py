import argparse
import json
import os
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.yahoo_finance import get_price_data

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "output"

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You are a valuation equity analyst. Your primary responsibility is to "
    "analyze valuation trends of a given stock. Analyze historical price data, "
    "volume data, annualized return, and annualized volatility. Identify trends "
    "and patterns. Assess whether the stock appears overvalued, undervalued, or "
    "fairly valued. Consider the risk/return profile."
)


def format_price_data(ticker: str, data: dict) -> str:
    daily_prices = data["daily_prices"]
    price_table = daily_prices[["Open", "High", "Low", "Close", "Volume"]].to_string(
        float_format=lambda x: f"{x:,.2f}"
    )

    return (
        f"Ticker: {ticker}\n"
        f"Current price: ${data['current_price']:,.2f}\n"
        f"Annualized return: {data['annualized_return'] * 100:.2f}%\n"
        f"Annualized volatility: {data['annualized_volatility'] * 100:.2f}%\n"
        f"Average daily volume: {data['avg_volume']:,.0f}\n"
        f"Trading days in sample: {len(daily_prices)}\n\n"
        f"Daily price history:\n{price_table}"
    )


def extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(0))

    raise ValueError(f"Could not find JSON object in response:\n{text}")


def analyze_valuation(ticker: str, risk_profile: str) -> dict:
    price_data = get_price_data(ticker)
    formatted = format_price_data(ticker, price_data)

    user_message = (
        f"Risk profile: {risk_profile}\n\n"
        f"{formatted}\n\n"
        "Based on this data, respond with ONLY a JSON object (no prose, no "
        "code fences) with exactly these fields:\n"
        '  - "recommendation": either "BUY" or "SELL"\n'
        '  - "confidence": one of "high", "medium", "low"\n'
        '  - "reasoning": 2-3 paragraph string explaining your analysis\n'
        '  - "key_factors": list of 3-5 short strings naming the drivers'
    )

    client = Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = "".join(block.text for block in response.content if block.type == "text")
    return extract_json(raw_text)


def print_recommendation(ticker: str, result: dict) -> None:
    print(f"\n=== Valuation Analysis: {ticker} ===")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence:     {result['confidence']}")
    print("\nKey Factors:")
    for factor in result.get("key_factors", []):
        print(f"  - {factor}")
    print("\nReasoning:")
    print(result["reasoning"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a stock's valuation with Claude.")
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument(
        "--risk-profile",
        default="risk-neutral",
        help="Risk profile to include in the prompt (default: risk-neutral)",
    )
    args = parser.parse_args()

    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in.")

    ticker = args.ticker.upper()
    result = analyze_valuation(ticker, args.risk_profile)
    print_recommendation(ticker, result)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{ticker}_valuation.json"
    output_path.write_text(json.dumps(result, indent=2))
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
