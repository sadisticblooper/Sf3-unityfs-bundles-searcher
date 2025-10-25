# runner_web.py - SIMPLE TEST
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    web_logger(f"Operation: {cli_args.get('selected_operation')}")
    web_logger(f"File: {cli_args.get('file_path')}")
    
    try:
        # Just test if we can write a file
        web_logger("=== TEST: Writing test file ===")
        with open('TEST_FILE.bytes', 'wb') as f:
            f.write(b'TEST_DATA')
        web_logger("TEST: File written successfully")
        
        # List files to see what's there
        import os
        files = os.listdir('.')
        web_logger(f"Files in VFS: {files}")
        
        web_logger("--- PROCESSING COMPLETE ---")
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
