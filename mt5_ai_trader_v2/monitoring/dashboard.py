# monitoring/dashboard.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os
from config import Settings

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <html>
        <head>
            <title>AI Trading Monitor</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div id="trades"></div>
            <script>
                async function updateData() {
                    const res = await fetch('/trades');
                    const data = await res.json();
                    Plotly.newPlot('trades', data);
                }
                setInterval(updateData, 5000);
            </script>
        </body>
    </html>
    """

@app.get("/trades")
async def get_trades():
    logs = []
    for file in os.listdir(Settings.LOG_DIR):
        if file.endswith('.json'):
            with open(os.path.join(Settings.LOG_DIR, file)) as f:
                logs.append(json.load(f))
                
    return {
        "data": [{
            "x": [log['time'] for log in logs],
            "y": [log['profit'] for log in logs],
            "type": "scatter"
        }]
    }