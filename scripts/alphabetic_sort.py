import json
import os
from collections import OrderedDict
import sys
import traceback

def sort_json(obj):
    if isinstance(obj, dict):
        sorted_dict = OrderedDict()
        for key in sorted(obj.keys()):
            sorted_dict[key] = sort_json(obj[key])
        return sorted_dict
    elif isinstance(obj, list):
        return [sort_json(element) for element in obj]
    else:
        return obj

def sanity_check(input_json, output_json):
    """Compares all keys and values of the input and output JSON"""
    if input_json.keys() != output_json.keys():
        return False
    for key in input_json:
        if isinstance(input_json[key], dict) and isinstance(output_json[key], dict):
            if not sanity_check(input_json[key], output_json[key]):
                return False
        elif input_json[key] != output_json[key]:
            return False
    return True

def main():
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    config_path = os.path.join('..', 'scripts_config.json')

    if not os.path.exists(config_path):
        print(f"Configuration file not found at {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)

    script_config = config.get(script_name)
    if script_config is None:
        print(f"No configuration found for script: {script_name}")
        sys.exit(1)

    input_folder = script_config.get('input_folder')
    output_folder = script_config.get('output_folder')

    if not input_folder or not output_folder:
        print("Configuration must include 'input_folder' and 'output_folder'.")
        sys.exit(1)

    os.makedirs(output_folder, exist_ok=True)
    
    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            with open(input_path, 'r', encoding='utf-8') as infile:
                try:
                    data = json.load(infile)
                except json.JSONDecodeError:
                    print(f"JSON decode error in file: {filename}")
                    continue

            sorted_data = sort_json(data)

            if not sanity_check(data, sorted_data):
                print(f"Sanity check failed for file: {filename}")
                sys.exit(1)

            with open(output_path, 'w', encoding='utf-8') as outfile:
                json.dump(sorted_data, outfile, indent=4, ensure_ascii=False, quote_keys=True)  # <-- FIX: ensure_ascii=False preserves proper JSON format
                outfile.write('\n')

if __name__ == "__main__":
    try:
        main()
        print("Script finished successfully.")
    except Exception as e:
        error_message = traceback.format_exc()
        print("An error occurred:\n", error_message)
    finally:
        input("\nPress Enter to exit...")
