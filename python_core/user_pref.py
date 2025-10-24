# user_pref.py (Refactored for Pyodide)

import json
# Use the Pyodide js module to interact with the browser's DOM and APIs
from js import localStorage 

PREF_KEY = 'animation_tool_prefs' # Key to store JSON in LocalStorage

def get_default_prefs():
    """Returns a dictionary with the default application settings."""
    return {
        'import_ext': '.bytes',
        'export_ext': '.bytes'
        # 'last_path' is removed as the browser handles paths via file dialogs
    }

def load_preferences():
    """
    Loads user preferences from the browser's LocalStorage.
    If no preference is found, returns default preferences.
    """
    # 1. Try to load the stored JSON string from the browser's localStorage
    stored_prefs_json = localStorage.getItem(PREF_KEY)
    
    if stored_prefs_json:
        try:
            prefs = json.loads(stored_prefs_json)
            # Ensure all keys exist
            defaults = get_default_prefs()
            for key, value in defaults.items():
                if key not in prefs:
                    prefs[key] = value
            return prefs
        except json.JSONDecodeError:
            # If storage is corrupted, return defaults
            return get_default_prefs()
    
    return get_default_prefs()

def save_preferences(prefs_dict):
    """
    Saves the given preferences dictionary to the browser's LocalStorage.
    """
    try:
        prefs_json = json.dumps(prefs_dict)
        localStorage.setItem(PREF_KEY, prefs_json)
        return True
    except Exception as e:
        # Note: LocalStorage can fail if full or if browser security prevents it
        print(f"Error saving preferences to LocalStorage: {e}")
        return False
