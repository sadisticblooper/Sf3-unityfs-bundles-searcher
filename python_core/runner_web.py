# runner_web.py - DEBUG ANIMATION CODE
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    try:
        # Get the main function from animation_decrypter_2
        import animation_decrypter_2
        
        web_logger("=== Running animation_decrypter_2.main ===")
        
        # Run the main function with debug logging
        animation_decrypter_2.main(cli_args=cli_args, logger=web_logger)
        
        web_logger("=== Checking files after animation code ===")
        import os
        files = os.listdir('.')
        web_logger(f"All files: {files}")
        
        # Check what files were created
        input_file = cli_args.get('file_path')
        output_files = [f for f in files if f != input_file and (f.endswith('.bytes') or f.endswith('.txt') or f.endswith('.csv'))]
        web_logger(f"Output files created: {output_files}")
        
        web_logger("--- PROCESSING COMPLETE ---")
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
