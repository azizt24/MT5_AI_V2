import MetaTrader5 as mt5
import pandas as pd
import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
from config import Settings, Credentials
from data.fetch_data import DataFetcher
from trade_execution.order_manager import OrderManager
from monitoring.logger import TradeLogger

class TradingBot:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.order_manager = OrderManager()
        self.trade_logger = TradeLogger()
        self._verify_environment()

    def _verify_environment(self):
        """Persistent environment verification"""
        print("\n🔍 Running system verification...")
        try:
            self.data_fetcher.initialize()
            terminal_info = mt5.terminal_info()
            print(f"✅ Connected to {terminal_info.company}")
            self._check_symbol_availability()
        except Exception as e:
            raise RuntimeError(f"System verification failed: {str(e)}")

    def _check_symbol_availability(self):
        """Persistent symbol verification"""
        print("\n🔎 Checking symbol availability:")
        for symbol in Settings.SYMBOLS:
            try:
                if self.data_fetcher._ensure_symbol_available(symbol):
                    tick = mt5.symbol_info_tick(symbol)
                    print(
                        f"   - {symbol}: Available\n"
                        f"     Bid: {tick.bid:.5f} | Ask: {tick.ask:.5f}\n"
                        f"     Spread: {(tick.ask - tick.bid) * 10000:.1f} pips"
                    )
            except Exception as e:
                print(f"⛔ Symbol check failed for {symbol}: {str(e)}")

    def run(self):
        """Main trading loop with connection persistence"""
        try:
            print(f"\n🚀 Starting AI Trading Bot ({Settings.TRADE_INTERVAL} interval)")
            print(f"📈 Trading symbols: {', '.join(Settings.SYMBOLS)}")
            print(f"⚖️ Risk management: {Settings.RISK_PERCENT}% per trade\n")

            while True:
                cycle_start = datetime.now()
                self._process_trading_cycle()
                self._sleep_until_next_cycle(cycle_start)

        except KeyboardInterrupt:
            print("\n🛑 Graceful shutdown initiated")
        finally:
            self.data_fetcher.shutdown()

    def _process_trading_cycle(self):
        """Monitor market and adjust trades dynamically"""

        for symbol in Settings.SYMBOLS:
            try:
                print(f"\n⚙️ Checking {symbol}...")

                # Fetch market data
                data = self.data_fetcher.fetch_historical_data(symbol)
                if data is None:
                    continue

                # Get AI trading decision
                decision = self._make_trading_decision(data)

                # Monitor existing trades
                existing_trade = self.order_manager.get_open_trade(symbol)
                if existing_trade:
                    # Adjust Stop-Loss/Take-Profit dynamically
                    self.order_manager.adjust_trade(existing_trade, decision)
                    continue  # Skip opening new trade

                # Open a new trade
                result = self.order_manager.execute_order(decision, symbol)
                self.trade_logger.log_trade(symbol, decision, result)

            except Exception as e:
                print(f"⚠️ Error processing {symbol}: {str(e)}")

    def _make_trading_decision(self, data: pd.DataFrame) -> Dict[str, Any]:
        """AI-based strategy selection and trade decision-making."""
    
        if len(data) < 50:
            return {'action': 'hold', 'stop_loss': 0.0, 'take_profit': 0.0, 'confidence': 0.0, 'reasoning': 'Insufficient data'}

        last_row = data.iloc[-1]

        # Get Indicators
        ema_20 = last_row['ema20']
        ema_50 = last_row['ema50']
        rsi = last_row['rsi']
        atr = last_row['atr']
        adx = last_row['adx']
        boll_upper = last_row['bollinger_upper']
        boll_lower = last_row['bollinger_lower']
        price = last_row['close']

        # Dynamic Risk Management
        risk_multiplier = 1.5
        stop_loss = price - (risk_multiplier * atr)
        take_profit = price + (risk_multiplier * atr)

        # 1️⃣ Trend-Following Strategy (EMA Crossover + ADX)
        if ema_20 > ema_50 and adx > 25 and rsi > 50:
            return {
                'action': 'buy',
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': 0.85,
                'reasoning': 'Strong bullish trend with EMA crossover & ADX > 25'
            }
        elif ema_20 < ema_50 and adx > 25 and rsi < 50:
            return {
                'action': 'sell',
                'stop_loss': price + (risk_multiplier * atr),
                'take_profit': price - (risk_multiplier * atr),
                'confidence': 0.85,
                'reasoning': 'Strong bearish trend with EMA crossover & ADX > 25'
            }

        # 2️⃣ Mean Reversion Strategy (Bollinger Bands)
        if price <= boll_lower and rsi < 30:
            return {
                'action': 'buy',
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': 0.75,
                'reasoning': 'Price at lower Bollinger Band & RSI < 30 (Oversold)'
            }
        elif price >= boll_upper and rsi > 70:
            return {
                'action': 'sell',
                'stop_loss': price + (risk_multiplier * atr),
                'take_profit': price - (risk_multiplier * atr),
                'confidence': 0.75,
                'reasoning': 'Price at upper Bollinger Band & RSI > 70 (Overbought)'
            }

        # 3️⃣ Breakout Strategy (ATR + Price Action)
        if atr > atr.mean() * 1.5:
            return {
                'action': 'buy' if rsi > 50 else 'sell',
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': 0.8,
                'reasoning': 'High ATR breakout detected'
            }

        return {
            'action': 'hold',
            'stop_loss': 0.0,
            'take_profit': 0.0,
            'confidence': 0.5,
            'reasoning': 'No clear signal'
        }

    def _sleep_until_next_cycle(self, start_time: datetime):
     """Real-time countdown timer until the next trading cycle starts."""
    
     elapsed = (datetime.now() - start_time).total_seconds()
     sleep_time = Settings.TRADE_INTERVAL.total_seconds() - elapsed
    
     if sleep_time > 0:
         print("\n⏳ Next trading cycle in:", end=" ", flush=True)
         for remaining in range(int(sleep_time), 0, -1):
             sys.stdout.write(f"\r⏳ Next cycle starts in {remaining} seconds...  ")
             sys.stdout.flush()
             time.sleep(1)
         print("\r🚀 Starting next trading cycle now!               ")
     else:
        print(f"\n⚠️ Cycle overrun by {-sleep_time:.1f} seconds")

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
