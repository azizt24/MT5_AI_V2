import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime
import sys

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Settings  # Now Python will find 'config'

class DataFetcher:
    def __init__(self):
        self.symbols = Settings.SYMBOLS
        self.timeframes = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "D1": mt5.TIMEFRAME_D1
        }
        self.bars = 1000  # Number of bars to fetch
        os.makedirs("data/data", exist_ok=True)  # Ensure correct data folder

    def connect_mt5(self):
        """Connect to MetaTrader 5"""
        if not mt5.initialize():
            print("⛔ MT5 Initialization Failed")
            return False
        return True

    def fetch_historical_data(self, symbol: str, timeframe: str):
        """Fetch historical data for a given symbol & timeframe"""
        if timeframe not in self.timeframes:
            print(f"⛔ Invalid timeframe: {timeframe}")
            return None

        rates = mt5.copy_rates_from_pos(symbol, self.timeframes[timeframe], 0, self.bars)
        if rates is None:
            print(f"⛔ No data received for {symbol} on {timeframe} timeframe")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df[['open', 'high', 'low', 'close', 'tick_volume']]

    def save_data(self):
        """Fetch & save historical data for all symbols & timeframes"""
        if not self.connect_mt5():
            return

        for symbol in self.symbols:
            for tf in self.timeframes.keys():
                print(f"📊 Fetching {symbol} {tf} data...")
                df = self.fetch_historical_data(symbol, tf)
                if df is not None:
                    filename = f"data/data/{symbol}_{tf}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
                    df.to_csv(filename)
                    print(f"✅ Saved {filename}")

        mt5.shutdown()
        print("🔌 MT5 Connection Closed")

if __name__ == "__main__":
    fetcher = DataFetcher()
    fetcher.save_data()
