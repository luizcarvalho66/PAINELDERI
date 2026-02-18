import os
import json
import time
from datetime import datetime

# [Data Guardian] Configuration
# Uses the same persistence logic as the Database Specialist
VOLUME_PATH = "/Volumes/main/default/ri_dashboard_data"
LOCAL_DATA_DIR = os.path.join(os.getcwd(), "data")
HISTORY_FILE_NAME = "kpi_history.json"
MAX_HISTORY_ITEMS = 50  # Keep last 50 snapshots to avoid file bloat

def _get_file_path():
    """Determines the safe persistent path for the history file."""
    if os.path.exists("/Volumes"):
        data_dir = VOLUME_PATH
    else:
        data_dir = LOCAL_DATA_DIR # Fallback to project/data
        
    try:
        os.makedirs(data_dir, exist_ok=True)
    except Exception:
        pass # access issues?
        
    return os.path.join(data_dir, HISTORY_FILE_NAME)

def load_history():
    """Loads the entire history list."""
    fpath = _get_file_path()
    if not os.path.exists(fpath):
        return []
    
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[SNAPSHOT MANAGER] Corrupt history file, resetting. Error: {e}")
        return []

def save_snapshot(context: str, metrics: dict):
    """
    Saves a new snapshot of metrics for a given context (e.g., 'farol_general').
    
    Args:
        context: A string identifier for the screen/section (e.g. 'farol_kpis')
        metrics: Dictionary containing numeric values to track.
    """
    history = load_history()
    
    entry = {
        "timestamp": time.time(),
        "date_str": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "context": context,
        "metrics": metrics
    }
    
    history.append(entry)
    
    # Prune old history specifically for this context is redundant if we prune global list
    # but let's just keep last N globally for simplicity or N per context.
    # Simple global prune for now.
    if len(history) > MAX_HISTORY_ITEMS:
        history = history[-MAX_HISTORY_ITEMS:]
        
    try:
        with open(_get_file_path(), 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[SNAPSHOT MANAGER] Failed to save snapshot: {e}")

def get_last_snapshot(context: str):
    """
    Returns the PREVIOUS snapshot (Penultimate) for comparison.
    Why Penultimate? Because 'Current' is usually what we are calculating right now.
    Wait, if we save *before* calculating, the last one IS the previous.
    Strategy: 
    1. The App calculates current metrics.
    2. The App asks: "What was the previous value?" -> Call get_last_snapshot()
    3. The App saves the current metrics -> Call save_snapshot()
    
    So get_last_snapshot should return the MOST RECENT entry in the file matching the context.
    """
    history = load_history()
    
    # Filter by context
    context_history = [h for h in history if h.get("context") == context]
    
    if not context_history:
        return None
        
    # Return the last one known (which is the "Previous" compared to what we are holding in memory now)
    return context_history[-1]
