#!/usr/bin/env python3
import os
import json5 as json
import shutil
from pathlib import Path
import sys
import traceback

def load_json(file_path):
    """Safely load JSON from a file, returning None on error."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not load {file_path}: {e}")
        return None

def save_json(data, file_path):
    """Save Python object as JSON with indentation."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False, quote_keys=True)
    except Exception as e:
        print(f"Could not save {file_path}: {e}")

def merge_string_arrays(parent_list, delta_list, strategy):
    """Merge two lists of strings according to the specified strategy."""
    if strategy == "ignore":
        return parent_list
    elif strategy == "merge":
        # Merge uniquely
        return list(set(parent_list + delta_list))
    elif strategy == "replace":
        # Replace entirely
        return delta_list
    # Fallback
    return parent_list

def merge_object_arrays(parent_list, delta_list, new_id_strategy):
    """
    Merge arrays of objects based on 'item' as an identifier.
    If delta has an object with an 'item' that doesn't exist in parent,
    it is added (if new_id_strategy == 'merge').
    """
    parent_dict = {}
    delta_dict = {}

    for obj in parent_list:
        if isinstance(obj, dict) and "item" in obj:
            parent_dict[obj["item"]] = obj

    for obj in delta_list:
        if isinstance(obj, dict) and "item" in obj:
            delta_dict[obj["item"]] = obj

    for key, val in delta_dict.items():
        if key in parent_dict:
            # Recursively merge the two objects
            parent_dict[key] = merge_json(parent_dict[key], val,
                                          array_merge_strategy="merge",
                                          new_id_strategy=new_id_strategy)
        else:
            if new_id_strategy == "merge":
                parent_dict[key] = val

    return list(parent_dict.values())

def merge_json(parent, delta,
               array_merge_strategy="merge",
               new_id_strategy="merge",
               excluded_fields=None):
    """
    Recursively merge 'delta' into 'parent'.
      - array_merge_strategy in {ignore, merge, replace}
      - new_id_strategy in {ignore, merge}
      - excluded_fields is a list of field names to skip entirely
    """
    if excluded_fields is None:
        excluded_fields = []

    if isinstance(parent, dict) and isinstance(delta, dict):
        for key, value in delta.items():
            # Skip excluded fields
            if key in excluded_fields:
                continue

            # If key not present in parent
            if key not in parent:
                if new_id_strategy == "merge":
                    parent[key] = value
                continue

            # If value is a dict, merge it into parent[key]
            if isinstance(value, dict):
                parent[key] = merge_json(
                    parent.get(key, {}),
                    value,
                    array_merge_strategy=array_merge_strategy,
                    new_id_strategy=new_id_strategy,
                    excluded_fields=excluded_fields
                )
            # If value is a list
            elif isinstance(value, list):
                # If it's an array of dicts, merge object arrays
                if len(value) > 0 and all(isinstance(item, dict) for item in value):
                    parent[key] = merge_object_arrays(
                        parent.get(key, []),
                        value,
                        new_id_strategy
                    )
                # If it's an array of strings, merge string arrays
                elif len(value) > 0 and all(isinstance(item, str) for item in value):
                    parent[key] = merge_string_arrays(
                        parent.get(key, []),
                        value,
                        array_merge_strategy
                    )
                else:
                    # Otherwise, replace the list entirely
                    parent[key] = value
            # If scalar (int, float, str, bool, etc.), just update
            else:
                parent[key] = value

    return parent

def process_folders(folder_1, folder_2, folder_3,
                    excluded_files=None,
                    array_merge_strategy="merge",
                    new_id_strategy="merge",
                    excluded_fields=None):
    """
    Recursively walk 'folder_1' (parent JSONs) and 'folder_2' (delta JSONs),
    merge them, and output into 'folder_3'.
    """
    if excluded_files is None:
        excluded_files = []
    if excluded_fields is None:
        excluded_fields = []

    folder_1_path = Path(folder_1)
    folder_2_path = Path(folder_2)
    folder_3_path = Path(folder_3)

    folder_3_path.mkdir(parents=True, exist_ok=True)

    # Traverse folder_1
    for root, _, files in os.walk(folder_1_path):
        # Calculate relative path to replicate structure in folder_3
        relative = Path(root).relative_to(folder_1_path)
        target_dir = folder_3_path / relative
        target_dir.mkdir(parents=True, exist_ok=True)

        for file_name in files:
            if file_name in excluded_files:
                continue

            source_1 = folder_1_path / relative / file_name
            source_2 = folder_2_path / relative / file_name
            dest_3 = target_dir / file_name

            # Only merge if JSON
            if source_1.suffix.lower() == ".json":
                parent_data = load_json(source_1)
                delta_data = load_json(source_2) if source_2.exists() else None

                if parent_data is None:
                    # If we can't load parent, just copy it over
                    shutil.copy(source_1, dest_3)
                    continue

                if delta_data is not None:
                    merged = merge_json(
                        parent_data,
                        delta_data,
                        array_merge_strategy=array_merge_strategy,
                        new_id_strategy=new_id_strategy,
                        excluded_fields=excluded_fields
                    )
                    save_json(merged, dest_3)
                else:
                    # No delta file -> just copy parent
                    save_json(parent_data, dest_3)
            else:
                # For non-JSON, just copy
                if source_1.is_file():
                    shutil.copy2(source_1, dest_3)

def main():
    # Example usage:
    # python merge_script.py
    
    # You can either hard-code or parse command-line arguments here.
    
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

    process_folders(
        input_folder,
        change_folder,
        output_folder,
        excluded_files=None,
        array_merge_strategy=array_merge_strategy,
        new_id_strategy=new_id_strategy,
        excluded_fields=excluded_fields
    )
    print("Done merging.")

if __name__ == "__main__":
    try:
        main()
        print("Script finished successfully.")
    except Exception as e:
        error_message = traceback.format_exc()  # Capture full traceback
        print("An error occurred:\n", error_message)  # Print explicitly
    finally:
        input("\nPress Enter to exit...")



