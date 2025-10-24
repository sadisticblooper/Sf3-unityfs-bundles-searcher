# runner_web.py

import os
import sys

# Import your core logic
from animation_decrypter_2 import main as core_logic 
from user_pref import load_preferences, save_preferences # Now Pyodide-friendly

# Define a single logger function that uses Python's print, which JS intercepts
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    """
    The main Pyodide entry point called by JavaScript.
    cli_args is a dictionary passed directly from JS.
    """
    web_logger(f"--- Python Processor Initializing ---")
    web_logger(f"Operation: {cli_args.get('selected_operation', 'N/A')}")
    web_logger(f"Input File: {os.path.basename(cli_args.get('file_path', 'N/A'))}")
    
    # 1. Load preferences using the new browser-safe method
    prefs = load_preferences()
    # Update arguments with preferred export extension
    cli_args['export_extension'] = prefs.get('export_ext', '.bytes')
    
    # 2. Call the core logic function with the collected arguments
    # Note: Your core logic (animation_decrypter_2.main) must be refactored 
    # to accept cli_args and logger as parameters, which it already does!
    
    final_output_path = None
    
    try:
        # core_logic should return the path to the final output file upon success
        final_output_path = core_logic(cli_args=cli_args, logger=web_logger)
        
        web_logger("\n--- PROCESSING COMPLETE ---")
        if final_output_path:
            # Return the final output path so JavaScript can download it
            return final_output_path
        else:
            return None # Indicate failure if no path is returned
            
    except Exception as e:
        # Log any unexpected error
        web_logger(f"\nFATAL ERROR in Python Core: {e}")
        # Optionally, raise the exception to stop JS execution
        raise e

# --- Expose the function to the Pyodide global scope ---
# This makes it easy for main.js to call this function directly
# No need to expose it here, we will import it in main.js.
