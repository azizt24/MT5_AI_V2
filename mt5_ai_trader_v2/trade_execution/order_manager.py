import MetaTrader5 as mt5
from typing import Dict, Any
from config import Settings  # ✅ Importing settings

class OrderManager:
    def __init__(self):
        self.fixed_lot_size = 0.1  # ✅ Fixed lot size for all trades

    def execute_order(self, decision: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Execute trade orders based on AI decisions."""
        
        if decision['action'] == 'hold':
            return {'status': 'hold', 'symbol': symbol}

        try:
            # Validate decision parameters
            self._validate_decision(decision, symbol)

            # Get current price
            price_info = self._get_price_info(symbol, decision['action'])

            # Prepare trade request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": self.fixed_lot_size,
                "type": mt5.ORDER_TYPE_BUY if decision['action'] == 'buy' else mt5.ORDER_TYPE_SELL,
                "price": price_info['price'],
                "sl": decision['stop_loss'],
                "tp": decision['take_profit'],
                "deviation": 10,
                "type_time": mt5.ORDER_TIME_GTC,
                "comment": "AI Trade"
            }

            # Send order to MT5
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Order rejected: {result.comment}")

            return {'status': 'executed', 'symbol': symbol, 'volume': self.fixed_lot_size, 'price': result.price}

        except Exception as e:
            return {'status': 'error', 'symbol': symbol, 'error': str(e)}

    def _validate_decision(self, decision: Dict[str, Any], symbol: str):
        """Check if the trade decision is valid before placing an order."""
        if decision['stop_loss'] <= 0 or decision['take_profit'] <= 0:
            raise ValueError("Invalid stop-loss or take-profit levels.")
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Symbol {symbol} information is unavailable.")

    def _get_price_info(self, symbol: str, action: str) -> Dict[str, float]:
        """Retrieve bid/ask prices for trade execution."""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            raise ValueError(f"Failed to get price data for {symbol}.")
        
        return {
            'price': tick.ask if action == 'buy' else tick.bid,
            'spread': tick.ask - tick.bid
        }

    def get_open_trade(self, symbol: str) -> Dict[str, Any]:
        """Check for existing open trades for the symbol."""
        orders = mt5.positions_get(symbol=symbol)
        if orders:
            for order in orders:
                return {
                    'order_id': order.ticket,
                    'symbol': order.symbol,
                    'volume': order.volume,
                    'price_open': order.price_open,
                    'stop_loss': order.sl,
                    'take_profit': order.tp,
                    'type': 'buy' if order.type == mt5.ORDER_TYPE_BUY else 'sell'
                }
        return {}

    def adjust_trade(self, existing_trade: Dict[str, Any], decision: Dict[str, Any]):
        """Adjust stop-loss and take-profit of an open trade."""
        if not existing_trade:
            print("⚠️ No open trade found for adjustment.")
            return

        order_id = existing_trade['order_id']
        new_stop_loss = decision['stop_loss']
        new_take_profit = decision['take_profit']

        # ✅ Check if trade is still open
        open_positions = mt5.positions_get(ticket=order_id)
        if not open_positions:
            print(f"⚠️ Trade {order_id} not found or already closed.")
            return

        # ✅ Modify existing trade
        modify_request = {
            "action": mt5.TRADE_ACTION_MODIFY,
            "position": order_id,
            "sl": new_stop_loss,
            "tp": new_take_profit,
        }

        result = mt5.order_send(modify_request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"⚠️ Failed to adjust trade {order_id}: {result.comment}")
        else:
            print(f"✅ Trade {order_id} updated: SL={new_stop_loss}, TP={new_take_profit}")
