# runner_web.py - ULTRA SIMPLE TEST
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("=== PYTHON CODE IS RUNNING ===")
    web_logger(f"Operation: {cli_args.get('selected_operation')}")
    
    # Force create output files
    web_logger("=== CREATING TEST FILES ===")
    
    with open('TEST1.bytes', 'wb') as f:
        f.write(b'TEST_FILE_1')
    web_logger("Created TEST1.bytes")
    
    with open('TEST2.txt', 'w') as f:
        f.write("Test file 2")
    web_logger("Created TEST2.txt")
    
    # Try to modify the input file
    input_file = cli_args.get('file_path')
    if input_file:
        try:
            with open(input_file, 'rb') as f:
                data = f.read()
            web_logger(f"Read input file: {len(data)} bytes")
            
            output_name = f"OUTPUT_{input_file}"
            with open(output_name, 'wb') as f:
                f.write(data)
            web_logger(f"Created {output_name}")
        except Exception as e:
            web_logger(f"Error with input file: {e}")
    
    web_logger("=== PYTHON COMPLETE ===")
    return "SUCCESS"
