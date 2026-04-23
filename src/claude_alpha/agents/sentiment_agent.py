import argparse
import json
import os
import re
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.news_fetcher import get_news

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "output"

MODEL = "claude-sonnet-4-20250514"

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


def extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(0))

    raise ValueError(f"Could not find JSON object in response:\n{text}")


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
    user_message = (
        f"Risk profile: {risk_profile}\n\n"
        f"{formatted}\n\n"
        "Based on this news coverage, respond with ONLY a JSON object (no "
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
    print(f"\n=== Sentiment Analysis: {ticker} ===")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence:     {result['confidence']}")
    print("\nKey Factors:")
    for factor in result.get("key_factors", []):
        print(f"  - {factor}")
    print("\nReasoning:")
    print(result["reasoning"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a stock's news sentiment with Claude.")
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
    result = analyze_sentiment(ticker, args.risk_profile)
    print_recommendation(ticker, result)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{ticker}_sentiment.json"
    output_path.write_text(json.dumps(result, indent=2))
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
