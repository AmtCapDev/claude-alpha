# ValuationAnalyst agent: pulls price/volume data, asks Claude to judge whether
# the stock looks over-, under-, or fairly valued, then writes a JSON verdict.
import sys
from pathlib import Path

# Add the parent `claude_alpha` package to sys.path so we can import sibling
# modules (`agents._base`, `data.yahoo_finance`) when running this file directly
# from the project root, e.g. `python src/claude_alpha/agents/valuation_agent.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Shared helpers live in _base.py — every analyst agent uses the same plumbing
# for CLI args, prompt assembly, the Claude API call, and writing output JSON.
from agents._base import (
    build_arg_parser,  # argparse setup: ticker + --risk-profile flags
    build_user_prompt,  # wraps the data block + risk profile into the user turn
    call_claude,  # sends system+user prompt to Claude, parses JSON reply
    load_env_or_exit,  # loads ANTHROPIC_API_KEY from .env, exits if missing
    print_recommendation,  # pretty-prints the verdict to the terminal
    save_recommendation,  # writes output/{TICKER}_{agent}.json
)

# Yahoo Finance helper — returns a dict with daily OHLCV plus precomputed
# annualized return, annualized volatility, current price, and avg volume.
from data.yahoo_finance import get_price_data

# The system prompt defines the agent's persona for Claude. This is what makes
# this agent a "valuation analyst" instead of a sentiment or fundamentals one —
# the persona is the only thing that really differs across the three agents.
SYSTEM_PROMPT = (
    "You are a valuation equity analyst. Your primary responsibility is to "
    "analyze valuation trends of a given stock. Analyze historical price data, "
    "volume data, annualized return, and annualized volatility. Identify trends "
    "and patterns. Assess whether the stock appears overvalued, undervalued, or "
    "fairly valued. Consider the risk/return profile."
)


def format_price_data(ticker: str, data: dict) -> str:
    """Turn the raw price-data dict into a plain-text block Claude can read."""
    # Render the OHLCV DataFrame as a clean text table — LLMs handle plain text
    # tables much better than nested JSON for this kind of tabular data.
    daily_prices = data["daily_prices"]
    price_table = daily_prices[["Open", "High", "Low", "Close", "Volume"]].to_string(
        float_format=lambda x: f"{x:,.2f}"
    )

    # Lead with the headline numbers (current price, annualized return/vol),
    # then the full daily history. Returns/vol are stored as decimals (0.23),
    # so we multiply by 100 to display as percentages.
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
    """Full pipeline for one ticker: fetch data → format → prompt Claude → return verdict."""
    # 1. Pull price/volume history from Yahoo Finance.
    price_data = get_price_data(ticker)
    # 2. Convert the DataFrame + stats into a text block for the prompt.
    formatted = format_price_data(ticker, price_data)
    # 3. Wrap that block with the risk profile and an instruction phrase.
    user_prompt = build_user_prompt(risk_profile, formatted, "Based on this data")
    # 4. Send to Claude with the valuation-analyst persona; returns parsed JSON
    #    matching the schema in CLAUDE.md (recommendation, confidence, etc.).
    return call_claude(SYSTEM_PROMPT, user_prompt)


def main() -> None:
    # CLI entry point — lets us run `python valuation_agent.py AAPL --risk-profile risk-averse`.
    parser = build_arg_parser("Analyze a stock's valuation with Claude.")
    args = parser.parse_args()

    # Read ANTHROPIC_API_KEY from .env; exit cleanly if it's not set.
    load_env_or_exit()

    # Normalize the ticker (yfinance is case-sensitive on some symbols).
    ticker = args.ticker.upper()
    result = analyze_valuation(ticker, args.risk_profile)
    # Print the verdict to stdout, then persist it to output/{TICKER}_valuation.json.
    print_recommendation("Valuation Analysis", ticker, result)
    output_path = save_recommendation(ticker, "valuation", result)
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
