import os

import pandas as pd
import yfinance as yf
from anthropic import Anthropic
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in.")

    client = Anthropic()
    ticker = yf.Ticker("AAPL")
    hist: pd.DataFrame = ticker.history(period="5d")
    print(hist.tail())
    print(f"anthropic client ready: {client.__class__.__name__}")


if __name__ == "__main__":
    main()
