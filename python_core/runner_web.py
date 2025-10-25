# runner_web.py - DEBUG MAIN FUNCTION
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("=== PYTHON CODE IS RUNNING ===")
    
    # Check if main function exists
    web_logger("=== CHECKING FOR MAIN FUNCTION ===")
    
    try:
        # Try to import and call main
        import animation_decrypter_2
        web_logger("✓ animation_decrypter_2 imported")
        
        if hasattr(animation_decrypter_2, 'main'):
            web_logger("✓ main function found")
            web_logger("=== CALLING MAIN FUNCTION ===")
            
            # Call the main function
            animation_decrypter_2.main(cli_args=cli_args, logger=web_logger)
            
            web_logger("=== MAIN FUNCTION COMPLETED ===")
        else:
            web_logger("✗ main function NOT found in animation_decrypter_2")
            
    except Exception as e:
        web_logger(f"✗ Error: {e}")
        import traceback
        web_logger("TRACEBACK:")
        web_logger(traceback.format_exc())
    
    web_logger("=== RUNNER COMPLETE ===")
    return "SUCCESS"
