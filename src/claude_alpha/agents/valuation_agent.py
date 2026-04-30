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
from data.yahoo_finance import get_price_data

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


def analyze_valuation(ticker: str, risk_profile: str) -> dict:
    price_data = get_price_data(ticker)
    formatted = format_price_data(ticker, price_data)
    user_prompt = build_user_prompt(risk_profile, formatted, "Based on this data")
    return call_claude(SYSTEM_PROMPT, user_prompt)


def main() -> None:
    parser = build_arg_parser("Analyze a stock's valuation with Claude.")
    args = parser.parse_args()

    load_env_or_exit()

    ticker = args.ticker.upper()
    result = analyze_valuation(ticker, args.risk_profile)
    print_recommendation("Valuation Analysis", ticker, result)
    output_path = save_recommendation(ticker, "valuation", result)
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
