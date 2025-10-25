# runner_web.py - FIXED VERSION
import io
import struct

def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    try:
        # Import the main function directly
        from animation_decrypter_2 import main as core_logic
        
        # Run the operation and capture output
        result = core_logic(cli_args=cli_args, logger=web_logger)
        
        web_logger("--- PROCESSING COMPLETE ---")
        
        # Return success status
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
