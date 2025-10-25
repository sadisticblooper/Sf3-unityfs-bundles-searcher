# runner_web.py - FINAL FIX
def web_logger(message):
    print(message)

def run_web_operation(cli_args):
    web_logger("--- Python Processor Starting ---")
    
    try:
        web_logger("=== Checking available modules ===")
        import sys
        modules = [name for name in sys.modules.keys() if 'animation' in name or 'decrypter' in name]
        web_logger(f"Animation-related modules: {modules}")
        
        # Try to get main function from globals
        if 'main' in globals():
            web_logger("Found main in globals")
            main_func = globals()['main']
        else:
            web_logger("Main not in globals, checking sys.modules")
            # Check all loaded modules for main function
            main_func = None
            for module_name, module in sys.modules.items():
                if module and hasattr(module, 'main'):
                    web_logger(f"Found main in {module_name}")
                    main_func = module.main
                    break
            
            if not main_func:
                web_logger("ERROR: Could not find main function in any module")
                return "ERROR: No main function found"
        
        web_logger("=== Running animation operation ===")
        main_func(cli_args=cli_args, logger=web_logger)
        
        web_logger("=== Checking results ===")
        import os
        files = os.listdir('.')
        web_logger(f"All files: {files}")
        
        input_file = cli_args.get('file_path')
        output_files = [f for f in files if f != input_file and (f.endswith('.bytes') or f.endswith('.txt') or f.endswith('.csv'))]
        web_logger(f"Output files found: {output_files}")
        
        web_logger("--- PROCESSING COMPLETE ---")
        return "SUCCESS"
        
    except Exception as e:
        web_logger(f"ERROR: {e}")
        import traceback
        web_logger(traceback.format_exc())
        return f"ERROR: {str(e)}"
