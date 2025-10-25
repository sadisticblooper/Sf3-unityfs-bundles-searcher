# runner_web.py - DEBUG VERSION
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    try:
        web_logger("=== DEBUG: Checking what's available ===")
        import sys
        web_logger(f"Modules loaded: {list(sys.modules.keys())}")
        
        if 'main' in globals():
            web_logger("DEBUG: main found in globals")
        else:
            web_logger("DEBUG: main NOT in globals")
            
        if 'animation_decrypter_2' in sys.modules:
            web_logger("DEBUG: animation_decrypter_2 module found")
            animation_module = sys.modules['animation_decrypter_2']
            if hasattr(animation_module, 'main'):
                web_logger("DEBUG: animation_decrypter_2.main found")
            else:
                web_logger("DEBUG: animation_decrypter_2.main NOT found")
        else:
            web_logger("DEBUG: animation_decrypter_2 module NOT found")
        
        web_logger("=== DEBUG: Listing files before operation ===")
        import os
        files_before = os.listdir('.')
        web_logger(f"Files before: {files_before}")
        
        # Try to run the operation
        web_logger("=== Running operation ===")
        if 'main' in globals():
            web_logger("Running main from globals...")
            main(cli_args=cli_args, logger=web_logger)
        elif 'animation_decrypter_2' in sys.modules:
            animation_module = sys.modules['animation_decrypter_2']
            if hasattr(animation_module, 'main'):
                web_logger("Running animation_decrypter_2.main...")
                animation_module.main(cli_args=cli_args, logger=web_logger)
            else:
                web_logger("ERROR: No main function found in animation_decrypter_2")
                return "ERROR: No main function"
        else:
            web_logger("ERROR: Could not find main function anywhere")
            return "ERROR: No main function found"
        
        web_logger("=== DEBUG: Listing files after operation ===")
        files_after = os.listdir('.')
        web_logger(f"Files after: {files_after}")
        
        # Check what changed
        new_files = [f for f in files_after if f not in files_before]
        web_logger(f"New files created: {new_files}")
        
        web_logger("--- PROCESSING COMPLETE ---")
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
