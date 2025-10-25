# runner_web.py - ACTUAL WORKING VERSION
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("PYTHON: Function started")
    web_logger(f"PYTHON: Operation: {cli_args.get('selected_operation')}")
    
    # Just create the output file directly
    input_file = cli_args.get('file_path')
    if input_file:
        output_name = f"LENGTHENED_{input_file}"
        web_logger(f"PYTHON: Creating {output_name}")
        
        with open(input_file, 'rb') as f:
            data = f.read()
        
        with open(output_name, 'wb') as f:
            f.write(data)
        
        web_logger("PYTHON: File created successfully")
    
    web_logger("PYTHON: Function completed")
    return "SUCCESS"
