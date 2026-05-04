import math

import pandas as pd
import yfinance as yf


def get_price_data(ticker: str, period: str = "3mo") -> dict:
    """Fetch price history for `ticker` and compute summary stats.

    Returns the raw daily price DataFrame plus annualized return,
    annualized volatility, the most recent close, and average volume.
    """
    # Hit the Yahoo Finance API for OHLCV daily bars over the requested window.
    # `period` accepts strings like "1mo", "3mo", "1y", "5y", "max".
    daily_prices: pd.DataFrame = yf.Ticker(ticker).history(period=period)

    # yfinance returns an empty frame for bad tickers or delisted symbols
    # rather than raising — turn that into a real error so callers notice.
    if daily_prices.empty:
        raise ValueError(
            f"No price data returned for ticker {ticker!r} over period {period!r}"
        )

    # Anchor points for the period: how many bars we got, and the
    # first/last closing prices used to compute the period return.
    n_trading_days = len(daily_prices)
    first_close = daily_prices["Close"].iloc[0]
    last_close = daily_prices["Close"].iloc[-1]

    # Total return over the window, then scaled up to a 1-year figure.
    # 252 is the conventional number of US trading days per year, so
    # raising (1 + return) to the power of (252 / n_days) annualizes it.
    cumulative_return = last_close / first_close - 1
    annualized_return = (1 + cumulative_return) ** (252 / n_trading_days) - 1

    # Daily simple returns (drop the first NaN from pct_change), then
    # annualize the standard deviation by sqrt(252) — standard finance trick
    # because variance scales linearly with time, so std scales with sqrt(time).
    daily_returns = daily_prices["Close"].pct_change().dropna()
    annualized_volatility = daily_returns.std() * math.sqrt(252)

    # Bundle everything the analyst agents need downstream. Cast numpy
    # scalars to plain floats so the dict is JSON-serializable.
    return {
        "daily_prices": daily_prices,
        "annualized_return": float(annualized_return),
        "annualized_volatility": float(annualized_volatility),
        "current_price": float(last_close),
        "avg_volume": float(daily_prices["Volume"].mean()),
    }
