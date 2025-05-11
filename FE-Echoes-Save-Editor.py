import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import json

def load_registry(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
##################### Load json ##################################
    
CHARACTER_ID_REGISTRY = load_registry("data/character_id_registry.json")
CLASS_ID_REGISTRY = load_registry("data/class_id_registry.json")
ITEM_ID_REGISTRY = load_registry("data/item_id_registry.json")

##################### Load json ##################################

def translate_id(value, registry):
    return f"{value} ({registry.get(value, 'Unknown')})"

##################### Debug Functions ############################

def print_all_class_ids(block_data):
    for i, block in enumerate(block_data):
        block_bytes = bytearray(block)
        class_id = block_bytes[11:19].hex().upper()
        print(f"Block {i+1}: Class ID = {class_id}")

def print_all_character_ids(block_data):
    for i, block in enumerate(block_data):
        block_bytes = bytearray(block)
        char_id = block_bytes[3:11].hex().upper()
        print(f"Block {i+1}: Character ID = {char_id}")

def print_all_items(block_data):
    for i, block in enumerate(block_data):
        block_bytes = bytearray(block)
        item = block_bytes[86:93].hex().upper()
        print(f"Block {i+1}: Item = {item}")


##################### Debug Functions ############################

def parse_block(block_bytes):
    def get_bytes(start, end):
        return block_bytes[start:end]

    def get_raw_hex_byte(pos):
        return f"{block_bytes[pos]:02X}"

    parsed = {}
    parsed['Marker'] = get_raw_hex_byte(0)
    parsed['Level'] = get_raw_hex_byte(1)
    parsed['EXP'] = get_raw_hex_byte(2)
    parsed['Character ID'] = get_bytes(3, 11).hex().upper()
    parsed['Class ID'] = get_bytes(11, 19).hex().upper()
    parsed['Supports'] = get_bytes(20, 24).hex().upper()
    parsed['HP'] = get_raw_hex_byte(24)
    parsed['Attack'] = get_raw_hex_byte(25)
    parsed['Skill'] = get_raw_hex_byte(26)
    parsed['Speed'] = get_raw_hex_byte(27)
    parsed['Luck'] = get_raw_hex_byte(28)
    parsed['Defense'] = get_raw_hex_byte(29)
    parsed['Resistance'] = get_raw_hex_byte(30)
    parsed['Movement'] = get_raw_hex_byte(31)
    parsed['Fatigue'] = get_raw_hex_byte(32)
    parsed['Item Skills Count'] = get_raw_hex_byte(49)
    parsed['Item Skills'] = get_bytes(50, 58).hex().upper()
    parsed['Item'] = get_bytes(86, 93).hex().upper()
    return parsed

def rebuild_block(parsed, original_block):
    block = bytearray(original_block)
    def set_bytes(start, end, value_hex):
        block[start:end] = bytes.fromhex(value_hex)
    def set_raw_hex_byte(pos, value_hex):
        block[pos] = int(value_hex, 16)

    set_raw_hex_byte(0, parsed['Marker'])
    set_raw_hex_byte(1, parsed['Level'])
    set_raw_hex_byte(2, parsed['EXP'])
    set_bytes(3, 11, parsed['Character ID'])
    set_bytes(11, 19, parsed['Class ID'])
    set_bytes(20, 24, parsed['Supports'])
    set_raw_hex_byte(24, parsed['HP'])
    set_raw_hex_byte(25, parsed['Attack'])
    set_raw_hex_byte(26, parsed['Skill'])
    set_raw_hex_byte(27, parsed['Speed'])
    set_raw_hex_byte(28, parsed['Luck'])
    set_raw_hex_byte(29, parsed['Defense'])
    set_raw_hex_byte(30, parsed['Resistance'])
    set_raw_hex_byte(31, parsed['Movement'])
    set_raw_hex_byte(32, parsed['Fatigue'])
    set_raw_hex_byte(49, parsed['Item Skills Count'])
    set_bytes(50, 58, parsed['Item Skills'])
    set_bytes(86, 93, parsed['Item'])
    return bytes(block)

class SaveEditorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Fire Emblem Echoes Save Editor")
        self.blocks = []
        self.block_data = []
        self.original_start = b''
        self.original_end = b''
        self.filename = ""

        tk.Button(master, text="Open Save File", command=self.load_file).pack(pady=5)
        self.listbox = tk.Listbox(master, width=80)
        self.listbox.pack(padx=10, pady=5)
        self.listbox.bind('<Double-1>', self.edit_selected_block)
        self.save_button = tk.Button(master, text="Save As...", command=self.save_file, state='disabled')
        self.save_button.pack(pady=5)

    def load_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        self.filename = file_path
        with open(file_path, "rb") as f:
            data = f.read()

        hex_string = data.hex().upper()
        tinu_index = hex_string.find("54494E55")
        if tinu_index == -1:
            messagebox.showerror("Error", "No TINU found in file.")
            return

        start_index = (tinu_index + 14) // 2
        current_index = start_index
        self.blocks = []
        self.block_data = []
        self.original_start = data[:start_index]
        self.original_end = b''

        while current_index < len(data):
            next_marker = hex_string.find("00000015", current_index * 2)
            if next_marker == -1:
                block = data[current_index: current_index + 105]
            else:
                next_marker_byte = next_marker // 2
                block = data[current_index: next_marker_byte + 3]
            parsed = parse_block(block)
            self.blocks.append(parsed)
            self.block_data.append(block)
            if next_marker == -1:
                self.original_end = data[current_index + 105:]
                break
            current_index = next_marker_byte + 3

        self.refresh_listbox()
        self.save_button.config(state='normal')

##################### Debug Functions ##################################
        
        print_all_class_ids(self.block_data)
        print_all_character_ids(self.block_data)
        print_all_items(self.block_data)
        
##################### Debug Functions ##################################

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, block in enumerate(self.blocks):
            char_name = CHARACTER_ID_REGISTRY.get(block['Character ID'], "Unknown")
            self.listbox.insert(tk.END, f"Block {i+1}: {char_name} ({block['Character ID']})")

    def edit_selected_block(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        block = self.blocks[index]

        editor = tk.Toplevel(self.master)
        editor.title(f"Edit Block {index+1}")
        fields = ["Level", "EXP", "Character ID", "Class ID", "Supports", "HP", "Attack", "Skill", "Speed", "Luck",
                  "Defense", "Resistance", "Movement", "Fatigue", "Item Skills Count", "Item Skills"] # Re-add "Item" here to edit items

        entries = {}
        for i, field in enumerate(fields):
            tk.Label(editor, text=field).grid(row=i, column=0, sticky="w")
            if field == "Character ID":
                combo = ttk.Combobox(editor, values=list(CHARACTER_ID_REGISTRY.values()), width=47)
                current_name = CHARACTER_ID_REGISTRY.get(block[field], "Unknown")
                combo.set(current_name)
                combo.grid(row=i, column=1)
                entries[field] = combo
            elif field == "Class ID":
                combo = ttk.Combobox(editor, values=list(CLASS_ID_REGISTRY.values()), width=47)
                current_name = CLASS_ID_REGISTRY.get(block[field], "Unknown")
                combo.set(current_name)
                combo.grid(row=i, column=1)
                entries[field] = combo
            elif field == "Item":
                combo = ttk.Combobox(editor, values=list(ITEM_ID_REGISTRY.values()), width=47)
                current_name = ITEM_ID_REGISTRY.get(block[field], "Unknown")
                combo.set(current_name)
                combo.grid(row=i, column=1)
                entries[field] = combo

            else:
                entry = tk.Entry(editor, width=50)
                entry.insert(0, block[field])
                entry.grid(row=i, column=1)
                entries[field] = entry

        def save_changes():
            try:
                for field in fields:
                    if field == "Character ID":
                        name = entries[field].get().strip()
                        id_lookup = {v: k for k, v in CHARACTER_ID_REGISTRY.items()}
                        if name not in id_lookup:
                            raise ValueError(f"Invalid Character Name: {name}")
                        block[field] = id_lookup[name]
                    elif field == "Class ID":
                        name = entries[field].get().strip()
                        id_lookup = {v: k for k, v in CLASS_ID_REGISTRY.items()}
                        if name not in id_lookup:
                            raise ValueError(f"Invalid Class Name: {name}")
                        block[field] = id_lookup[name]
                    elif field == "Item":
                        name = entries[field].get().strip()
                        id_lookup = {v: k for k, v in ITEM_ID_REGISTRY.items()}
                        if name not in id_lookup:
                            raise ValueError(f"Invalid Item Name: {name}")
                        block[field] = id_lookup[name]
                    else:
                        block[field] = entries[field].get().strip().upper()

                self.blocks[index] = block
                self.block_data[index] = rebuild_block(block, self.block_data[index])
                self.refresh_listbox()
                editor.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(editor, text="Save Changes", command=save_changes).grid(row=len(fields), columnspan=2, pady=5)

    def save_file(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".bin",
                                                 initialfile=os.path.splitext(os.path.basename(self.filename))[0] + "_modified")
        if not save_path:
            return
        with open(save_path, "wb") as f:
            f.write(self.original_start)
            for block in self.block_data:
                f.write(block)
            f.write(self.original_end)
        messagebox.showinfo("Success", f"File saved as: {save_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SaveEditorApp(root)
    root.mainloop()
