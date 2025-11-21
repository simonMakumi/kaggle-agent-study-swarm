import json
import os

MEMORY_FILE = "user_memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"facts": []}
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            # Ensure structure is correct even if file is old
            if "facts" not in data: data["facts"] = []
            return data
    except:
        return {"facts": []}

def save_memory(memory_data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory_data, f, indent=4)

def update_memory(new_fact):
    data = load_memory()
    if new_fact not in data["facts"]:
        data["facts"].append(new_fact)
        save_memory(data)

# NEW FUNCTION
def delete_fact(fact_to_delete):
    data = load_memory()
    if fact_to_delete in data["facts"]:
        data["facts"].remove(fact_to_delete)
        save_memory(data)