### indicators/trend_analysis.py
import pandas as pd

def detect_trend(df):
    """Identify strong uptrends/downtrends using moving averages."""
    df["trend"] = "Neutral"
    df.loc[df["ema_20"] > df["ema_50"], "trend"] = "Bullish"
    df.loc[df["ema_20"] < df["ema_50"], "trend"] = "Bearish"
    return df