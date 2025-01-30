import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Optional
from config import Settings, Credentials
import time

class DataFetcher:
    def __init__(self):
        self.timeframe_map = {
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "D1": mt5.TIMEFRAME_D1
        }
        self.max_retries = 3
        self.retry_delay = 5
        self.connection = None
        
    def initialize(self):
        """Maintain persistent MT5 connection"""
        if not self.connection or not mt5.initialize(**Credentials.mt5()):
            self.connection = mt5.initialize(**Credentials.mt5())
            if not self.connection:
                raise ConnectionError(f"MT5 connection failed: {mt5.last_error()}")
            print(f"✅ Persistent connection established")
            
    def fetch_historical_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Robust data fetcher with connection persistence"""
        print(f"📡 Fetching {symbol} data...")
        
        for attempt in range(self.max_retries):
            try:
                self.initialize()
                
                if not self._ensure_symbol_available(symbol):
                    return None
                    
                rates = mt5.copy_rates_from_pos(
                    symbol,
                    self.timeframe_map[Settings.TIMEFRAME],
                    0,
                    Settings.DATA_BARS
                )
                
                if rates is None or rates.size == 0:
                    raise ValueError(f"No data received for {symbol}")
                    
                return self._process_rates(rates, symbol)
                
            except Exception as e:
                print(f"⛔ Attempt {attempt+1} failed: {str(e)}")
                time.sleep(self.retry_delay)
            finally:
                # Keep connection open for next symbols
                pass
                
        return None

    def _ensure_symbol_available(self, symbol: str) -> bool:
        """Advanced symbol validation with persistent Market Watch"""
        if not mt5.symbol_select(symbol, True):
            print(f"⛔ Critical: Failed to add {symbol} to Market Watch")
            return False
            
        # Verify symbol properties
        info = mt5.symbol_info(symbol)
        if not info or not info.visible:
            print(f"⛔ {symbol} not visible after selection")
            return False
            
        # Verify market data
        for _ in range(5):
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.time > 0:
                print(f"✅ Verified {symbol} market data")
                return True
            time.sleep(0.5)
            
        print(f"⛔ No market data for {symbol}")
        return False

    def _process_rates(self, rates: np.ndarray, symbol: str) -> pd.DataFrame:
        """Process rates with validation"""
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['symbol'] = symbol
        return df[['time', 'symbol', 'open', 'high', 'low', 'close', 'tick_volume']]

    def shutdown(self):
        """Proper connection cleanup"""
        if self.connection:
            mt5.shutdown()
            self.connection = None
            print("🔌 MT5 connection closed")