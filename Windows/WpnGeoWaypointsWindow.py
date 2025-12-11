import tkinter as tk
from tkinter import ttk, messagebox
import json
from dds.AIEP_AIEP_ import CMSHCI_AIEP_WPN_GEO_WAYPOINTS

class WpnGeoWaypointsWindow:
    def __init__(self, parent, publisher):
        self.window = None
        self.parent = parent
        self.publisher = publisher
        self.waypoint_entries = []  # 경로점 입력 필드들을 저장할 리스트
        
    def __call__(self):
        # 이미 창이 열려있으면 포커스만 이동
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return
            
        # 새 창 생성
        self.window = tk.Toplevel(self.parent)
        self.window.title("Modify Weapon Waypoints")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # 메인 프레임
        main_frame = tk.Frame(self.window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 무장 종류 및 발사관 번호 프레임
        weapon_frame = tk.Frame(main_frame)
        weapon_frame.pack(fill=tk.X, pady=5)
        
        # 무장 종류 선택
        tk.Label(weapon_frame, text="Weapon Type:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.weapon_type_var = tk.StringVar(value="0")
        weapon_type_combo = ttk.Combobox(weapon_frame, textvariable=self.weapon_type_var, 
                                         values=list(range(6)), width=5, state="readonly")
        weapon_type_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)


        # 발사관 번호 선택
        tk.Label(weapon_frame, text="Tube Number:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.tube_num_var = tk.StringVar(value="1")
        tube_num_combo = ttk.Combobox(weapon_frame, textvariable=self.tube_num_var, 
                                      values=list(range(1, 7)), width=5, state="readonly")
        tube_num_combo.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        # 경로점 자동 생성 여부
        tk.Label(weapon_frame, text="Auto Generate:").grid(row=0, column=4, sticky="e", padx=5, pady=5)
        self.auto_generate_var = tk.BooleanVar(value=False)
        auto_generate_check = ttk.Checkbutton(weapon_frame, variable=self.auto_generate_var)
        auto_generate_check.grid(row=0, column=5, sticky="w", padx=5, pady=5)
        
        # 경로점 개수 프레임
        count_frame = tk.Frame(main_frame)
        count_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(count_frame, text="Number of Waypoints:").pack(side=tk.LEFT, padx=5)
        self.count_var = tk.StringVar(value="3")  # 기본값 3개
        count_combo = ttk.Combobox(count_frame, textvariable=self.count_var, 
                                  values=list(range(1, 16)), width=5, state="readonly")
        count_combo.pack(side=tk.LEFT, padx=5)
        count_combo.bind("<<ComboboxSelected>>", self.update_waypoint_entries)
        
        # 스크롤 가능한 경로점 입력 프레임
        self.canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
      
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 전송 버튼 프레임
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        send_btn = tk.Button(btn_frame, text="Send Waypoints", command=self.send_waypoints)
        send_btn.pack(pady=5)
        
        # 초기 경로점 입력 필드 생성
        self.update_waypoint_entries()
        
    def update_waypoint_entries(self, event=None):
        # 기존 입력 필드 삭제
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.waypoint_entries = []
        count = int(self.count_var.get())
        
        # 열 제목 표시
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        headers = ["No.", "Latitude(deg)", "Longitude(deg)", "Depth(m)", "Speed(m/s)", "Valid"]
        widths = [40, 100, 100, 80, 80, 60]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            lbl = ttk.Label(header_frame, text=header, width=width//10, anchor="center")
            lbl.grid(row=0, column=i, padx=2)
          
        # 경로점 수만큼 입력 필드 생성
        for i in range(count):
            wp_frame = ttk.Frame(self.scrollable_frame)
            wp_frame.pack(fill=tk.X, pady=2)
            
            # 경로점 번호
            ttk.Label(wp_frame, text=f"{i+1}", width=4, anchor="center").grid(row=0, column=0, padx=2)
            
            # 각 경로점 파라미터 입력 필드
            entry_fields = {}
            
            # 위도, 경도, 심도, 속력 입력 필드
            for j, (field, width) in enumerate(zip(["dLatitude", "dLongitude", "fDepth", "fSpeed"], widths[1:5])):
                entry = ttk.Entry(wp_frame, width=width//10)
                entry.grid(row=0, column=j+1, padx=2)
                entry_fields[field] = entry
                
                # 기본값 설정
                if field == "dLatitude":
                    entry.insert(0, "35.0")  # 기본 위도
                elif field == "dLongitude":
                    entry.insert(0, f"{128.0 + i*0.1:.1f}")  # 기본 경도 (각 포인트마다 약간씩 다르게)
                elif field == "fDepth":
                    entry.insert(0, "0.0")  # 기본 심도
                elif field == "fSpeed":
                    entry.insert(0, "10.0")  # 기본 속력
            
            # Valid 체크박스
            valid_var = tk.BooleanVar(value=True)
            valid_check = ttk.Checkbutton(wp_frame, variable=valid_var)
            valid_check.grid(row=0, column=5, padx=2)
            entry_fields["bValid"] = valid_var
            
            self.waypoint_entries.append(entry_fields)
        
        # 창 크기 조정
        self.canvas.update_idletasks()
        visible_height = min(500, self.scrollable_frame.winfo_height() + 150)  # 최대 높이 제한
        self.window.geometry(f"800x{visible_height}")
        
    def send_waypoints(self):
        try:
            # 무장 종류 및 발사관 번호 가져오기
            wpn_kind = int(self.weapon_type_var.get())
            tube_num = int(self.tube_num_var.get())
            count = int(self.count_var.get())
            auto_generate = self.auto_generate_var.get()
            
            # 메시지 생성
            msg = CMSHCI_AIEP_WPN_GEO_WAYPOINTS()
            # 헤더 설정이 필요하면 여기에 추가
            msg.eWpnKind = wpn_kind
            msg.eTubeNum = tube_num
            msg.bValid_GenerateWaypoints = 1 if auto_generate else 0
            
            # 경로점 정보 설정
            msg.stGeoWaypoints.unCntWaypoints = count
            
            # 각 경로점 정보 설정
            for i in range(count):
                entry_fields = self.waypoint_entries[i]
                
                try:
                    latitude = float(entry_fields["dLatitude"].get())
                    longitude = float(entry_fields["dLongitude"].get())
                    depth = float(entry_fields["fDepth"].get())
                    speed = float(entry_fields["fSpeed"].get())
                    valid = entry_fields["bValid"].get()
                    
                    # 값 검증
                    if not (-90 <= latitude <= 90):
                        raise ValueError(f"Latitude for waypoint #{i+1} must be between -90 and 90.")
                    if not (-180 <= longitude <= 180):
                        raise ValueError(f"Longitude for waypoint #{i+1} must be between -180 and 180.")
                    if depth < 0:
                        raise ValueError(f"Depth for waypoint #{i+1} cannot be negative.")
                    if speed < 0:
                      
                        raise ValueError(f"Speed for waypoint #{i+1} cannot be negative.")
                    
                    # 메시지에 값 설정
                    msg.stGeoWaypoints.stGeoPos[i].dLatitude = latitude
                    msg.stGeoWaypoints.stGeoPos[i].dLongitude = longitude
                    msg.stGeoWaypoints.stGeoPos[i].fDepth = depth
                    msg.stGeoWaypoints.stGeoPos[i].fSpeed = speed
                    msg.stGeoWaypoints.stGeoPos[i].bValid = 1 if valid else 0
                    
                except ValueError as e:
                    if str(e).startswith("Latitude") or str(e).startswith("Longitude") or str(e).startswith("Depth") or str(e).startswith("Speed"):
                        raise  # Pass custom error message directly
                    else:
                        raise ValueError(f"Invalid input for waypoint #{i+1}: {e}")
            
            # 메시지 전송
            self.publisher.writerCMSHCI_AIEP_WPN_GEO_WAYPOINTS.write(msg)
            
            messagebox.showinfo("Success", f"Waypoints information for weapon type {wpn_kind}, tube {tube_num} sent successfully.")


        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Send Failed", f"Failed to send message:\n{e}")
