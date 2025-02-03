import os
import json5 as json
import sys
import traceback

def load_json(filepath):
    """Load JSON data from a file."""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_item_set(data, id_key):
    """Extract a set of 'item' values for a given ID."""
    items = data.get(id_key, {}).get("items", [])
    return set(item.get("item") for item in items if "item" in item)

def get_full_item_objects(data, id_key, added_items):
    """Retrieve full item objects for the added IDDs."""
    items = data.get(id_key, {}).get("items", [])
    # Filter items where 'item' is in added_items
    return [item for item in items if item.get("item") in added_items]

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

    # List all JSON files in input_folder
    for filename in os.listdir(input_folder):
        if not filename.endswith('.json'):
            continue  # Skip non-JSON files

        path1 = os.path.join(input_folder, filename)
        path2 = os.path.join(change_folder, filename)

        # Check if corresponding file exists in change_folder
        if not os.path.exists(path2):
            print(f"Skipping {filename}: not found in folder '{change_folder}'.")
            continue

        try:
            json1 = load_json(path1)
            json2 = load_json(path2)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for file {filename}: {e}")
            continue

        data1 = json1.get("data", {})
        data2 = json2.get("data", {})

        # Initialize reports
        extra_ids = set(data2.keys()) - set(data1.keys())
        common_ids = set(data2.keys()).intersection(set(data1.keys()))
        idd_report = {}
        extra_ids_full = {}
        idd_full_objects = {}

        # Collect Extra Top-Level IDs and their full objects
        if extra_ids:
            extra_ids_full = {id_key: data2[id_key] for id_key in extra_ids}

        # Now, for IDs present in both, check for extra IDDs
        for id_key in common_ids:
            items2 = get_item_set(data2, id_key)
            items1 = get_item_set(data1, id_key)

            added_items = items2 - items1
            if added_items:
                # Retrieve full item objects for added IDDs
                added_item_objects = get_full_item_objects(data2, id_key, added_items)
                idd_report[id_key] = sorted(added_items)
                idd_full_objects[id_key] = added_item_objects

        # Check if there are any changes
        if extra_ids or idd_report:
            # Prepare the .txt filename
            txt_filename = os.path.splitext(filename)[0] + '.txt'
            txt_path = os.path.join(output_folder, txt_filename)

            # Format the report as per the desired sequence
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                # 1. List of Added Top-Level IDs
                if extra_ids:
                    txt_file.write("=== List of Added Top-Level IDs ===\n")
                    for extra_id in sorted(extra_ids):
                        txt_file.write(f"- {extra_id}\n")
                    txt_file.write("\n")

                # 2. List of Added IDDs Under Existing IDs
                if idd_report:
                    txt_file.write("=== List of Added IDDs Under Existing IDs ===\n")
                    for id_key in sorted(idd_report.keys()):
                        txt_file.write(f"ID: {id_key}\n")
                        for added_idd in idd_report[id_key]:
                            txt_file.write(f"  - {added_idd}\n")
                    txt_file.write("\n")

                # 3. Full Objects of Added Top-Level IDs
                if extra_ids_full:
                    txt_file.write("=== Full Objects of Added Top-Level IDs ===\n")
                    for extra_id, obj in sorted(extra_ids_full.items()):
                        txt_file.write(f"ID: {extra_id}\n")
                        txt_file.write("Full Object:\n")
                        # Pretty-print the JSON object with indentation
                        obj_pretty = json.dumps(obj, indent=4, ensure_ascii=False, quote_keys=True)
                        # Indent each line for better readability
                        obj_pretty_indented = '\n'.join(['    ' + line for line in obj_pretty.splitlines()])
                        txt_file.write(f"{obj_pretty_indented}\n\n")

                # 4. Full Objects of Added IDDs
                if idd_full_objects:
                    txt_file.write("=== Full Objects of Added IDDs ===\n")
                    for id_key, items in sorted(idd_full_objects.items()):
                        txt_file.write(f"ID: {id_key}\n")
                        for item in items:
                            # Pretty-print each item object
                            item_pretty = json.dumps(item, indent=4, ensure_ascii=False, quote_keys=True)
                            # Indent each line for better readability
                            item_pretty_indented = '\n'.join(['    ' + line for line in item_pretty.splitlines()])
                            txt_file.write(f"  - {item_pretty_indented}\n")
                        txt_file.write("\n")  # Add space between IDs

            print(f"Changes found in '{filename}'. Report saved to '{txt_path}'.")
        else:
            print(f"No changes found in '{filename}'.")

if __name__ == "__main__":
    try:
        main()
        print("Script finished successfully.")
    except Exception as e:
        error_message = traceback.format_exc()  # Capture full traceback
        print("An error occurred:\n", error_message)  # Print explicitly
    finally:
        input("\nPress Enter to exit...")

