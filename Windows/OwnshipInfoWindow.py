# -*- coding: utf-8 -*-
"""
OwnshipInfoWindow.py
자함 정보 설정 및 전송
"""

import tkinter as tk
from tkinter import messagebox
import json
from dds.AIEP_AIEP_ import NAVINF_SHIP_NAVIGATION_INFO


def save_values_to_json(data, filename="ownship_info.json"):
    """Save values to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        messagebox.showinfo("Save", f"Values saved to {filename}")
    except Exception as e:
        messagebox.showerror("Save Error", str(e))


def load_values_from_json(filename="ownship_info.json"):
    """Load values from JSON file"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        messagebox.showerror("Load Error", str(e))
        return None


class OwnshipInfoWindow(tk.Toplevel):
    """Ownship Navigation Info Window"""
    
    def __init__(self, parent, publisher, main_gui):
        super().__init__(parent)
        self.title("Ownship Navigation Info")
        self.geometry("400x350")
        
        self.publisher = publisher
        self.main_gui = main_gui  # Reference to main GUI
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        # Ship Movement Info Frame
        movement_frame = tk.LabelFrame(self, text="Ship Movement Info", padx=10, pady=5)
        movement_frame.pack(fill=tk.BOTH, padx=10, pady=5)
        
        fields = [
            ("Latitude (deg):", "lat"),
            ("Longitude (deg):", "lon"),
            ("Depth (m):", "depth"),
            ("Speed (m/s):", "speed"),
            ("Heading (deg):", "heading"),
        ]
        
        self.entries = {}
        for i, (label_text, key) in enumerate(fields):
            tk.Label(movement_frame, text=label_text).grid(
                row=i, column=0, sticky="w", padx=5, pady=3
            )
            entry = tk.Entry(movement_frame, width=20)
            entry.grid(row=i, column=1, padx=5, pady=3)
            self.entries[key] = entry
        
        # Default values
        self.entries["lat"].insert(0, "35.0")
        self.entries["lon"].insert(0, "129.0")
        self.entries["depth"].insert(0, "50.0")
        self.entries["speed"].insert(0, "5.0")
        self.entries["heading"].insert(0, "0.0")
        
        # Button frame
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="Send",
            command=self.send_ownship_info,
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
            text="Note: This ownship info will be used in engagement plan viewer.\n"
                 "If not set, external NAVINF message will be used.",
            font=("Arial", 8),
            fg="blue",
            wraplength=350,
            justify=tk.LEFT
        )
        info_label.pack(pady=5)
    
    def send_ownship_info(self):
        """Send ownship navigation info"""
        try:
            # Read values
            lat = float(self.entries["lat"].get())
            lon = float(self.entries["lon"].get())
            depth = float(self.entries["depth"].get())
            speed = float(self.entries["speed"].get())
            heading = float(self.entries["heading"].get())
            
            # Create message
            msg = NAVINF_SHIP_NAVIGATION_INFO()
            msg.stShipMovementInfo.dShipLatitude = lat
            msg.stShipMovementInfo.dShipLongitude = lon
            msg.stShipMovementInfo.fShipDepth = depth
            msg.stUnderwaterEnvironmentInfo.fDivingDepth = depth
            msg.stShipMovementInfo.fShipSpeed = speed
            msg.stShipMovementInfo.fShipHeading = heading
            
            # Send message
            self.publisher.publish_NAVINF_SHIP_NAVIGATION_INFO(msg)
            
            # Save to main GUI for simulator use
            self.main_gui.ownship_info_data = msg
            
            messagebox.showinfo("Success", "Ownship info sent and saved!")
        
        except ValueError:
            messagebox.showerror("Error", "Invalid input! Please enter valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send: {e}")
    
    def save_to_json(self):
        """Save values to JSON"""
        try:
            data = {
                "lat": self.entries["lat"].get(),
                "lon": self.entries["lon"].get(),
                "depth": self.entries["depth"].get(),
                "speed": self.entries["speed"].get(),
                "heading": self.entries["heading"].get(),
            }
            save_values_to_json(data)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
    
    def load_from_json(self):
        """Load values from JSON"""
        try:
            data = load_values_from_json()
            if data is None:
                return
            
            self.entries["lat"].delete(0, tk.END)
            self.entries["lat"].insert(0, data.get("lat", ""))
            
            self.entries["lon"].delete(0, tk.END)
            self.entries["lon"].insert(0, data.get("lon", ""))
            
            self.entries["depth"].delete(0, tk.END)
            self.entries["depth"].insert(0, data.get("depth", ""))
            
            self.entries["speed"].delete(0, tk.END)
            self.entries["speed"].insert(0, data.get("speed", ""))
            
            self.entries["heading"].delete(0, tk.END)
            self.entries["heading"].insert(0, data.get("heading", ""))
            
            messagebox.showinfo("Load", "Values loaded from JSON.")
        
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
