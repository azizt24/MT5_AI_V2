import pandas as pd
import pandas_ta as ta
from typing import Optional

class TechnicalAnalyzer:
    def analyze(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Calculate technical indicators"""
        print("📈 Calculating technical indicators...")
        try:
            # Momentum indicators
            df['rsi'] = ta.rsi(df['close'], length=14)
            
            # Trend indicators
            df['ema20'] = ta.ema(df['close'], length=20)
            df['ema50'] = ta.ema(df['close'], length=50)
            
            # Volatility indicators
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
            
            # MACD
            macd = ta.macd(df['close'])
            df = pd.concat([df, macd], axis=1)
            
            print("✅ Technical analysis complete")
            return df.dropna()
            
        except Exception as e:
            print(f"⛔ Indicator calculation failed: {str(e)}")
            return None