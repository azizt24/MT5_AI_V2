import pandas as pd
import xgboost as xgb
import sys
import os
import glob
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Settings  # Import Settings

class MLTrader:
    def __init__(self):
        self.model_filename = "models/trading_model.pkl"
        os.makedirs("models", exist_ok=True)

    def get_latest_file(self, symbol: str, timeframe: str):
        """Find the latest available market data file for a given symbol and timeframe."""
        print(f"🔍 Looking for latest file: {symbol} {timeframe}...")
        
        files = glob.glob(f"data/data/{symbol}_{timeframe}_*.csv") or glob.glob(f"data/{symbol}_{timeframe}_*.csv")
        if not files:
            print(f"⛔ No files found for {symbol} {timeframe}. Run fetch_data.py first.")
            return None
        latest_file = max(files, key=os.path.getctime)
        print(f"📂 Found latest data file: {latest_file}")
        return latest_file

    def load_data(self, filepath):
        """Load historical data for model training"""
        print(f"📥 Loading data from {filepath}")
        df = pd.read_csv(filepath, parse_dates=['time'])
        df.set_index('time', inplace=True)
        df.dropna(inplace=True)
        return df

    def prepare_features(self, df):
        """Generate technical indicators as features for ML model"""
        print("📊 Generating technical indicators...")
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['rsi'] = self.calculate_rsi(df['close'])
        df['macd'] = df['ema_20'] - df['ema_50']
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)  # 1 if price goes up, 0 if down
        df.dropna(inplace=True)
        return df

    def calculate_rsi(self, series, period=14):
        """Calculate Relative Strength Index (RSI)"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def train_model(self, df):
        """Train an XGBoost model for trade prediction"""
        print("🧠 Training AI model...")
        features = ['ema_20', 'ema_50', 'rsi', 'macd']
        X = df[features]
        y = df['target']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=5)
        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        print(f"✅ Model trained with accuracy: {accuracy:.2f}")

        with open(self.model_filename, 'wb') as f:
            pickle.dump(model, f)
        print(f"✅ Model saved to {self.model_filename}")

    def predict(self, df):
        """Load trained model and make predictions"""
        if not os.path.exists(self.model_filename):
            print("⛔ No trained model found. Train the model first.")
            return None

        with open(self.model_filename, 'rb') as f:
            model = pickle.load(f)

        features = ['ema_20', 'ema_50', 'rsi', 'macd']
        X = df[features].tail(1)  # Predict next trade
        prediction = model.predict(X)[0]
        action = 'buy' if prediction == 1 else 'sell'
        print(f"🤖 AI Trade Prediction: {action.upper()}")
        return action

if __name__ == "__main__":
    trader = MLTrader()
    
    try:
        file_path = trader.get_latest_file("EURUSD", "M15")  # Automatically find the latest file
        if not file_path:
            raise FileNotFoundError("⛔ No EURUSD M15 data found. Trying another available symbol...")

        df = trader.load_data(file_path)
        df = trader.prepare_features(df)
        trader.train_model(df)
        trader.predict(df)
    
    except FileNotFoundError as e:
        print(str(e))
