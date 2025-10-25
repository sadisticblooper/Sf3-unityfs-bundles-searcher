# runner_web.py - SIMPLE VERSION
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    try:
        # Get the main function from globals (it should be loaded already)
        if 'main' in globals():
            web_logger("Running main function...")
            main(cli_args=cli_args, logger=web_logger)
            web_logger("--- PROCESSING COMPLETE ---")
            return "SUCCESS"
        else:
            # Try to find the main function in animation_decrypter_2 namespace
            import sys
            if 'animation_decrypter_2' in sys.modules:
                animation_module = sys.modules['animation_decrypter_2']
                if hasattr(animation_module, 'main'):
                    web_logger("Running animation_decrypter_2.main...")
                    animation_module.main(cli_args=cli_args, logger=web_logger)
                    web_logger("--- PROCESSING COMPLETE ---")
                    return "SUCCESS"
            
            web_logger("ERROR: Could not find main function")
            return "ERROR: Could not find main function"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
