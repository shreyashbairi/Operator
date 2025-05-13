#Operator/executor.py
# This script is responsible for executing the actions specified by the assistant. It loads scripts from the scripts folder, executes
# them with the provided parameters, and returns the result. The execute_action function takes a JSON string as input, extracts the action
# and parameters, and executes the corresponding script. It uses subprocess to run the scripts and returns True if successful, False otherwise.
# The load_scripts function scans the scripts folder for available scripts and maps them to actions based on the script filename. The execute_script
# function takes an action and parameters, finds the corresponding script, expands user paths, and executes the script with the parameters as arguments.
# The main interface for the assistant is the execute_action function, which processes the JSON input, extracts the action and parameters, and calls
# execute_script to run the corresponding script. If an error occurs during execution, it returns False.

import os
import json
import subprocess
import shutil

# ------------------------------------------------------------------------------
# 1. Dynamically load scripts from the 'scripts' folder
#    The 'action' name is the script's base filename (no extension).
# ------------------------------------------------------------------------------

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
ACTION_HISTORY = []

def load_scripts():
    """
    Scans the SCRIPTS_DIR for any files (e.g. 'delete_file.scpt', 'move_file.sh')
    and maps them to actions, e.g. 'delete_file' -> full path to script.
    """
    script_map = {}
    if os.path.isdir(SCRIPTS_DIR):
        for script_file in os.listdir(SCRIPTS_DIR):
            # Ignore hidden/system files
            if script_file.startswith("."):
                continue

            action_name, ext = os.path.splitext(script_file)
            full_path = os.path.join(SCRIPTS_DIR, script_file)
            script_map[action_name] = full_path
    return script_map

ACTION_SCRIPTS = load_scripts()


# ------------------------------------------------------------------------------
# 2. Execute a script by name + pass in the params as argv
# ------------------------------------------------------------------------------

def test_script(action, params):
    print(f"Testing script: {action} with params: {params}")
    return execute_script(action, params)

def execute_script(action, params):
    """
    Given an action (e.g. "delete_file") and a params dict 
    (e.g. {"path": "~/Desktop/test.txt"}),
    find the corresponding script in ACTION_SCRIPTS and run it.
    Pass the params as command-line arguments, in the order they appear in the dict.
    """
    
    script_path = ACTION_SCRIPTS.get(action)
    if not script_path:
        print(f"No script found for action '{action}'")
        return False

    # Expand user (~) in all param values
    expanded_params = [os.path.expanduser(str(value)) for value in params.values()]

    _, ext = os.path.splitext(script_path)

    if ext == ".scpt":
        # AppleScript -> osascript
        cmd = ["osascript", script_path] + expanded_params
    elif ext == ".sh":
        # Shell script
        cmd = ["bash", script_path] + expanded_params
    elif ext == ".py":
        # Python script
        cmd = ["python3", script_path] + expanded_params
    else:
        # Fallback to trying to execute directly (chmod +x might be needed)
        cmd = [script_path] + expanded_params

    print("Executing:", cmd)
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Script execution failed: {str(e)}")
        return False


# ------------------------------------------------------------------------------
# 3. Main interface for the assistant
# ------------------------------------------------------------------------------

def execute_action(json_str):
    try:
        command = json.loads(json_str)
        action = command.get("action")
        params = command.get("params", {})

        if action:
            return execute_script(action, params)
        else:
            print("JSON missing 'action' field.")
    except Exception as e:
        print(f"Error in execute_action: {str(e)}")

    return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test scripts directly')
    parser.add_argument('--action', required=True, help='Action name')
    parser.add_argument('--params', type=json.loads, required=True, 
                       help='JSON parameters string')
    args = parser.parse_args()

    result = execute_script(args.action, args.params)
    print(f"Execution {'succeeded' if result else 'failed'}")

    # to run script directly, use:
    #python3 executor.py --action copy_file --params '{"path": "~/Desktop/test.txt"}'