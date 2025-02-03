import os
import json5 as json
import re
import sys
import traceback

def remove_trailing_commas(json_str):
    """
    Removes trailing commas that may appear before closing brackets or braces.
    E.g. "[ {...}, {...}, ]" -> "[ {...}, {...} ]"
    """
    pattern = r',\s*(\]|\})'
    return re.sub(pattern, r'\1', json_str)

def process_json_files(input_folder, output_folder):
    """
    Processes all JSON files in the input_folder by removing trailing commas
    and saves the cleaned JSON files to the output_folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for root, _, files in os.walk(input_folder):
        # Determine the relative path to maintain folder structure
        relative_path = os.path.relpath(root, input_folder)
        target_folder = os.path.join(output_folder, relative_path)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        for filename in files:
            if filename.lower().endswith('.json'):
                input_path = os.path.join(root, filename)
                output_path = os.path.join(target_folder, filename)

                with open(input_path, 'r', encoding='utf-8') as f:
                    data_str = f.read()

                cleaned_str = remove_trailing_commas(data_str)

                with open(output_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(cleaned_str)

def main():
    # Get the script name without the .py extension
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    
    # Define the path to config.json relative to the script's location
    config_path = os.path.join('..', 'scripts_config.json')  # Adjust the path as needed
    
    # Check if config.json exists
    if not os.path.exists(config_path):
        print(f"Configuration file not found at {config_path}")
        sys.exit(1)
    
    # Load the JSON configuration
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    
    # Retrieve the configuration for the current script
    script_config = config.get(script_name)
    if script_config is None:
        print(f"No configuration found for script: {script_name}")
        sys.exit(1)
    
    # Dynamically assign configuration parameters as variables
    for key, value in script_config.items():
        globals()[key] = value

    process_json_files(input_folder, output_folder)
    print(f"Trailing commas removed. Cleaned files are saved in '{output_folder}'.")

if __name__ == "__main__":
    try:
        main()
        print("Script finished successfully.")
    except Exception as e:
        error_message = traceback.format_exc()  # Capture full traceback
        print("An error occurred:\n", error_message)  # Print explicitly
    finally:
        input("\nPress Enter to exit...")
