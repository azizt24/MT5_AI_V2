import json
import os
from datetime import datetime
from typing import Dict, Any
import MetaTrader5 as mt5

class TradeLogger:
    def __init__(self):
        os.makedirs("trade_logs", exist_ok=True)  

    def log_trade(self, symbol: str, decision: Dict[str, Any], result: Dict[str, Any]):
        """Structured trade logging with local time context"""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # ✅ Uses local time
            "symbol": symbol,
            "decision": decision,
            "result": result,
            "context": {
                "balance": self._get_account_balance(),
                "market_conditions": self._get_market_state(symbol)
            }
        }
        
        self._write_log(symbol, log_entry)

    def _get_account_balance(self) -> float:
        try:
            return mt5.account_info().balance
        except Exception:
            return 0.0

    def _get_market_state(self, symbol: str) -> Dict[str, Any]:
        try:
            tick = mt5.symbol_info_tick(symbol)
            return {
                "spread": tick.ask - tick.bid,
                "last_price": tick.last
            }
        except Exception:
            return {}

    def _write_log(self, symbol: str, entry: Dict[str, Any]):
        filename = f"trade_logs/{symbol}_{datetime.now().date()}.json"  # ✅ Uses local date
        try:
            with open(filename, "a") as f:
                f.write(json.dumps(entry) + "\n")
            print(f"📄 Logged {symbol} trade: {entry['result']['status']} at {entry['timestamp']}")
        except Exception as e:
            print(f"⛔ Failed to log trade: {str(e)}")
