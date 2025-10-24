// main.js - Complete Vercel Implementation

let pyodide = null;
let currentBoneCheckboxes = new Map();

// DOM Elements
const elements = {
    outputLog: document.getElementById('outputLog'),
    runButton: document.getElementById('runButton'),
    operationSelect: document.getElementById('operationSelect'),
    paramsContainer: document.getElementById('paramsContainer'),
    splicerSection: document.getElementById('splicerSection'),
    boneSelectionSection: document.getElementById('boneSelectionSection'),
    boneList: document.getElementById('boneList'),
    settingsButton: document.getElementById('settingsButton'),
    settingsModal: document.getElementById('settingsModal'),
    saveSettings: document.getElementById('saveSettings'),
    cancelSettings: document.getElementById('cancelSettings'),
    selectAllBones: document.getElementById('selectAllBones'),
    deselectAllBones: document.getElementById('deselectAllBones')
};

// Bone map matching your Python BONE_MAP
const BONE_MAP = {
    0: "pelvis", 1: "stomach", 2: "chest", 3: "neck", 4: "head", 5: "hair", 6: "hair1",
    7: "zero_joint_hand_l", 8: "clavicle_l", 9: "arm_l", 10: "forearm_l",
    11: "forearm_twist_l", 12: "hand_l", 13: "weapon_l", 14: "f_big1_l", 15: "f_big2_l", 16: "f_big3_l",
    17: "f_main1_l", 18: "f_main2_l", 19: "f_main3_l", 20: "f_pointer1_l", 21: "f_pointer2_l", 22: "f_pointer3_l",
    23: "scapular_l", 24: "chest_l", 25: "zero_joint_hand_r", 26: "clavicle_r", 27: "arm_r", 28: "forearm_r",
    29: "forearm_twist_r", 30: "hand_r", 31: "weapons_r", 32: "f_big1_r", 33: "f_big2_r", 34: "f_big3_r",
    35: "f_main1_r", 36: "f_main2_r", 37: "f_main3_r", 38: "f_pointer1_r", 39: "f_pointer2_r", 40: "f_pointer3_r",
    41: "scapular_r", 42: "chest_r", 43: "zero_joint_pelvis_l", 44: "thigh_l", 45: "calf_l", 46: "foot_l",
    47: "toe_l", 48: "back_l", 49: "chest_h_49", 50: "stomach_h_50",
    51: "zero_joint_pelvis_r", 52: "thigh_r", 53: "calf_r", 54: "foot_r", 55: "toe_r", 56: "back_r",
    57: "biceps_twist_l", 58: "biceps_twist_r", 59: "thigh_twist_l", 60: "thigh_twist_r",
    61: "foot_r_extra", 62: "toe_r_extra", 63: "weapon_r_extra", 64: "weapon_l_extra", 65: "root_extra"
};

class AnimationTool {
    constructor() {
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.initializePyodide();
    }

    setupEventListeners() {
        elements.operationSelect.addEventListener('change', () => this.updateParametersUI());
        elements.settingsButton.addEventListener('click', () => this.showSettingsModal());
        elements.saveSettings.addEventListener('click', () => this.saveSettings());
        elements.cancelSettings.addEventListener('click', () => this.hideSettingsModal());
        elements.selectAllBones.addEventListener('click', () => this.toggleAllBones(true));
        elements.deselectAllBones.addEventListener('click', () => this.toggleAllBones(false));
        
        // Splicer file listeners
        document.getElementById('splicerFile1').addEventListener('change', () => this.updateSplicerInfo());
        document.getElementById('splicerFile2').addEventListener('change', () => this.updateSplicerInfo());
    }

    log(message) {
        elements.outputLog.textContent += message + '\n';
        elements.outputLog.scrollTop = elements.outputLog.scrollHeight;
        console.log(message);
    }

    clearLog() {
        elements.outputLog.textContent = '';
    }

    async initializePyodide() {
        this.log("🚀 Loading Pyodide runtime...");
        
        try {
            pyodide = await loadPyodide();
            this.log("✅ Pyodide loaded successfully!");

            // Load required packages
            await pyodide.loadPackage(['micropip']);
            const micropip = pyodide.pyimport('micropip');
            await micropip.install('numpy');
            this.log("✅ NumPy installed");

            // Load Python modules
            await this.loadPythonModules();
            
            elements.runButton.textContent = "Run Operation";
            elements.runButton.disabled = false;
            elements.runButton.onclick = () => this.runOperation();

            this.log("✅ System ready! Select an operation to begin.");
            
        } catch (error) {
            this.log(`❌ Failed to initialize: ${error}`);
            elements.runButton.textContent = "Initialization Failed";
        }
    }

    async loadPythonModules() {
    // Load all Python code into a single module context
    const modules = [
        'frame_modifiers.py',
        'user_pref.py', 
        'animation_decrypter_2.py',
        'runner_web.py'
    ];
    
    let allPythonCode = '';
    
    // First, concatenate all Python code
    for (const module of modules) {
        try {
            const response = await fetch(`./python_core/${module}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const code = await response.text();
            allPythonCode += `\n# --- ${module} ---\n` + code + `\n`;
            this.log(`✅ Loaded: ${module}`);
        } catch (error) {
            this.log(`❌ Failed to load ${module}: ${error}`);
            throw error; // Stop if any module fails
        }
    }
    
    // Execute all Python code at once
    try {
        pyodide.runPython(allPythonCode);
        this.log("✅ All Python modules executed successfully");
    } catch (error) {
        this.log(`❌ Failed to execute Python code: ${error}`);
        throw error;
    }
}

    updateParametersUI() {
        const operation = elements.operationSelect.value;
        elements.paramsContainer.innerHTML = '';
        
        // Hide special sections
        elements.splicerSection.style.display = 'none';
        elements.boneSelectionSection.style.display = 'none';

        switch(operation) {
            case 'SHORTEN':
            case 'LENGTHEN':
                elements.paramsContainer.innerHTML = `
                    <div class="param-row">
                        <label>Factor:</label>
                        <input type="number" id="factor" value="2.0" step="0.1" min="1.0">
                    </div>
                `;
                break;

            case 'DASH':
                elements.paramsContainer.innerHTML = `
                    <div class="param-row">
                        <label>Offset Factor:</label>
                        <input type="number" id="offsetFactor" value="10.0" step="0.1">
                    </div>
                    <div class="param-row">
                        <label>Direction:</label>
                        <select id="dashDirection">
                            <option value="Towards">Towards</option>
                            <option value="Away">Away</option>
                        </select>
                    </div>
                `;
                break;

            case 'BIRTH_LOCATION':
                elements.paramsContainer.innerHTML = `
                    <div class="param-row">
                        <label>Total Offset:</label>
                        <input type="number" id="totalOffset" value="200.0">
                    </div>
                    <div class="param-row">
                        <label>Direction:</label>
                        <select id="birthDirection">
                            <option value="Towards">Towards</option>
                            <option value="Away">Away</option>
                        </select>
                    </div>
                `;
                break;

            case 'TRIMMER':
                elements.paramsContainer.innerHTML = `
                    <div class="param-row">
                        <label>Remove Frames:</label>
                        <input type="text" id="trimRange" value="1-10" placeholder="e.g., 1-10">
                    </div>
                    <p class="note">Frames are counted from 1. Range is inclusive.</p>
                `;
                break;

            case 'AXIS_ADDER':
                elements.paramsContainer.innerHTML = `
                    <div class="param-row">
                        <label>X Offset:</label>
                        <input type="number" id="xOffset" value="0.0" step="0.1">
                    </div>
                    <div class="param-row">
                        <label>Y Offset:</label>
                        <input type="number" id="yOffset" value="0.0" step="0.1">
                    </div>
                    <div class="param-row">
                        <label>Z Offset:</label>
                        <input type="number" id="zOffset" value="0.0" step="0.1">
                    </div>
                    <div class="param-row">
                        <label>Bone ID:</label>
                        <input type="number" id="boneId" value="-1">
                    </div>
                    <p class="note">Use -1 for all bones, 0 for pelvis</p>
                `;
                break;

            case 'AXIS_SCALER':
                elements.paramsContainer.innerHTML = `
                    <div class="param-row">
                        <label>Scale Factor:</label>
                        <input type="number" id="scaleFactor" value="1.5" step="0.1">
                    </div>
                `;
                elements.boneSelectionSection.style.display = 'block';
                this.populateBoneList();
                break;

            case 'SPLICER':
                elements.splicerSection.style.display = 'block';
                break;

            case 'X_DOUBLE':
                elements.paramsContainer.innerHTML = `<p>Doubles X position for all bones</p>`;
                break;

            case 'EXTRACT_CSV':
                elements.paramsContainer.innerHTML = `<p>Extracts animation data to CSV format</p>`;
                break;
        }
    }

    populateBoneList() {
        elements.boneList.innerHTML = '';
        currentBoneCheckboxes.clear();

        Object.entries(BONE_MAP).forEach(([boneId, boneName]) => {
            const boneItem = document.createElement('div');
            boneItem.className = 'bone-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `bone-${boneId}`;
            checkbox.value = boneId;
            checkbox.checked = true;

            const label = document.createElement('label');
            label.htmlFor = `bone-${boneId}`;
            label.textContent = `${boneId}: ${boneName}`;

            boneItem.appendChild(checkbox);
            boneItem.appendChild(label);
            elements.boneList.appendChild(boneItem);

            currentBoneCheckboxes.set(parseInt(boneId), checkbox);
        });
    }

    toggleAllBones(selected) {
        currentBoneCheckboxes.forEach(checkbox => {
            checkbox.checked = selected;
        });
    }

    getSelectedBoneIds() {
        const selected = [];
        currentBoneCheckboxes.forEach((checkbox, boneId) => {
            if (checkbox.checked) selected.push(boneId);
        });
        return selected;
    }

    updateSplicerInfo() {
        // Placeholder for frame count updates
        // Would require file parsing to implement
    }

    showSettingsModal() {
        const prefs = this.loadPreferences();
        document.getElementById('exportExt').value = prefs.export_ext || '.bytes';
        elements.settingsModal.style.display = 'block';
    }

    hideSettingsModal() {
        elements.settingsModal.style.display = 'none';
    }

    saveSettings() {
        const prefs = {
            export_ext: document.getElementById('exportExt').value
        };
        this.savePreferences(prefs);
        this.hideSettingsModal();
        this.log("Settings saved");
    }

    loadPreferences() {
        try {
            return JSON.parse(localStorage.getItem('animation_tool_prefs')) || {};
        } catch {
            return {};
        }
    }

    savePreferences(prefs) {
        try {
            localStorage.setItem('animation_tool_prefs', JSON.stringify(prefs));
            return true;
        } catch {
            return false;
        }
    }

    async runOperation() {
        const operation = elements.operationSelect.value;
        
        // Validate inputs
        if (operation !== 'SPLICER' && !document.getElementById('inputFile').files[0]) {
            alert('Please select an animation file.');
            return;
        }

        if (operation === 'SPLICER') {
            const file1 = document.getElementById('splicerFile1').files[0];
            const file2 = document.getElementById('splicerFile2').files[0];
            if (!file1 || !file2) {
                alert('Please select both files for SPLICER operation.');
                return;
            }
        }

        this.clearLog();
        elements.runButton.disabled = true;
        elements.runButton.textContent = "Processing...";

        try {
            const cliArgs = await this.gatherCLIArguments();
            
            // Handle file uploads to virtual file system
            await this.uploadFilesToVFS();

            this.log(`Starting ${operation} operation...`);
            
            const run_web_operation = pyodide.globals.get('run_web_operation');
            const pyArgs = pyodide.toPy(cliArgs);
            
            const outputFilename = await run_web_operation(pyArgs);
            
            if (outputFilename) {
                this.downloadVFSFile(outputFilename);
                this.log("✅ Operation completed successfully!");
            } else {
                this.log("⚠️ Operation completed but no output file was returned.");
            }

        } catch (error) {
            this.log(`❌ Error: ${error.message}`);
            console.error(error);
        } finally {
            elements.runButton.disabled = false;
            elements.runButton.textContent = "Run Operation";
            this.cleanupVFS();
        }
    }

    async gatherCLIArguments() {
        const operation = elements.operationSelect.value;
        const args = {
            selected_operation: operation,
            save_csvs: document.getElementById('saveCSV').checked,
            export_extension: document.getElementById('exportExt').value || '.bytes'
        };

        switch(operation) {
            case 'SHORTEN':
            case 'LENGTHEN':
                args.factor = document.getElementById('factor').value;
                break;
            case 'DASH':
                args.offset_factor = document.getElementById('offsetFactor').value;
                args.direction = document.getElementById('dashDirection').value;
                break;
            case 'BIRTH_LOCATION':
                args.total_offset = document.getElementById('totalOffset').value;
                args.direction = document.getElementById('birthDirection').value;
                break;
            case 'TRIMMER':
                args.range = document.getElementById('trimRange').value;
                break;
            case 'AXIS_ADDER':
                args.x_offset = document.getElementById('xOffset').value;
                args.y_offset = document.getElementById('yOffset').value;
                args.z_offset = document.getElementById('zOffset').value;
                args.bone_id = document.getElementById('boneId').value;
                break;
            case 'AXIS_SCALER':
                args.scale_factor = document.getElementById('scaleFactor').value;
                args.target_bone_ids = this.getSelectedBoneIds();
                break;
            case 'SPLICER':
                args.file1 = document.getElementById('splicerFile1').files[0]?.name;
                args.file2 = document.getElementById('splicerFile2').files[0]?.name;
                args.range1 = document.getElementById('splicerRange1').value;
                args.range2 = document.getElementById('splicerRange2').value;
                break;
        }

        return args;
    }

    async uploadFilesToVFS() {
        const operation = elements.operationSelect.value;
        
        if (operation !== 'SPLICER') {
            const mainFile = document.getElementById('inputFile').files[0];
            if (mainFile) {
                const data = await this.readFileAsArrayBuffer(mainFile);
                pyodide.FS.writeFile(mainFile.name, new Uint8Array(data));
            }
        } else {
            // Handle SPLICER files
            const file1 = document.getElementById('splicerFile1').files[0];
            const file2 = document.getElementById('splicerFile2').files[0];
            
            if (file1) {
                const data1 = await this.readFileAsArrayBuffer(file1);
                pyodide.FS.writeFile(file1.name, new Uint8Array(data1));
            }
            if (file2) {
                const data2 = await this.readFileAsArrayBuffer(file2);
                pyodide.FS.writeFile(file2.name, new Uint8Array(data2));
            }
        }
    }

    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }

    downloadVFSFile(filename) {
        try {
            const fileData = pyodide.FS.readFile(filename, { encoding: 'binary' });
            const blob = new Blob([fileData], { type: 'application/octet-stream' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.log(`Downloaded: ${filename}`);
        } catch (error) {
            this.log(`Download error: ${error}`);
        }
    }

    cleanupVFS() {
        try {
            pyodide.FS.readdir('/').forEach(file => {
                if (file.endsWith('.bytes') || file.endsWith('.csv') || file.endsWith('.txt')) {
                    try {
                        pyodide.FS.unlink(file);
                    } catch (e) {
                        // Ignore cleanup errors
                    }
                }
            });
        } catch (error) {
            // Ignore cleanup errors
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.animationTool = new AnimationTool();
});
