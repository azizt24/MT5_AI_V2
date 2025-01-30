import MetaTrader5 as mt5
from typing import Dict, Any
from config import Settings

class OrderManager:
    def __init__(self):
        self.min_lot_size = 0.01
        
    def execute_order(self, decision: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Enhanced order execution with pre-trade checks"""
        if decision['action'] == 'hold':
            return {'status': 'hold', 'symbol': symbol}
            
        try:
            self._validate_decision(decision, symbol)
            price_info = self._get_price_info(symbol, decision['action'])
            lot_size = self._calculate_position_size(symbol, decision, price_info)
            
            return self._send_order(
                symbol=symbol,
                order_type=decision['action'],
                price=price_info['price'],
                sl=decision['stop_loss'],
                tp=decision['take_profit'],
                lot_size=lot_size
            )
        except Exception as e:
            return {'status': 'error', 'symbol': symbol, 'error': str(e)}

    def _validate_decision(self, decision: Dict[str, Any], symbol: str):
        """Comprehensive decision validation"""
        if decision['stop_loss'] <= 0 or decision['take_profit'] <= 0:
            raise ValueError("Invalid price levels")
            
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise ValueError("Symbol info unavailable")
            
        point = symbol_info.point
        if point <= 0:
            raise ValueError("Invalid point value")

    def _get_price_info(self, symbol: str, action: str) -> Dict[str, float]:
        """Get current pricing with validation"""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            raise ValueError("Price data unavailable")
            
        return {
            'price': tick.ask if action == 'buy' else tick.bid,
            'spread': tick.ask - tick.bid
        }

    def _calculate_position_size(self, symbol: str, decision: Dict[str, Any], 
                               price_info: Dict[str, float]) -> float:
        """Risk-adjusted position sizing"""
        balance = mt5.account_info().balance
        risk_amount = balance * (Settings.RISK_PERCENT / 100)
        price_distance = abs(price_info['price'] - decision['stop_loss'])
        
        if price_distance <= 0:
            return self.min_lot_size
            
        pip_value = mt5.symbol_info(symbol).trade_tick_value
        lot_size = (risk_amount / price_distance) / pip_value
        
        return max(min(lot_size, mt5.symbol_info(symbol).volume_max), self.min_lot_size)

    def _send_order(self, symbol: str, order_type: str, price: float,
                  sl: float, tp: float, lot_size: float) -> Dict[str, Any]:
        """Execute validated order"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": round(lot_size, 2),
            "type": mt5.ORDER_TYPE_BUY if order_type == 'buy' else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "type_time": mt5.ORDER_TIME_GTC,
            "comment": "AI Trade"
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise ValueError(f"Order rejected: {result.comment}")
            
        return {
            'status': 'executed',
            'symbol': symbol,
            'volume': lot_size,
            'price': result.price,
            'sl': sl,
            'tp': tp
        }