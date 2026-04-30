import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents._base import (
    build_arg_parser,
    build_user_prompt,
    call_claude,
    load_env_or_exit,
    print_recommendation,
    save_recommendation,
)
from data.financials import get_financials

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


def analyze_fundamentals(ticker: str, risk_profile: str) -> dict:
    financials = get_financials(ticker)
    formatted = format_financials(ticker, financials)
    user_prompt = build_user_prompt(risk_profile, formatted, "Based on these financials")
    return call_claude(SYSTEM_PROMPT, user_prompt)


def main() -> None:
    parser = build_arg_parser("Analyze a stock's fundamentals with Claude.")
    args = parser.parse_args()

    load_env_or_exit()

    ticker = args.ticker.upper()
    result = analyze_fundamentals(ticker, args.risk_profile)
    print_recommendation("Fundamental Analysis", ticker, result)
    output_path = save_recommendation(ticker, "fundamental", result)
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
