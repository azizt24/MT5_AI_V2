### data/preprocess.py
import pandas as pd

def preprocess_market_data(df):
    """Clean and structure market data."""
    df = df.dropna()
    df["returns"] = df["close"].pct_change()
    df["volatility"] = df["returns"].rolling(window=10).std()
    df.dropna(inplace=True)
    return df