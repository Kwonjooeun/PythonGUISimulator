import tkinter as tk
from tkinter import ttk, messagebox
import json
from dds.AIEP_AIEP_ import TEWA_ASSIGN_CMD, ST_WA_SESSION, SGEODETIC_POSITION, CMSHCI_AIEP_WPN_CTRL_CMD

class WpnCtrlCmdWindow:
    def __init__(self, parent, publisher):
        self.window = None
        self.parent = parent
        self.publisher = publisher
        
    def __call__(self):
        # 이미 창이 열려있으면 포커스만 이동
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return
            
        # 새 창 생성
        self.window = tk.Toplevel(self.parent)
        self.window.title("Weapon Control Command")
        self.window.resizable(False, False)
        
        # 프레임 생성
        main_frame = tk.Frame(self.window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH)
        
        # 발사관 번호 입력
        tube_frame = tk.Frame(main_frame)
        tube_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(tube_frame, text="Tube Number (1-6):").pack(side=tk.LEFT)
        self.tube_num_var = tk.StringVar(value="1")
        tube_combo = ttk.Combobox(tube_frame, textvariable=self.tube_num_var, values=list(range(1, 7)), width=5, state="readonly")
        tube_combo.pack(side=tk.LEFT, padx=5)

          
        # 무장 종류 입력
        wpn_kind_frame = tk.Frame(main_frame)
        wpn_kind_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(wpn_kind_frame, text="Weapon Kind (0-5):").pack(side=tk.LEFT)
        self.wpn_kind_var = tk.StringVar(value="0")
        wpn_kind_combo = ttk.Combobox(wpn_kind_frame, textvariable=self.wpn_kind_var, values=list(range(6)), width=5, state="readonly")
        wpn_kind_combo.pack(side=tk.LEFT, padx=5)
        
        # 무장 통제 명령 선택
        cmd_frame = tk.Frame(main_frame)
        cmd_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cmd_frame, text="Command:").pack(side=tk.LEFT)
        
        # 명령 종류 정의 (예시, 실제 enum 값에 맞게 조정 필요)
        self.cmd_options = {
            "Turn On": 1,
            "Turn Off": 2,
            "Fire": 4,
            "Cancel": 5
        }
        
        self.cmd_var = tk.StringVar(value="Turn On")
        cmd_combo = ttk.Combobox(cmd_frame, textvariable=self.cmd_var, values=list(self.cmd_options.keys()), width=10, state="readonly")
        cmd_combo.pack(side=tk.LEFT, padx=5)
        
        # 전송 버튼
        send_frame = tk.Frame(main_frame)
        send_frame.pack(fill=tk.X, pady=10)
        
        send_btn = tk.Button(send_frame, text="Send Command", command=self.send_wpn_ctrl_cmd)
        send_btn.pack(pady=5)
        
    def send_wpn_ctrl_cmd(self):
        try:
            tube_num = int(self.tube_num_var.get())
            wpn_kind = int(self.wpn_kind_var.get())
            cmd_value = self.cmd_options[self.cmd_var.get()]
            
            # 메시지 생성
            msg = CMSHCI_AIEP_WPN_CTRL_CMD()
            # 헤더 설정이 필요하면 여기에 추가
            msg.eTubeNum = tube_num
            msg.eWpnKind = wpn_kind
            msg.eWpnCtrlCmd = cmd_value
            
            # 메시지 전송
            self.publisher.writerCMSHCI_AIEP_WPN_CTRL_CMD.write(msg)
            
            messagebox.showinfo("Command Sent", 
                               f"Weapon Control Command sent:\n"
                               f"Tube: {tube_num}\n"
                               f"Weapon Kind: {wpn_kind}\n"
                               f"Command: {self.cmd_var.get()}")
                               
        except Exception as e:
            messagebox.showerror("Send Failed", f"Failed to send command:\n{e}")      
