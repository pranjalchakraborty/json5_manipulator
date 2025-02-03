import json5 as json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess

class JSONEditor:
    def __init__(self, master, json_data, json_path):
        self.master = master
        self.master.title("JSON Editor")
        self.json_data = json_data
        self.json_path = json_path
        self.entries = {}

        # Top frame for Save button
        top_frame = ttk.Frame(master)
        top_frame.pack(fill="x", padx=10, pady=5)

        save_button = ttk.Button(top_frame, text="Save", command=self.save_json)
        save_button.pack(side="right")

        # Create a canvas and a scrollbar
        self.canvas = tk.Canvas(master)
        self.scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Populate the GUI with JSON data
        self.build_gui(self.scrollable_frame, self.json_data)

    def build_gui(self, parent, data):
        if isinstance(data, dict):
            for top_key, top_value in data.items():
                frame = ttk.LabelFrame(parent, text=top_key)
                frame.pack(fill="x", padx=10, pady=5, anchor="w")

                if isinstance(top_value, dict):
                    self.build_sub_gui(frame, top_key, top_value)
                else:
                    self.build_entry(frame, top_key, top_value, parent_key='')

                # Add Run Button for this top_key
                run_button = ttk.Button(frame, text="Run", command=lambda tk=top_key: self.run_executable(tk))
                run_button.pack(pady=5, anchor="e")
        else:
            messagebox.showerror("Error", "The JSON root must be an object/dictionary.")

    def build_sub_gui(self, parent, top_key, data):
        for key, value in data.items():
            frame = ttk.Frame(parent)
            frame.pack(fill="x", padx=5, pady=2)

            label = ttk.Label(frame, text=key, width=20, anchor="w")
            label.pack(side="left")

            entry = ttk.Entry(frame)
            entry.insert(0, str(value))
            entry.pack(side="left", fill="x", expand=True)

            full_key = f"{top_key}.{key}"
            self.entries[full_key] = entry

    def build_entry(self, parent, key, value, parent_key):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)

        label = ttk.Label(frame, text=key, width=20, anchor="w")
        label.pack(side="left")

        entry = ttk.Entry(frame)
        entry.insert(0, str(value))
        entry.pack(side="left", fill="x", expand=True)

        full_key = f"{parent_key}{key}" if parent_key else key
        self.entries[full_key] = entry

    def save_json(self):
        try:
            updated_data = self.json_data.copy()
            for full_key, entry in self.entries.items():
                keys = full_key.split('.')
                sub_data = updated_data
                for key in keys[:-1]:
                    sub_data = sub_data[key]
                final_key = keys[-1]
                new_value = entry.get()

                # Try to interpret the type
                try:
                    # Attempt to parse as JSON
                    parsed_value = json.loads(new_value)
                except:
                    # Fallback to string
                    parsed_value = new_value

                sub_data[final_key] = parsed_value

            # Save to file
            with open(self.json_path, 'w') as f:
                json.dump(updated_data, f, indent=4)

            messagebox.showinfo("Success", f"JSON saved to {self.json_path}")
            return updated_data
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON:\n{e}")
            return None

    def run_executable(self, top_key):
        # Save the JSON first
        updated_data = self.save_json()
        if updated_data is None:
            return  # Save failed

        exe_name = f"{top_key}.exe"
        exe_directory = "./scripts"
        exe_path = os.path.join(exe_directory, exe_name)

        if not os.path.isfile(exe_path):
            messagebox.showerror("Error", f"Executable '{exe_name}' not found in '{exe_directory}'.")
            return

        try:
            # Run the executable
            subprocess.Popen([exe_path], cwd=exe_directory)
            messagebox.showinfo("Success", f"Executed '{exe_name}' successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute '{exe_name}':\n{e}")

def load_json_file():
    file_path = filedialog.askopenfilename(
        title="Select JSON File",
        filetypes=(("JSON Files", "*.json"), ("All Files", "*.*"))
    )
    if file_path:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data, file_path
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON:\n{e}")
            return None, None
    return None, None

def main():
    root = tk.Tk()
    root.title("JSON Editor Launcher")
    root.geometry("400x200")

    # Add a frame for loading JSON
    load_frame = ttk.Frame(root)
    load_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def open_editor():
        data, path = load_json_file()
        if data and path:
            editor_window = tk.Toplevel(root)
            editor_window.title("JSON Editor")
            editor_window.geometry("600x400")
            editor = JSONEditor(editor_window, data, path)

    load_button = ttk.Button(load_frame, text="Load JSON File", command=open_editor)
    load_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
