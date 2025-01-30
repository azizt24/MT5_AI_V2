### monitoring/trade_logger.py
import json

def log_trade(data, filename="trade_logs.json"):
    """Log trade data in JSON format."""
    with open(filename, "a") as file:
        json.dump(data, file, indent=4)
        file.write("\n")