import math

import pandas as pd
import yfinance as yf


def _latest(df: pd.DataFrame, row_label: str) -> float:
    return float(df.loc[row_label].iloc[0])


def get_financials(ticker: str) -> dict:
    yf_ticker = yf.Ticker(ticker)
    income_stmt: pd.DataFrame = yf_ticker.income_stmt
    balance_sheet: pd.DataFrame = yf_ticker.balance_sheet
    cash_flow: pd.DataFrame = yf_ticker.cashflow

    if income_stmt.empty or balance_sheet.empty or cash_flow.empty:
        raise ValueError(f"No financial data returned for ticker {ticker!r}")

    revenue = _latest(income_stmt, "Total Revenue")
    net_income = _latest(income_stmt, "Net Income")
    operating_income = _latest(income_stmt, "Operating Income")
    operating_margin = operating_income / revenue

    revenue_prior = float(income_stmt.loc["Total Revenue"].iloc[1])
    revenue_growth = revenue / revenue_prior - 1

    total_debt = _latest(balance_sheet, "Total Debt")
    total_equity = _latest(balance_sheet, "Stockholders Equity")
    if total_equity == 0 or math.isnan(total_equity):
        debt_to_equity_ratio = float("nan")
    else:
        debt_to_equity_ratio = total_debt / total_equity

    if "Free Cash Flow" in cash_flow.index:
        free_cash_flow = _latest(cash_flow, "Free Cash Flow")
    else:
        operating_cash_flow = _latest(cash_flow, "Operating Cash Flow")
        capital_expenditure = _latest(cash_flow, "Capital Expenditure")
        free_cash_flow = operating_cash_flow + capital_expenditure

    return {
        "revenue": revenue,
        "net_income": net_income,
        "operating_margin": operating_margin,
        "total_debt": total_debt,
        "total_equity": total_equity,
        "debt_to_equity_ratio": debt_to_equity_ratio,
        "free_cash_flow": free_cash_flow,
        "revenue_growth": revenue_growth,
    }
