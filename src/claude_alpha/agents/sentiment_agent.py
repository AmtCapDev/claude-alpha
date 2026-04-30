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
from data.news_fetcher import get_news

SYSTEM_PROMPT = (
    "You are a sentiment equity analyst. Your primary responsibility is to "
    "analyze financial news, analyst ratings, and disclosures related to a "
    "stock. Assess the overall sentiment, identify key themes such as "
    "earnings, executive changes, analyst upgrades or downgrades, and insider "
    "activity. Consider whether the sentiment is likely already priced in."
)


def format_news(ticker: str, articles: list[dict]) -> str:
    if not articles:
        return f"Ticker: {ticker}\n\nNo recent news articles available for this ticker."

    lines = [f"Ticker: {ticker}", f"Articles retrieved: {len(articles)}", ""]
    for i, article in enumerate(articles, start=1):
        date = article.get("publish_date")
        date_str = date.strftime("%Y-%m-%d") if date else "unknown date"
        publisher = article.get("publisher") or "unknown publisher"
        title = article.get("title") or "(no title)"
        link = article.get("link") or ""
        lines.append(f"{i}. [{date_str}] {publisher}")
        lines.append(f"   {title}")
        if link:
            lines.append(f"   {link}")
        lines.append("")
    return "\n".join(lines).rstrip()


def no_news_result(ticker: str) -> dict:
    return {
        "recommendation": "SELL",
        "confidence": "low",
        "reasoning": (
            f"No recent news articles could be retrieved for {ticker}, so a "
            "sentiment-driven thesis cannot be supported. Without catalysts, "
            "analyst commentary, or disclosures to lean on, there is no "
            "informational edge on the long side.\n\n"
            "In the absence of evidence, defaulting to a low-conviction SELL "
            "avoids taking sentiment-based risk that cannot be justified. A "
            "fundamentals or valuation view should drive any actual position "
            "decision here, not this agent."
        ),
        "key_factors": [
            "No news articles returned by the data source",
            "Unable to assess catalysts or themes",
            "No analyst actions or disclosures observed",
            "Low-conviction default in the absence of signal",
        ],
    }


def analyze_sentiment(ticker: str, risk_profile: str) -> dict:
    articles = get_news(ticker)
    if not articles:
        return no_news_result(ticker)

    formatted = format_news(ticker, articles)
    user_prompt = build_user_prompt(risk_profile, formatted, "Based on this news coverage")
    return call_claude(SYSTEM_PROMPT, user_prompt)


def main() -> None:
    parser = build_arg_parser("Analyze a stock's news sentiment with Claude.")
    args = parser.parse_args()

    load_env_or_exit()

    ticker = args.ticker.upper()
    result = analyze_sentiment(ticker, args.risk_profile)
    print_recommendation("Sentiment Analysis", ticker, result)
    output_path = save_recommendation(ticker, "sentiment", result)
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
