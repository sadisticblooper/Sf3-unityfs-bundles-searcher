# runner_web.py - FIXED VERSION WITH FILE WRITING
import io
import struct
import os

def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    try:
        # Import the main function 
        from animation_decrypter_2 import main
        
        # Run the operation
        web_logger("Running animation operation...")
        main(cli_args=cli_args, logger=web_logger)
        
        # Check for output files manually
        web_logger("Checking for output files...")
        output_files = []
        for file in os.listdir('.'):
            if file.endswith('.bytes') or file.endswith('.txt') or file.endswith('.csv'):
                # Skip input files
                if (cli_args.get('file_path') and file == cli_args.get('file_path')) or \
                   (cli_args.get('file1') and file == cli_args.get('file1')) or \
                   (cli_args.get('file2') and file == cli_args.get('file2')):
                    continue
                output_files.append(file)
                web_logger(f"Found output file: {file}")
        
        if output_files:
            web_logger(f"Output files: {output_files}")
        else:
            web_logger("No output files found after operation")
        
        web_logger("--- PROCESSING COMPLETE ---")
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
