import json
import os

MEMORY_FILE = "user_memory.json"

def load_memory():
    """Loads the user's long-term memory from a JSON file."""
    if not os.path.exists(MEMORY_FILE):
        return {"user_name": "User", "preferences": [], "facts": []}
    
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {"user_name": "User", "preferences": [], "facts": []}

def save_memory(memory_data):
    """Saves the user's long-term memory to a JSON file."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory_data, f, indent=4)

def update_memory(new_fact):
    """Adds a new fact to the memory."""
    data = load_memory()
    if new_fact not in data["facts"]:
        data["facts"].append(new_fact)
        save_memory(data)
