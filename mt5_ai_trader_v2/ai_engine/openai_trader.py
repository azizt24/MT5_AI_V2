# ai_engine/openai_trader.py
import openai
import json
import time
from typing import Dict, Any
from pydantic import BaseModel, ValidationError, validator
from config import Settings, Credentials

class TradeDecision(BaseModel):
    action: str  # buy, sell, hold
    stop_loss: float
    take_profit: float
    confidence: float
    reasoning: str

    @validator('action')
    def valid_action(cls, v):
        if v not in ('buy', 'sell', 'hold'):
            raise ValueError('Invalid trading action')
        return v

    @validator('stop_loss', 'take_profit')
    def valid_prices(cls, v, values):
        if values.get('action', 'hold') != 'hold' and v <= 0:
            raise ValueError('Positive price levels required for active trades')
        return round(v, 5)  # Round to 5 decimal places for FX pairs

    @validator('confidence')
    def valid_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return round(v, 2)

class AITrader:
    def __init__(self):
        openai.api_key = Credentials.openai()
        self.model = Settings.MODEL_NAME
        self.max_retries = 3
        self.retry_delay = 2
        self.min_rr_ratio = 1.5  # Minimum risk/reward ratio
        
    def analyze_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-driven trading decisions with robust validation"""
        print(f"🤖 [AI] Analyzing {data.get('symbol', 'Unknown')} market...")
        
        for attempt in range(self.max_retries):
            try:
                decision = self._get_ai_decision(data)
                self._validate_decision(data['close'], decision)
                return decision
                
            except ValidationError as e:
                print(f"⛔ Validation error (attempt {attempt+1}): {str(e)}")
            except Exception as e:
                print(f"⛔ API error (attempt {attempt+1}): {str(e)}")
                
            time.sleep(self.retry_delay)
            
        return self._safe_decision()

    def _get_ai_decision(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get and process AI response"""
        prompt = self._build_prompt(data)
        response = openai.chat.completions.create(
            model=self.model,
            messages=self._create_messages(data),
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        return self._parse_response(response, data)

    def _create_messages(self, data: Dict[str, Any]) -> list:
        """Create context-aware message stack"""
        return [
            {
                "role": "system",
                "content": f"""Act as a professional FX trader. Rules:
1. Use {data.get('timeframe', 'M15')} timeframe
2. Max risk: {Settings.RISK_PERCENT}% per trade
3. Stop loss: {self._calculate_sl_distance(data):.5f} pips
4. Minimum {self.min_rr_ratio}:1 risk/reward
5. Consider volatility: {'High' if data.get('atr', 0) > 0.005 else 'Low'}"""
            },
            {"role": "user", "content": self._build_prompt(data)}
        ]

    def _build_prompt(self, data: Dict[str, Any]) -> str:
       return f"""Analyze {data.get('symbol', 'Pair')} market conditions:

Technical Indicators:
- Price: {data.get('close', 'N/A')}
- RSI(14): {data.get('rsi', 'N/A')}
- MACD: {data.get('macd', 'N/A')}  # Changed from MACD_12_26_9
- Bollinger Bands: {data.get('bb_upper', 'N/A')}/{data.get('bb_lower', 'N/A')}
- ATR(14): {data.get('atr', 'N/A')}
- EMA(50): {data.get('ema50', 'N/A')}

Market Context:
- Trend: {'Bullish' if data.get('close', 0) > data.get('ema50', 0) else 'Bearish'}
- Session: {data.get('session', 'London')}

Provide JSON response: {{"action": "buy/sell/hold", "stop_loss": price, "take_profit": price, "confidence": 0.0-1.0, "reasoning": "technical analysis"}}"""

    def _parse_response(self, response, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate API response"""
        try:
            response_data = json.loads(response.choices[0].message.content)
            return TradeDecision(**response_data).dict()
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from AI")
        except Exception as e:
            raise ValidationError(f"Response validation failed: {str(e)}")

    def _validate_decision(self, price: float, decision: Dict[str, Any]):
        """Validate trading decision parameters"""
        if decision['action'] == 'hold':
            return

        sl = decision['stop_loss']
        tp = decision['take_profit']
        
        # Price relationship validation
        if decision['action'] == 'buy' and not (sl < price < tp):
            raise ValueError(f"Invalid levels: SL({sl}) < Price({price}) < TP({tp})")
            
        if decision['action'] == 'sell' and not (tp < price < sl):
            raise ValueError(f"Invalid levels: TP({tp}) < Price({price}) < SL({sl})")

        # Risk/reward validation
        risk = abs(price - sl)
        reward = abs(tp - price)
        if reward / risk < self.min_rr_ratio:
            raise ValueError(f"RR ratio {reward/risk:.2f}:1 below minimum {self.min_rr_ratio}:1")

    def _calculate_sl_distance(self, data: Dict[str, Any]) -> float:
        """Calculate stop loss distance based on volatility"""
        return (data.get('atr', 0.001) * 2) * (1 if data.get('close', 0) > data.get('ema50', 0) else 1.5)

    def _safe_decision(self) -> Dict[str, Any]:
        """Fallback decision for system safety"""
        return {
            'action': 'hold',
            'stop_loss': 0.0,
            'take_profit': 0.0,
            'confidence': 0.0,
            'reasoning': 'System error - conservative hold'
        }