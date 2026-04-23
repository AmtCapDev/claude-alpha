import math

import pandas as pd
import yfinance as yf


def get_price_data(ticker: str, period: str = "3mo") -> dict:
    daily_prices: pd.DataFrame = yf.Ticker(ticker).history(period=period)

    if daily_prices.empty:
        raise ValueError(
            f"No price data returned for ticker {ticker!r} over period {period!r}"
        )

    n_trading_days = len(daily_prices)
    first_close = daily_prices["Close"].iloc[0]
    last_close = daily_prices["Close"].iloc[-1]

    cumulative_return = last_close / first_close - 1
    annualized_return = (1 + cumulative_return) ** (252 / n_trading_days) - 1

    daily_returns = daily_prices["Close"].pct_change().dropna()
    annualized_volatility = daily_returns.std() * math.sqrt(252)

    return {
        "daily_prices": daily_prices,
        "annualized_return": float(annualized_return),
        "annualized_volatility": float(annualized_volatility),
        "current_price": float(last_close),
        "avg_volume": float(daily_prices["Volume"].mean()),
    }


if __name__ == "__main__":
    result = get_price_data("AAPL")
    print(result["daily_prices"].tail())
    print(f"annualized_return:     {result['annualized_return'] * 100:.2f}%")
    print(f"annualized_volatility: {result['annualized_volatility'] * 100:.2f}%")
    print(f"current_price:         {result['current_price']:.2f}")
    print(f"avg_volume:            {result['avg_volume']:,.0f}")
