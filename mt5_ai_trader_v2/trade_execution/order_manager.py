import MetaTrader5 as mt5
from typing import Dict, Any
from config import Settings
from ai_engine.openai_trader import AITrader

class OrderManager:
    def __init__(self):
        self.ai_trader = AITrader()
        self.lot_size = 0.1  # Fixed lot size

    def execute_order(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade orders based on AI decisions."""
        decision = self.ai_trader.analyze_market(market_data)
        
        if decision['action'] == 'hold':
            return {'status': 'hold', 'symbol': market_data['symbol']}

        try:
            price_info = self._get_price_info(market_data['symbol'], decision['action'])
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": market_data['symbol'],
                "volume": self.lot_size,
                "type": mt5.ORDER_TYPE_BUY if decision['action'] == 'buy' else mt5.ORDER_TYPE_SELL,
                "price": price_info['price'],
                "sl": decision['stop_loss'],
                "tp": decision['take_profit'],
                "deviation": 10,
                "type_time": mt5.ORDER_TIME_GTC,
                "comment": "AI Trade"
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Order rejected: {result.comment}")
            
            return {'status': 'executed', 'symbol': market_data['symbol'], 'price': result.price, 'volume': self.lot_size}

        except Exception as e:
            return {'status': 'error', 'symbol': market_data['symbol'], 'error': str(e)}

    def _get_price_info(self, symbol: str, action: str) -> Dict[str, float]:
        """Retrieve bid/ask prices for trade execution."""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            raise ValueError(f"Failed to get price data for {symbol}.")
        return {'price': tick.ask if action == 'buy' else tick.bid}
