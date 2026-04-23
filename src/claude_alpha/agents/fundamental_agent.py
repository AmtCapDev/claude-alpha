import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.financials import get_financials

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "output"

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You are a fundamental financial equity analyst. Your primary "
    "responsibility is to analyze a company's financial statements including "
    "income, balance sheet, and cash flow. Evaluate revenue growth, "
    "profitability trends, debt levels, and cash flow health. Compare metrics "
    "year over year to identify improving or deteriorating trends. Base your "
    "analysis solely on the financial data provided."
)


def _fmt_dollars(value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"${value:,.0f}"


def _fmt_pct(value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{value * 100:.2f}%"


def _fmt_ratio(value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{value:.2f}"


def format_financials(ticker: str, data: dict) -> str:
    return (
        f"Ticker: {ticker}\n\n"
        "Income Statement:\n"
        f"  Revenue (latest FY):       {_fmt_dollars(data['revenue'])}\n"
        f"  Revenue growth YoY:        {_fmt_pct(data['revenue_growth'])}\n"
        f"  Net income:                {_fmt_dollars(data['net_income'])}\n"
        f"  Operating margin:          {_fmt_pct(data['operating_margin'])}\n\n"
        "Balance Sheet:\n"
        f"  Total debt:                {_fmt_dollars(data['total_debt'])}\n"
        f"  Total stockholders equity: {_fmt_dollars(data['total_equity'])}\n"
        f"  Debt-to-equity ratio:      {_fmt_ratio(data['debt_to_equity_ratio'])}\n\n"
        "Cash Flow:\n"
        f"  Free cash flow:            {_fmt_dollars(data['free_cash_flow'])}"
    )


def extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(0))

    raise ValueError(f"Could not find JSON object in response:\n{text}")


def analyze_fundamentals(ticker: str, risk_profile: str) -> dict:
    financials = get_financials(ticker)
    formatted = format_financials(ticker, financials)

    user_message = (
        f"Risk profile: {risk_profile}\n\n"
        f"{formatted}\n\n"
        "Based on these financials, respond with ONLY a JSON object (no "
        "prose, no code fences) with exactly these fields:\n"
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
    print(f"\n=== Fundamental Analysis: {ticker} ===")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence:     {result['confidence']}")
    print("\nKey Factors:")
    for factor in result.get("key_factors", []):
        print(f"  - {factor}")
    print("\nReasoning:")
    print(result["reasoning"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a stock's fundamentals with Claude.")
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
    result = analyze_fundamentals(ticker, args.risk_profile)
    print_recommendation(ticker, result)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{ticker}_fundamental.json"
    output_path.write_text(json.dumps(result, indent=2))
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
