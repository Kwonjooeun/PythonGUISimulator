from dds.AIEP_AIEP_ import CMSHCI_AIEP_PA_INFO
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os

class PAInfoWindow:
    def __init__(self, parent, publisher, gui_instance):
        self.window = None
        self.parent = parent
        self.publisher = publisher
        self.gui_instance = gui_instance
        self.pa_entries = []
        
    def __call__(self):
        # 이미 창이 열려있으면 포커스만 이동
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return
            
        # 새 창 생성
        self.window = tk.Toplevel(self.parent)
        self.window.title("Prohibited Area Information")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # 메인 프레임
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상단 버튼 프레임 추가
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Load 버튼 추가
        load_btn = tk.Button(buttons_frame, text="Load from CSV", command=self.load_from_csv)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save 버튼 추가
        save_btn = tk.Button(buttons_frame, text="Save to CSV", command=self.save_to_csv)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 금지구역 개수 선택 프레임
        count_frame = tk.Frame(main_frame)
        count_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(count_frame, text="Number of Prohibited Areas:").pack(side=tk.LEFT)
        self.count_var = tk.StringVar(value="1")
        count_combo = ttk.Combobox(count_frame, textvariable=self.count_var, 
                                   values=list(range(1, 17)), width=5, state="readonly")
        count_combo.pack(side=tk.LEFT, padx=5)
        count_combo.bind("<<ComboboxSelected>>", self.update_pa_entries)
        
        # 스크롤 가능한 금지구역 정보 프레임
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
        
        send_btn = tk.Button(btn_frame, text="Send PA Info", command=self.send_pa_info)
        send_btn.pack(pady=5)
        
        # 초기 금지구역 입력 필드 생성
        self.update_pa_entries()
    
    def update_pa_entries(self, event=None):
        # 기존 입력 필드 삭제
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.pa_entries = []
        count = int(self.count_var.get())
        
        # 열 제목 표시
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        headers = ["No.", "Radius(m)", "Latitude(deg)", "Longitude(deg)", "Course(deg)", "Speed(m/s)"]
        widths = [40, 100, 100, 100, 100, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            lbl = ttk.Label(header_frame, text=header, width=width//10, anchor="center")
            lbl.grid(row=0, column=i, padx=2)
        
        # 금지구역 수만큼 입력 필드 생성
        for i in range(count):
            pa_frame = ttk.Frame(self.scrollable_frame)
            pa_frame.pack(fill=tk.X, pady=2)
            
            # 금지구역 번호
            ttk.Label(pa_frame, text=f"{i+1}", width=4, anchor="center").grid(row=0, column=0, padx=2)
            
            # 각 금지구역 파라미터 입력 필드
            entry_fields = {}
            for j, (field, width) in enumerate(zip(["dRadius", "dLatitude", "dLongitude", "dCourse", "dSpeed"], widths[1:])):
                entry = ttk.Entry(pa_frame, width=width//10)
                entry.grid(row=0, column=j+1, padx=2)
                entry_fields[field] = entry
                
                # 기본값 설정
                if field == "dRadius":
                    entry.insert(0, "1000")  # 기본 반경 1000m
                elif field == "dLatitude":
                    entry.insert(0, "35.0")  # 기본 위도
                elif field == "dLongitude":
                    entry.insert(0, "128.0")  # 기본 경도
                elif field == "dCourse":
                    entry.insert(0, "0.0")  # 기본 진로
                elif field == "dSpeed":
                    entry.insert(0, "0.0")  # 기본 속도
            
            self.pa_entries.append(entry_fields)
        
        # 창 크기 조정
        self.canvas.update_idletasks()
        visible_height = min(500, self.scrollable_frame.winfo_height() + 100)  # 최대 높이 제한
        self.window.geometry(f"800x{visible_height}")
    
    def load_from_csv(self):
        # 파일 선택 대화상자 열기
        filepath = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Load Prohibited Area Data"
        )
        
        if not filepath:  # 사용자가 취소한 경우
            return
            
        try:
            # CSV 파일 읽기
            with open(filepath, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
                
                # 데이터 유효성 검사
                if not data:
                    messagebox.showerror("Error", "No data found in the CSV file.")
                    return
                    
                # 금지구역 개수 설정
                count = len(data)
                if count > 16:
                    messagebox.showwarning("Warning", f"CSV contains {count} areas, but only 16 can be used.")
                    count = 16
                    data = data[:16]

                        
                self.count_var.set(str(count))
                self.update_pa_entries()  # 입력 필드 업데이트
                
                # 데이터 채우기
                for i, row in enumerate(data):
                    if i >= count:
                        break
                    
                    try:
                        # CSV의 열 이름이 클래스의 필드 이름과 일치해야 함
                        self.pa_entries[i]["dRadius"].delete(0, tk.END)
                        self.pa_entries[i]["dRadius"].insert(0, row.get("Radius", "1000"))
                        
                        self.pa_entries[i]["dLatitude"].delete(0, tk.END)
                        self.pa_entries[i]["dLatitude"].insert(0, row.get("Latitude", "35.0"))
                        
                        self.pa_entries[i]["dLongitude"].delete(0, tk.END)
                        self.pa_entries[i]["dLongitude"].insert(0, row.get("Longitude", "128.0"))
                        
                        self.pa_entries[i]["dCourse"].delete(0, tk.END)
                        self.pa_entries[i]["dCourse"].insert(0, row.get("Course", "0.0"))
                        
                        self.pa_entries[i]["dSpeed"].delete(0, tk.END)
                        self.pa_entries[i]["dSpeed"].insert(0, row.get("Speed", "0.0"))
                    except Exception as e:
                        messagebox.showerror("Data Error", f"Error loading data for PA #{i+1}: {e}")
                
                messagebox.showinfo("Success", f"Loaded {count} prohibited areas from {os.path.basename(filepath)}.")
                
        except Exception as e:
            messagebox.showerror("File Error", f"Error loading file: {e}")
    
    def save_to_csv(self):
        # 현재 데이터 수집
        count = int(self.count_var.get())
        data = []
      
        for i in range(count):
            try:
                pa_data = {
                    "PA_Number": i+1,
                    "Radius": self.pa_entries[i]["dRadius"].get(),
                    "Latitude": self.pa_entries[i]["dLatitude"].get(),
                    "Longitude": self.pa_entries[i]["dLongitude"].get(),
                    "Course": self.pa_entries[i]["dCourse"].get(),
                    "Speed": self.pa_entries[i]["dSpeed"].get()
                }
                data.append(pa_data)
            except Exception as e:
                messagebox.showerror("Data Error", f"Error collecting data for PA #{i+1}: {e}")
                return
        
        # 파일 저장 대화상자 열기
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Save Prohibited Area Data"
        )
        
        if not filepath:  # 사용자가 취소한 경우
            return
            
        try:
            # CSV 파일 쓰기
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = ["PA_Number", "Radius", "Latitude", "Longitude", "Course", "Speed"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
                            
                messagebox.showinfo("Success", f"Saved {count} prohibited areas to {os.path.basename(filepath)}.")
                
        except Exception as e:
            messagebox.showerror("File Error", f"Error saving file: {e}")
    
    def send_pa_info(self):
        # 기존 코드 유지
        try:
            count = int(self.count_var.get())
            
            # 메시지 생성
            msg = CMSHCI_AIEP_PA_INFO()
            # 헤더 설정이 필요하면 여기에 추가
            msg.nCountPA = count
            
            # 로컬 저장 객체 생성
            stored_pa_info = CMSHCI_AIEP_PA_INFO()
            stored_pa_info.nCountPA = count
            
            # 각 금지구역 정보 설정
            for i in range(count):
                entry_fields = self.pa_entries[i]
                
                try:
                    radius = float(entry_fields["dRadius"].get())
                    latitude = float(entry_fields["dLatitude"].get())
                    longitude = float(entry_fields["dLongitude"].get())
                    course = float(entry_fields["dCourse"].get())
                    speed = float(entry_fields["dSpeed"].get())
                    
                    # 값 검증
                    if radius <= 0:
                        raise ValueError(f"Radius for PA #{i+1} must be positive.")
                    if not (-90 <= latitude <= 90):
                        raise ValueError(f"Latitude for PA #{i+1} must be between -90 and 90.")
                    if not (-180 <= longitude <= 180):
                        raise ValueError(f"Longitude for PA #{i+1} must be between -180 and 180.")
                    if not (0 <= course < 360):
                        raise ValueError(f"Course for PA #{i+1} must be between 0 and 360.")
                    if speed < 0:
                        raise ValueError(f"Speed for PA #{i+1} cannot be negative.")
                    
                    # 메시지에 값 설정
                    msg.stPaPoint[i].dRadius = radius
                    msg.stPaPoint[i].dLatitude = latitude
                    msg.stPaPoint[i].dLongitude = longitude
                    msg.stPaPoint[i].dCourse = course
                    msg.stPaPoint[i].dSpeed = speed
                    
                    # 로컬 저장 객체에도 설정
                    stored_pa_info.stPaPoint[i].dRadius = radius
                    stored_pa_info.stPaPoint[i].dLatitude = latitude
                    stored_pa_info.stPaPoint[i].dLongitude = longitude
                    stored_pa_info.stPaPoint[i].dCourse = course
                    stored_pa_info.stPaPoint[i].dSpeed = speed
                except ValueError as e:
                    if str(e).startswith("Radius") or str(e).startswith("Latitude") or str(e).startswith("Longitude") or str(e).startswith("Course") or str(e).startswith("Speed"):
                        raise
                    else:
                        raise ValueError(f"Invalid input for PA #{i+1}: {e}")
            
            # 메시지 전송
            self.publisher.writerCMSHCI_AIEP_PA_INFO.write(msg)
            
            # GUI 인스턴스에 금지구역 정보 직접 업데이트
            self.gui_instance.pa_info_data = stored_pa_info
            
            # 플롯 창이 열려있으면 업데이트
            if hasattr(self.gui_instance, 'ep_plot_window') and self.gui_instance.ep_plot_window and self.gui_instance.ep_plot_window.winfo_exists():
                self.gui_instance.update_ep_plot()
            
            messagebox.showinfo("Success", f"{count} prohibited area(s) information sent successfully.")
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        except Exception as e:
            messagebox.showerror("Send Failed", f"Failed to send message:\n{e}")

