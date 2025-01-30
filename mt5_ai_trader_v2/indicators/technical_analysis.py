import pandas as pd
import pandas_ta as ta
from typing import Optional

class TechnicalAnalyzer:
    def analyze(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Calculate technical indicators"""
        print("📈 Calculating technical indicators...")
        required_columns = ['close', 'high', 'low']
        if not all(col in df.columns for col in required_columns):
            print(f"⛔ DataFrame is missing required columns: {', '.join(required_columns)}")
            return None
        
        try:
            # Ensure there's enough data to calculate indicators
            if len(df) < 20:
                print(f"⛔ Not enough data points to calculate indicators. At least 20 are required, but only {len(df)} were provided.")
                return None

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
