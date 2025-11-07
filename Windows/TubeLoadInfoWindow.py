# -*- coding: utf-8 -*-
"""
TubeLoadInfoWindow.py
발사관 무장 적재 정보 설정 및 전송
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from dds.AIEP_AIEP_ import TEWA_WA_TUBE_LOAD_INFO


WEAPON_TYPES = {
    "None": 0,
    "WGT (Torpedo)": 1,
    "M_MINE (Mine)": 2,
    "ASM (Anti-Ship)": 3,
    "ALM (Anti-Land)": 4,
    "AAM (Anti-Air)": 5,
}


def save_values_to_json(data, filename="tube_load_info.json"):
    """Save values to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        messagebox.showinfo("Save", f"Values saved to {filename}")
    except Exception as e:
        messagebox.showerror("Save Error", str(e))


def load_values_from_json(filename="tube_load_info.json"):
    """Load values from JSON file"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        messagebox.showerror("Load Error", str(e))
        return None


class TubeLoadInfoWindow(tk.Toplevel):
    """Tube Load Info Window"""
    
    def __init__(self, parent, publisher, main_gui):
        super().__init__(parent)
        self.title("Tube Load Information")
        self.geometry("500x400")
        
        self.publisher = publisher
        self.main_gui = main_gui
        
        # Tube load data: {tube_num: weapon_kind}
        self.tube_loads = {i: 0 for i in range(1, 7)}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        # Title
        title_label = tk.Label(
            self,
            text="Set Weapon Type for Each Tube",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=10)
        
        # Tube configuration frame
        config_frame = tk.LabelFrame(self, text="Tube Configuration", padx=10, pady=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tube_combos = {}
        
        for tube_num in range(1, 7):
            row_frame = tk.Frame(config_frame)
            row_frame.pack(fill=tk.X, pady=3)
            
            tk.Label(
                row_frame,
                text=f"Tube {tube_num}:",
                width=10,
                anchor="w"
            ).pack(side=tk.LEFT, padx=5)
            
            combo = ttk.Combobox(
                row_frame,
                values=list(WEAPON_TYPES.keys()),
                state="readonly",
                width=20
            )
            combo.set("None")
            combo.pack(side=tk.LEFT, padx=5)
            
            self.tube_combos[tube_num] = combo
        
        # Button frame
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="Send All",
            command=self.send_all_tube_loads,
            width=12,
            bg="lightgreen"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Send Selected",
            command=self.send_selected_tube,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Save to JSON",
            command=self.save_to_json,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Load from JSON",
            command=self.load_from_json,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # Info label
        info_label = tk.Label(
            self,
            text="Note: Send All will send load info for all 6 tubes.\n"
                 "Send Selected will send only the currently selected tube.",
            font=("Arial", 8),
            fg="blue",
            wraplength=450,
            justify=tk.LEFT
        )
        info_label.pack(pady=5)
    
    def send_all_tube_loads(self):
        """Send load info for all tubes"""
        try:
            # Read all tube configurations
            for tube_num in range(1, 7):
                weapon_name = self.tube_combos[tube_num].get()
                weapon_kind = WEAPON_TYPES[weapon_name]
                
                # Create and send message
                msg = TEWA_WA_TUBE_LOAD_INFO()
                msg.eTubeNum = tube_num
                msg.eWpnKind = weapon_kind
                
                self.publisher.publish_TEWA_WA_TUBE_LOAD_INFO(msg)
                
                # Save to main GUI
                if not hasattr(self.main_gui, 'tube_load_info_data'):
                    self.main_gui.tube_load_info_data = {}
                self.main_gui.tube_load_info_data[tube_num] = weapon_kind
            
            messagebox.showinfo("Success", "All tube load info sent!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send: {e}")
    
    def send_selected_tube(self):
        """Send load info for selected tube only"""
        # Create dialog to select tube
        dialog = tk.Toplevel(self)
        dialog.title("Select Tube")
        dialog.geometry("200x150")
        
        tk.Label(dialog, text="Select Tube Number:").pack(pady=10)
        
        tube_var = tk.IntVar(value=1)
        for tube_num in range(1, 7):
            tk.Radiobutton(
                dialog,
                text=f"Tube {tube_num}",
                variable=tube_var,
                value=tube_num
            ).pack(anchor=tk.W, padx=20)
        
        def send():
            try:
                tube_num = tube_var.get()
                weapon_name = self.tube_combos[tube_num].get()
                weapon_kind = WEAPON_TYPES[weapon_name]
                
                # Create and send message
                msg = TEWA_WA_TUBE_LOAD_INFO()
                msg.eTubeNum = tube_num
                msg.eWpnKind = weapon_kind
                
                self.publisher.publish_TEWA_WA_TUBE_LOAD_INFO(msg)
                
                # Save to main GUI
                if not hasattr(self.main_gui, 'tube_load_info_data'):
                    self.main_gui.tube_load_info_data = {}
                self.main_gui.tube_load_info_data[tube_num] = weapon_kind
                
                messagebox.showinfo("Success", f"Tube {tube_num} load info sent!")
                dialog.destroy()
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send: {e}")
        
        tk.Button(dialog, text="Send", command=send).pack(pady=10)
    
    def save_to_json(self):
        """Save values to JSON"""
        try:
            data = {}
            for tube_num in range(1, 7):
                weapon_name = self.tube_combos[tube_num].get()
                data[f"tube_{tube_num}"] = weapon_name
            
            save_values_to_json(data)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
    
    def load_from_json(self):
        """Load values from JSON"""
        try:
            data = load_values_from_json()
            if data is None:
                return
            
            for tube_num in range(1, 7):
                weapon_name = data.get(f"tube_{tube_num}", "None")
                if weapon_name in WEAPON_TYPES:
                    self.tube_combos[tube_num].set(weapon_name)
            
            messagebox.showinfo("Load", "Values loaded from JSON.")
        
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
