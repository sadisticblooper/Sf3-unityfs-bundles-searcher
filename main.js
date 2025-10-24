// main.js (Updated for Modular Pyodide)

let pyodide = null;
const outputLog = document.getElementById('outputLog');
const runButton = document.getElementById('runButton');
// ... (logToConsole, initializePyodide, downloadVFSFile functions remain the same) ...

async function initializePyodide() {
    // ... (Pyodide loading logic) ...
    
    // Use micropip to install your package from the local file system.
    // This is the cleanest way to import local modules/packages.
    await pyodide.loadPackage(['micropip', 'numpy']);
    
    // Manually register your /python_core directory as a Python package.
    // This assumes your Python files are correctly placed in the python_core/ directory.
    await pyodide.runPythonAsync(`
        import micropip
        # The python_core folder is the package source
        await micropip.install('/python_core') 
    `);
    
    logToConsole("Pyodide is ready! Core modules loaded.");
    runButton.textContent = "Run Operation";
    runButton.disabled = false;
    runButton.onclick = runPythonCode;
}

// ... (downloadVFSFile function must be included here) ...

async function runPythonCode() {
    // ... (Gather UI parameters as before) ...
    // ... (File upload and VFS write logic as before) ...

    try {
        // 1. Get a reference to your Python function from the loaded package
        // This is the true modular way: pyodide.globals.get("module").get("function")
        const python_module = pyodide.globals.get('pyodide_runner_web'); // Assuming the package name is pyodide_runner_web
        const run_fn = python_module.get('run_web_operation');

        // 2. Convert the JavaScript object (cliArgs) to a Pyodide-friendly Python object
        const py_args = pyodide.toPy(cliArgs); 
        
        // 3. Execute the Python function asynchronously and capture the result (the output filename)
        logToConsole("\nProcessing data in Pyodide...");
        const outputFilename = await run_fn(py_args);
        
        // 4. Use the returned filename to trigger the download
        if (outputFilename) {
            downloadVFSFile(outputFilename, 'application/octet-stream');
            // Clean up the VFS file after download is initiated
            pyodide.FS.unlink(outputFilename);
        } else {
            logToConsole("Warning: Python script finished, but did not return a valid output path.");
        }
        
    } catch (e) {
        logToConsole(`FATAL PYTHON ERROR: ${e.message || e}\n`);
    } finally {
        // ... (Cleanup and UI reset) ...
    }
}

initializePyodide();
