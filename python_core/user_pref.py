import json
from js import localStorage

PREF_KEY = 'animation_tool_prefs'

def get_default_prefs():
    return {
        'import_ext': '.bytes',
        'export_ext': '.bytes'
    }

def load_preferences():
    try:
        stored = localStorage.getItem(PREF_KEY)
        if stored:
            prefs = json.loads(stored)
            defaults = get_default_prefs()
            return {**defaults, **prefs}
    except:
        pass
    return get_default_prefs()

def save_preferences(prefs_dict):
    try:
        localStorage.setItem(PREF_KEY, json.dumps(prefs_dict))
        return True
    except:
        return False