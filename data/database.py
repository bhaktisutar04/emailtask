import sqlite3
import json
from datetime import datetime
import os

os.makedirs("data", exist_ok=True)
DB_PATH = "data/history.db"

def init_db():
    """Initializes the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for execution history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            workflow_id TEXT,
            input_data TEXT,
            state JSON,
            status TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def log_execution(workflow_id: str, input_data: str, final_state: dict, status: str = "success"):
    """Logs a workflow execution run."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO history (workflow_id, input_data, state, status)
        VALUES (?, ?, ?, ?)
    ''', (workflow_id, input_data, json.dumps(final_state), status))
    
    conn.commit()
    conn.close()
