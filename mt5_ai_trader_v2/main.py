import MetaTrader5 as mt5
import pandas as pd
import time
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
        print("\n🔎 Persistent symbol verification:")
        for symbol in Settings.SYMBOLS:
            try:
                if self.data_fetcher._ensure_symbol_available(symbol):
                    tick = mt5.symbol_info_tick(symbol)
                    print(
                        f"   - {symbol}: Available\n"
                        f"     Bid: {tick.bid:.5f} | Ask: {tick.ask:.5f}\n"
                        f"     Spread: {(tick.ask - tick.bid)*10000:.1f} pips"
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
        """Process all symbols in sequence with error isolation"""
        for symbol in Settings.SYMBOLS:
            try:
                print(f"\n⚙️ Processing {symbol}")
                data = self.data_fetcher.fetch_historical_data(symbol)
                if data is not None:
                    decision = self._make_trading_decision(data)
                    result = self.order_manager.execute_order(decision, symbol)
                    self.trade_logger.log_trade(symbol, decision, result)
            except Exception as e:
                print(f"⚠️ Non-critical error processing {symbol}: {str(e)}")

    def _make_trading_decision(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Trading decision pipeline (add your AI/strategy here)"""
        # Placeholder for actual decision-making logic
        return {
            'action': 'hold',
            'stop_loss': 0.0,
            'take_profit': 0.0,
            'confidence': 0.0,
            'reasoning': 'Default safety decision'
        }

    def _sleep_until_next_cycle(self, start_time: datetime):
        """Precision timing control with dynamic sleep adjustment"""
        elapsed = (datetime.now() - start_time).total_seconds()
        sleep_time = Settings.TRADE_INTERVAL.total_seconds() - elapsed
        if sleep_time > 0:
            print(f"\n⏳ Next trading cycle in {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        else:
            print(f"\n⚠️ Cycle overrun by {-sleep_time:.1f} seconds")

    def _cleanup_resources(self):
        """Ensure proper resource cleanup"""
        print("\n🧹 Cleaning up resources...")
        mt5.shutdown()
        print("✅ Resources released")

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()