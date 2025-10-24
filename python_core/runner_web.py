import os
from animation_decrypter_2 import main as core_logic
from user_pref import load_preferences

def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    prefs = load_preferences()
    cli_args['export_extension'] = prefs.get('export_ext', '.bytes')
    
    try:
        final_output_path = core_logic(cli_args=cli_args, logger=web_logger)
        web_logger("--- PROCESSING COMPLETE ---")
        return final_output_path
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        raise e