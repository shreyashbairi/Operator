# #Operator/executor.py

# This script is responsible for executing the actions specified by the assistant. 
# It loads scripts from the scripts folder, executesthem with the provided parameters, 
# and returns the result. The execute_action function takes a JSON string as input, 
# extracts the action and parameters, and executes the corresponding script. 
# It uses subprocess to run the scripts and returns True if successful, False otherwise.
# The load_scripts function scans the scripts folder for available scripts and 
# maps them to actions based on the script filename. The execute_script function 
# takes an action and parameters, finds the corresponding script, expands user paths,
# and executes the script with the parameters as arguments. The main interface for 
# the assistant is the execute_action function, which processes the JSON input,
# extracts the action and parameters, and calls execute_script to run the corresponding script.
# If an error occurs during execution, it returns False.


import os
import json
import subprocess
import shutil

# Constants
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

# ------------------------------------------------------------------------------
# Script Loading Utilities
# ------------------------------------------------------------------------------

def load_scripts():
    """Scan scripts directory and map filenames to action names"""
    script_map = {}
    if not os.path.isdir(SCRIPTS_DIR):
        return script_map

    for script_file in os.listdir(SCRIPTS_DIR):
        if script_file.startswith("."):
            continue  # Skip hidden files

        action_name, _ = os.path.splitext(script_file)
        script_path = os.path.join(SCRIPTS_DIR, script_file)
        script_map[action_name] = script_path
    
    return script_map

ACTION_SCRIPTS = load_scripts()

# ------------------------------------------------------------------------------
# Execution Core
# ------------------------------------------------------------------------------

# Required parameters for common actions
REQUIRED_PARAMS = {
    "delete_file": ["path"],
    "move_file": ["source", "destination"],
    "create_folder": ["path"],
    "kill_process": ["target"],
    "list_processes": []
}

def validate_parameters(action, params):
    """Verify required parameters and check for user input placeholders"""
    # Check required parameters
    if required := REQUIRED_PARAMS.get(action):
        if missing := [p for p in required if p not in params]:
            print(f"Missing parameters for {action}: {missing}")
            return False

    # Check for placeholders needing user input
    if ask_params := [k for k, v in params.items() if str(v).strip().upper() == "ASK_USER"]:
        print(f"Action '{action}' requires user input for: {', '.join(ask_params)}")
        return False

    return True

def execute_script(action, params):
    """
    Execute script for given action with parameters
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not (script_path := ACTION_SCRIPTS.get(action)):
        print(f"No script found for action '{action}'")
        return False

    if not validate_parameters(action, params):
        return False

    # Prepare parameters with path expansion
    expanded_params = [os.path.expanduser(str(v)) for v in params.values()]
    _, extension = os.path.splitext(script_path)

    # Build appropriate execution command
    if extension == ".scpt":
        cmd = ["osascript", script_path] + expanded_params
    elif extension == ".sh":
        cmd = ["bash", script_path] + expanded_params
    elif extension == ".py":
        cmd = ["python3", script_path] + expanded_params
    else:
        cmd = [script_path] + expanded_params  # Direct execution

    print(f"Executing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Script execution failed: {str(e)}")
        return False

# ------------------------------------------------------------------------------
# Public Interface
# ------------------------------------------------------------------------------

def execute_action(json_str):
    """Main execution entry point - processes JSON commands"""
    try:
        command = json.loads(json_str)
        if action := command.get("action"):
            return execute_script(action, command.get("params", {}))
        print("JSON missing 'action' field")
    except Exception as e:
        print(f"Execution error: {str(e)}")
    return False

# ------------------------------------------------------------------------------
# Testing Harness
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test script execution')
    parser.add_argument('--action', required=True, help='Action name')
    parser.add_argument('--params', type=json.loads, required=True, 
                       help='JSON parameters string')
    args = parser.parse_args()

    result = execute_script(args.action, args.params)
    print(f"Execution {'succeeded' if result else 'failed'}")

#     # to run script directly, use:
#     #python3 executor.py --action copy_file --params '{"path": "~/Desktop/test.txt"}'