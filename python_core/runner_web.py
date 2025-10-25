# runner_web.py - SIMPLE WORKING VERSION
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    try:
        web_logger("=== Running animation operation ===")
        
        # Get the main function directly from globals
        if 'main' not in globals():
            web_logger("ERROR: main function not found in globals")
            return "ERROR: main function not found"
        
        # Run the main function
        main(cli_args=cli_args, logger=web_logger)
        
        web_logger("=== Checking results ===")
        import os
        files = os.listdir('.')
        web_logger(f"Files in VFS: {files}")
        
        input_file = cli_args.get('file_path')
        if input_file:
            output_files = [f for f in files if f != input_file and (f.endswith('.bytes') or f.endswith('.txt') or f.endswith('.csv'))]
            web_logger(f"Output files: {output_files}")
        
        web_logger("--- PROCESSING COMPLETE ---")
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
