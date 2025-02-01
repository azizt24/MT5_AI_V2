import pandas as pd
import os
from ml_predictor import MLTrader

class Backtester:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.trader = MLTrader()
        self.results = []
    
    def load_data(self):
        """Load historical data for backtesting"""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"⛔ Data file {self.data_file} not found.")
        
        df = pd.read_csv(self.data_file, parse_dates=['time'])
        df.set_index('time', inplace=True)
        return df
    
    def run_backtest(self):
        """Run backtest on historical data using ML model"""
        df = self.load_data()
        df = self.trader.prepare_features(df)
        
        for i in range(len(df) - 1):
            row = df.iloc[i]
            prediction = self.trader.predict(pd.DataFrame([row]))
            actual = df.iloc[i + 1]['close']
            entry_price = row['close']
            profit = actual - entry_price if prediction == 'buy' else entry_price - actual
            self.results.append({'time': row.name, 'prediction': prediction, 'profit': profit})
        
        self.save_results()
    
    def save_results(self):
        """Save backtest results to a file"""
        results_df = pd.DataFrame(self.results)
        results_df.to_csv("backtest_results.csv", index=False)
        print("✅ Backtest results saved to backtest_results.csv")
    
if __name__ == "__main__":
    backtester = Backtester("data/EURUSD_M15.csv")  # Example dataset
    backtester.run_backtest()
