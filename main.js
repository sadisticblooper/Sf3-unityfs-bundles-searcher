// Global variable for the Pyodide instance
let pyodide = null;
const outputLog = document.getElementById('outputLog');
const runButton = document.getElementById('runButton');

// Function to log messages to the HTML <pre> area
function logToConsole(message) {
    outputLog.textContent += message + '\n';
    // Scroll to the bottom of the log
    outputLog.scrollTop = outputLog.scrollHeight;
}

/**
 * Initializes Pyodide and sets up the environment.
 */
async function initializePyodide() {
    logToConsole("Starting Pyodide initialization...");
    try {
        pyodide = await loadPyodide();
        
        // This is where you would normally load NumPy and your .py files
        await pyodide.loadPackage(['numpy']);

        logToConsole("Pyodide is ready! NumPy loaded.");
        
        // Setup the run button state
        runButton.textContent = "Run Operation";
        runButton.disabled = false;
        runButton.onclick = runPythonCode;
        
    } catch (e) {
        logToConsole(`ERROR: Pyodide failed to load: ${e}`);
        runButton.textContent = "Initialization Failed";
    }
}

/**
 * Executes a boilerplate Python script using the arguments from the UI.
 */
async function runPythonCode() {
    runButton.disabled = true;
    runButton.textContent = "Processing...";
    
    // 1. Gather UI parameters (Mimicking your get_ui_params)
    const operation = document.getElementById('operationSelect').value;
    const factorN = document.getElementById('factor_n').value;
    const factorD = document.getElementById('factor_d').value;
    const boneIDs = document.getElementById('boneIDs').value;
    const filename = document.getElementById('inputFile').files[0] ? document.getElementById('inputFile').files[0].name : "NO_FILE_SELECTED";

    logToConsole(`\n--- Running Operation: ${operation} ---`);
    logToConsole(`File: ${filename}`);
    logToConsole(`Factors: ${factorN}/${factorD}`);
    logToConsole(`Bones: ${boneIDs || 'ALL'}`);

    // 2. Define the Python script as a multiline string
    // This script will run in the Pyodide environment.
    const pythonScript = `
import sys
import datetime

# Define a simple function to print and return
def process_data(op, N, D, bones, filename):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Print to stdout, which is redirected to the JS console by default
    print(f"[{timestamp}] Hello from Python! Operation: {op} started.")
    print(f"[{timestamp}] Arguments received: N={N}, D={D}, Bones='{bones}'")
    
    # Simulate the work being done
    result = f"Successfully simulated {op} on {filename}."
    
    # A successful run returns a value which can be captured by JS
    return result

# Get the variables passed from JavaScript
op = '${operation}'
N = '${factorN}'
D = '${factorD}'
bones = '${boneIDs}'
filename = '${filename}'

# Call the function and make sure its result is the last thing evaluated
process_data(op, N, D, bones, filename)
    `;

    try {
        // 3. Execute the Python script
        // pyodide.runPythonAsync is used because loading packages (which we did) is async.
        const pythonResult = await pyodide.runPythonAsync(pythonScript);
        
        // 4. Log the return value from the Python script
        logToConsole(`Python Script Finished. Result (Returned to JS): ${pythonResult}`);
        
    } catch (e) {
        // 5. Log any errors that occurred in the Python script
        logToConsole(`FATAL PYTHON ERROR: ${e.type}: ${e.message}`);
        logToConsole("Check console for more details.");
    } finally {
        runButton.textContent = "Run Operation";
        runButton.disabled = false;
        logToConsole("--------------------------------------");
    }
}

// Start the entire process
initializePyodide();
