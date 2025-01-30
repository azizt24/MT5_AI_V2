from datetime import timedelta

class Settings:
    SYMBOLS = [
    "USDCAD",    # Standard
     "EURUSD",  
    "XAUUSD",    # Gold
     
    "USDJPY",    # Yen
     
]
    TIMEFRAME = "M15"
    RISK_PERCENT = 1.0
    MODEL_NAME = "gpt-3.5-turbo"
    DATA_BARS = 500
    LOG_DIR = "trade_logs"
    TRADE_INTERVAL = timedelta(minutes=15)
    MAX_RETRIES = 3