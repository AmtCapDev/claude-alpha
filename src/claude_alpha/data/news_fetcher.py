from datetime import datetime

import yfinance as yf


def get_news(ticker: str) -> list[dict]:
    raw = yf.Ticker(ticker).news or []
    headlines: list[dict] = []
    for item in raw:
        content = item.get("content") or {}
        pub_raw = content.get("pubDate")
        publish_date = None
        if pub_raw:
            publish_date = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
        headlines.append(
            {
                "title": content.get("title"),
                "publisher": (content.get("provider") or {}).get("displayName"),
                "link": (content.get("canonicalUrl") or {}).get("url"),
                "publish_date": publish_date,
            }
        )
    return headlines


if __name__ == "__main__":
    for article in get_news("AAPL"):
        print(f"[{article['publish_date']}] {article['publisher']}")
        print(f"  {article['title']}")
        print(f"  {article['link']}")
