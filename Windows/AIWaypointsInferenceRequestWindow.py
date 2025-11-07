import tkinter as tk
from tkinter import ttk, messagebox
import json
from dds.AIEP_AIEP_ import CMSHCI_AIEP_AI_WAYPOINTS_INFERENCE_REQ

class AIWaypointsInferenceRequestWindow:
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
        self.window.title("AI Waypoints Inference Request")
        self.window.resizable(False, False)
        
        # 메인 프레임
        main_frame = tk.Frame(self.window, padx=20, pady=20)
        main_frame.pack()
        
        # 무장 종류 및 발사관 번호 입력 프레임
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        # 무장 종류 입력
        tk.Label(input_frame, text="Weapon Type:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.weapon_type_var = tk.StringVar(value="0")
        weapon_type_combo = ttk.Combobox(input_frame, textvariable=self.weapon_type_var, 
                                               values=list(range(6)), width=5, state="readonly")
        weapon_type_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # 발사관 번호 입력
        tk.Label(input_frame, text="Tube Number:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.tube_num_var = tk.StringVar(value="1")
        tube_num_combo = ttk.Combobox(input_frame, textvariable=self.tube_num_var, 
                                      values=list(range(1, 7)), width=5, state="readonly")
        tube_num_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # AI 경로점 생성 여부
        generate_frame = tk.Frame(main_frame)
        generate_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(generate_frame, text="Generate AI Waypoints:").pack(side=tk.LEFT, padx=(0, 10))
        self.generate_var = tk.BooleanVar(value=True)
        generate_check = ttk.Checkbutton(generate_frame, variable=self.generate_var)
        generate_check.pack(side=tk.LEFT)
        
        # 전송 버튼
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        send_btn = tk.Button(btn_frame, text="Send Request", command=self.send_request)
        send_btn.pack(pady=5)
        
    def send_request(self):
        try:
            wpn_kind = int(self.weapon_type_var.get())
            tube_num = int(self.tube_num_var.get())
            generate_ai = self.generate_var.get()
            
            # 메시지 생성
            msg = CMSHCI_AIEP_AI_WAYPOINTS_INFERENCE_REQ()
            # 헤더 설정이 필요하면 여기에 추가
            
            # 메시지 필드 설정
            msg.eWpnKind = wpn_kind
            msg.eTubeNum = tube_num
            msg.bGenerateAIWaypoints = 1 if generate_ai else 0
            
            # 메시지 전송
            self.publisher.writerCMSHCI_AIEP_AI_WAYPOINTS_INFERENCE_REQ.write(msg)
            
            messagebox.showinfo("Success", f"AI waypoints inference request sent for weapon type {wpn_kind}, tube {tube_num}.")
            
        except Exception as e:
            messagebox.showerror("Send Failed", f"Failed to send request:\n{e}")
