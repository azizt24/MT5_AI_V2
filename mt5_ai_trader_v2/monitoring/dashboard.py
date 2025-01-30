# monitoring/dashboard.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os
from config import Settings

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Returns an interactive HTML dashboard for AI trading performance."""
    return """
    <html>
        <head>
            <title>AI Trading Monitor</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <h1>AI Trading Performance</h1>
            <div id="trades"></div>
            <script>
                async function updateData() {
                    try {
                        const res = await fetch('/trades');
                        const data = await res.json();
                        
                        // Ensure valid data format
                        if (!data.data || data.data.length === 0) {
                            console.warn("No trade data received.");
                            return;
                        }

                        // Update the chart dynamically
                        Plotly.react('trades', data.data, { title: "Trading Profit/Loss Over Time" });
                    } catch (error) {
                        console.error("Error fetching trade data:", error);
                    }
                }

                // Initial load and auto-update every 5 seconds
                updateData();
                setInterval(updateData, 5000);
            </script>
        </body>
    </html>
    """

@app.get("/trades")
async def get_trades():
    """Fetch and format trade log data for visualization."""
    logs = []

    # Ensure log directory exists
    if not os.path.exists(Settings.LOG_DIR):
        return {"data": []}

    # Read all JSON logs and collect valid trade entries
    for file in os.listdir(Settings.LOG_DIR):
        if file.endswith('.json'):
            try:
                with open(os.path.join(Settings.LOG_DIR, file)) as f:
                    log_entries = json.load(f)
                    if isinstance(log_entries, list):  # If log contains multiple entries
                        logs.extend(log_entries)
                    else:  # If single entry, wrap in a list
                        logs.append(log_entries)
            except json.JSONDecodeError:
                print(f"⚠️ Skipping corrupted file: {file}")

    # Format data for Plotly
    if not logs:
        return {"data": []}  # Return empty dataset if no logs found

    return {
        "data": [{
            "x": [log.get('timestamp', '') for log in logs],  # Use 'timestamp' key safely
            "y": [log.get('result', {}).get('profit', 0) for log in logs],  # Extract profit safely
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Trade Profit"
        }]
    }
