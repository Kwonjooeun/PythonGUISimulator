# tewa_assign_cmd_window.py
import tkinter as tk
from tkinter import messagebox
import json
from dds.AIEP_AIEP_ import TEWA_ASSIGN_CMD, ST_WA_SESSION, SGEODETIC_POSITION

# 변환 함수: 입력된 문자열을 JSON 저장/불러움에 사용할 수 있도록 처리
def save_values_to_json(data, filename="tewa_assign_cmd.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        messagebox.showinfo("Save", f"Values saved to {filename}")
    except Exception as e:
        messagebox.showerror("Save Error", str(e))

def load_values_from_json(filename="tewa_assign_cmd.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        messagebox.showerror("Load Error", str(e))
        return None

  # TEWA_ASSIGN_CMD 입력창 클래스
class TEWAAssignCmdWindow(tk.Toplevel):
    def __init__(self, parent, publisher_callback):
        super().__init__(parent)
        self.title("TEWA_ASSIGN_CMD Message")
        self.publisher_callback = publisher_callback  # 메시지 전송 함수

        # --- 상단: TEWA_ASSIGN_CMD 기본 필드 ---
        tk.Label(self, text="eSetCmd (int):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.eSetCmd_entry = tk.Entry(self)
        self.eSetCmd_entry.grid(row=0, column=1, padx=5, pady=5)

        # --- ST_WA_SESSION 입력 프레임 ---
        session_frame = tk.LabelFrame(self, text="Weapon Assignment Session (ST_WA_SESSION)")
        session_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        session_labels = [
            ("enConsoleNum (0-9):", "enConsoleNum"),
            ("enTubeNum (0-6):", "enTubeNum"),
            ("enWeaponType (0-5):", "enWeaponType"),
            ("enAllocConsoleNum (0-9):", "enAllocConsoleNum"),
            ("unTrackNumber (0-128):", "unTrackNumber"),
            ("usAllocDroppingPlanListNum:", "usAllocDroppingPlanListNum"),
            ("usAllocLayNum:", "usAllocLayNum"),
            ("enAllocTube (0-3):", "enAllocTube"),
            ("enAllocLay (0-3):", "enAllocLay"),
            ("enAllocTrack (0-3):", "enAllocTrack")
        ]
        self.session_entries = {}
        for idx, (label_text, field_name) in enumerate(session_labels):
            tk.Label(session_frame, text=label_text).grid(row=idx, column=0, sticky="w", padx=5, pady=2)
            entry = tk.Entry(session_frame)
            entry.grid(row=idx, column=1, padx=5, pady=2)
            self.session_entries[field_name] = entry
          
        # --- SGEODETIC_POSITION (stTargetPos) 입력 프레임 ---
        pos_frame = tk.LabelFrame(session_frame, text="Target Position (stTargetPos)")
        pos_frame.grid(row=len(session_labels), column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        tk.Label(pos_frame, text="dLatitude:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.dLatitude_entry = tk.Entry(pos_frame)
        self.dLatitude_entry.grid(row=0, column=1, padx=5, pady=2)
        tk.Label(pos_frame, text="dLongitude:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.dLongitude_entry = tk.Entry(pos_frame)
        self.dLongitude_entry.grid(row=1, column=1, padx=5, pady=2)
        tk.Label(pos_frame, text="fAltitude:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.fAltitude_entry = tk.Entry(pos_frame)
        self.fAltitude_entry.grid(row=2, column=1, padx=5, pady=2)

        # enAllocTarget 입력
        tk.Label(session_frame, text="enAllocTarget (0-3):").grid(row=len(session_labels)+1, column=0, sticky="w", padx=5, pady=2)
        self.enAllocTarget_entry = tk.Entry(session_frame)
        self.enAllocTarget_entry.grid(row=len(session_labels)+1, column=1, padx=5, pady=2)

        # --- 하단: 전송, 저장, 불러오기 버튼 ---
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=10)
        
        send_btn = tk.Button(btn_frame, text="TEWA_ASSIGN_CMD", command=self.send_command)
        send_btn.pack(side=tk.LEFT, padx=5)
        save_btn = tk.Button(btn_frame, text="Save to JSON", command=self.save_to_json)
        save_btn.pack(side=tk.LEFT, padx=5)
        load_btn = tk.Button(btn_frame, text="Load from JSON", command=self.load_from_json)
        load_btn.pack(side=tk.LEFT, padx=5)
    
    def send_command(self):
        try:
                      # 각 필드의 값 읽기 및 변환
            eSetCmd = int(self.eSetCmd_entry.get().strip())
            enConsoleNum = int(self.session_entries["enConsoleNum"].get().strip())
            enTubeNum = int(self.session_entries["enTubeNum"].get().strip())
            enWeaponType = int(self.session_entries["enWeaponType"].get().strip())
            enAllocConsoleNum = int(self.session_entries["enAllocConsoleNum"].get().strip())
            unTrackNumber = int(self.session_entries["unTrackNumber"].get().strip())
            usAllocDroppingPlanListNum = int(self.session_entries["usAllocDroppingPlanListNum"].get().strip())
            usAllocLayNum = int(self.session_entries["usAllocLayNum"].get().strip())
            enAllocTube = int(self.session_entries["enAllocTube"].get().strip())
            enAllocLay = int(self.session_entries["enAllocLay"].get().strip())
            enAllocTrack = int(self.session_entries["enAllocTrack"].get().strip())
            dLatitude = float(self.dLatitude_entry.get().strip())
            dLongitude = float(self.dLongitude_entry.get().strip())
            fAltitude = float(self.fAltitude_entry.get().strip())
            enAllocTarget = int(self.enAllocTarget_entry.get().strip())
            
            # DDS 메시지 생성
            cmd_msg = TEWA_ASSIGN_CMD()
            cmd_msg.eSetCmd = eSetCmd
            session = cmd_msg.stWpnAssign
            session.enConsoleNum = enConsoleNum
            session.enTubeNum = enTubeNum
            session.enWeaponType = enWeaponType
            session.enAllocConsoleNum = enAllocConsoleNum
            session.unTrackNumber = unTrackNumber
            session.usAllocDroppingPlanListNum = usAllocDroppingPlanListNum
            session.usAllocLayNum = usAllocLayNum
            session.enAllocTube = enAllocTube
            session.enAllocLay = enAllocLay
                      session.enAllocTrack = enAllocTrack
            session.stTargetPos.dLatitude = dLatitude
            session.stTargetPos.dLongitude = dLongitude
            session.stTargetPos.fAltitude = fAltitude
            session.enAllocTarget = enAllocTarget
            
            # 전송: publisher_callback 함수 호출
            self.publisher_callback.publish_TEWA_ASSIGN_CMD(cmd_msg)
            messagebox.showinfo("Info", "TEWA_ASSIGN_CMD message sent.")
            #self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send TEWA_ASSIGN_CMD: {e}")
    
    def save_to_json(self):
        try:
            # 각 입력 필드의 값을 읽어 딕셔너리 형태로 저장 (여기서는 dict를 임시 저장용으로 사용합니다)
            data = {
                "eSetCmd": self.eSetCmd_entry.get().strip(),
                "ST_WA_SESSION": { key: self.session_entries[key].get().strip() for key in self.session_entries },
                "stTargetPos": {
                    "dLatitude": self.dLatitude_entry.get().strip(),
                    "dLongitude": self.dLongitude_entry.get().strip(),
                    "fAltitude": self.fAltitude_entry.get().strip()
                },
                "enAllocTarget": self.enAllocTarget_entry.get().strip()
            }
            save_values_to_json(data)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
    
    def load_from_json(self):
        try:
                     data = load_values_from_json()
            if data is None:
                return
            self.eSetCmd_entry.delete(0, tk.END)
            self.eSetCmd_entry.insert(0, data.get("eSetCmd", ""))
            session_data = data.get("ST_WA_SESSION", {})
            for key, entry in self.session_entries.items():
                entry.delete(0, tk.END)
                entry.insert(0, session_data.get(key, ""))
            pos_data = data.get("stTargetPos", {})
            self.dLatitude_entry.delete(0, tk.END)
            self.dLatitude_entry.insert(0, pos_data.get("dLatitude", ""))
            self.dLongitude_entry.delete(0, tk.END)
            self.dLongitude_entry.insert(0, pos_data.get("dLongitude", ""))
            self.fAltitude_entry.delete(0, tk.END)
            self.fAltitude_entry.insert(0, pos_data.get("fAltitude", ""))
            self.enAllocTarget_entry.delete(0, tk.END)
            self.enAllocTarget_entry.insert(0, data.get("enAllocTarget", ""))
            messagebox.showinfo("Load", "Values loaded from JSON.")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
