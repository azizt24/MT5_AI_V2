import openai
import json
import time
from typing import Dict, Any
from config import Settings, Credentials
from ml_predictor import MLTrader

class AITrader:
    def __init__(self):
        openai.api_key = Credentials.openai()
        self.model = Settings.MODEL_NAME
        self.ml_trader = MLTrader()
    
    def analyze_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-driven trading decisions using GPT-3.5 and ML model"""
        print(f"🤖 [AI] Analyzing {data.get('symbol', 'Unknown')} market...")
        
        try:
            # Get Machine Learning prediction
            ml_decision = self.ml_trader.predict(data)
            
            # Get AI decision from GPT-3.5
            ai_decision = self._get_ai_decision(data, ml_decision)
            return ai_decision
        except Exception as e:
            print(f"⛔ AI Decision Error: {str(e)}")
            return self._safe_decision()
    
    def _get_ai_decision(self, data: Dict[str, Any], ml_decision: str) -> Dict[str, Any]:
        """Get trading decision from GPT-3.5 using ML suggestion"""
        messages = [
            {"role": "system", "content": "Act as a professional Forex trader making AI-driven decisions."},
            {"role": "user", "content": self._build_prompt(data, ml_decision)}
        ]
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=300
        )
        
        return self._parse_response(response)
    
    def _build_prompt(self, data: Dict[str, Any], ml_decision: str) -> str:
        """Create prompt for GPT-3.5 decision-making"""
        return f"""Analyze {data.get('symbol', 'Unknown')} market conditions:
        - ML Suggested Action: {ml_decision.upper()}
        - Current Price: {data.get('close', 'N/A')}
        - RSI: {data.get('rsi', 'N/A')}
        - MACD: {data.get('macd', 'N/A')}
        - EMA(20): {data.get('ema_20', 'N/A')}
        - EMA(50): {data.get('ema_50', 'N/A')}
        - ATR(14): {data.get('atr', 'N/A')}
        
        Should I proceed with a trade? Respond in JSON format: 
        {{"action": "buy/sell/hold", "stop_loss": price, "take_profit": price, "confidence": 0.0-1.0, "reasoning": "short explanation"}}"""
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse AI response from GPT-3.5"""
        try:
            response_data = json.loads(response["choices"][0]["message"]["content"])
            return response_data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from AI")
    
    def _safe_decision(self) -> Dict[str, Any]:
        """Fallback decision for system safety"""
        return {"action": "hold", "stop_loss": 0.0, "take_profit": 0.0, "confidence": 0.0, "reasoning": "System error - conservative hold"}

if __name__ == "__main__":
    trader = AITrader()
    sample_data = {"symbol": "EURUSD", "close": 1.105, "rsi": 50.2, "macd": 0.002, "ema_20": 1.104, "ema_50": 1.103, "atr": 0.001}
    decision = trader.analyze_market(sample_data)
    print("🤖 AI Trade Decision:", decision)
