### backtesting/backtest.py
import pandas as pd

def backtest_strategy(data):
    """Evaluate trading strategy on historical data."""
    capital = 10000
    for index, row in data.iterrows():
        if row["trend"] == "Bullish":
            capital *= 1.02  # Assume 2% profit per trade
        elif row["trend"] == "Bearish":
            capital *= 0.98  # Assume 2% loss per trade
    return capital