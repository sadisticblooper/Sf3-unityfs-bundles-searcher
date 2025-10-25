# runner_web.py - FORCE FILE CREATION
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    web_logger(f"Operation: {cli_args.get('selected_operation')}")
    web_logger(f"File: {cli_args.get('file_path')}")
    
    try:
        # Force create some test files to see if writing works
        web_logger("=== FORCING FILE CREATION ===")
        
        # Test 1: Write a simple test file
        with open('TEST_OUTPUT.bytes', 'wb') as f:
            f.write(b'TEST_DATA_12345')
        web_logger("✓ Created TEST_OUTPUT.bytes")
        
        # Test 2: Try to read the input file
        input_file = cli_args.get('file_path')
        if input_file:
            try:
                with open(input_file, 'rb') as f:
                    data = f.read()
                    web_logger(f"✓ Read input file: {len(data)} bytes")
                    
                    # Test 3: Create a modified version
                    output_name = f"MODIFIED_{input_file}"
                    with open(output_name, 'wb') as f:
                        f.write(data + b"_MODIFIED")
                    web_logger(f"✓ Created {output_name}")
            except Exception as e:
                web_logger(f"✗ Error reading input file: {e}")
        
        # Test 4: Create another test file
        with open('ANOTHER_TEST.txt', 'w') as f:
            f.write("This is a test file")
        web_logger("✓ Created ANOTHER_TEST.txt")
        
        # List all files to see what we created
        import os
        files = os.listdir('.')
        web_logger(f"=== ALL FILES IN VFS: {files} ===")
        
        web_logger("--- PROCESSING COMPLETE ---")
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
