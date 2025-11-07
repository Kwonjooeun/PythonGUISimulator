# DroppingPlanWindows.py
import tkinter as tk
from tkinter import ttk, messagebox
import copy
from dds.AIEP_AIEP_ import (
    AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST,
    CMSHCI_AIEP_M_MINE_EDITED_PLAN_LIST,
    ST_M_MINE_PLAN_LIST,
    ST_M_MINE_PLAN_INFO,
    ST_WEAPON_WAYPOINT,
    ST_M_MINE_PLAN_OWNSHIP_WAYPOINT
)


# =============================================================================
# Helper Functions
# =============================================================================

def extract_string_from_char_array(char_array):
    """DDS char 배열을 Python 문자열로 변환"""
    try:
        result = ""
        for c in char_array:
            if c == 0 or c == '\0':
                break
            result += chr(c) if isinstance(c, int) else c
        return result
    except:
        return ""


def set_string_to_char_array(char_array, string_value, max_length=50):
    """Python 문자열을 DDS char 배열로 설정"""
    try:
        bytes_data = string_value.encode('utf-8')[:max_length-1]
        for i in range(max_length):
            if i < len(bytes_data):
                char_array[i] = bytes_data[i]
            else:
                char_array[i] = 0
    except Exception as e:
        print(f"Error setting char array: {e}")


def is_plan_list_empty(plan_list):
    """Check if plan list is empty"""
    # 이름이 있으면 비어있지 않음
    name = extract_string_from_char_array(plan_list.chDescription)
    if name.strip():
        return False
    
    # 이름도 없고 sListID도 0이면 비어있음
    if plan_list.sListID == 0:
        return True
    
    # sListID가 있지만 이름이 없는 경우, 계획이 있는지 확인
    has_valid_plan = any(
        plan_list.stPlan[i].sListID != 0 
        for i in range(15)
    )
    
    return not has_valid_plan


def is_plan_info_empty(plan_info):
    """개별 부설계획이 비어있는지 확인"""
    return plan_info.sListID == 0 and plan_info.usDroppingPlanNumber == 0


# =============================================================================
# Level 1: Dropping Plan List Window
# =============================================================================

class DroppingPlanListWindow(tk.Toplevel):
    """부설계획 목록 조회 및 관리 (최대 15개)"""
    
    def __init__(self, parent, publisher, plan_data):
        super().__init__(parent)
        self.title("Dropping Plan Lists")
        self.geometry("900x600")
        
        self.publisher = publisher
        
        # 원본 데이터 복사 (수정 중 원본 보존)
        if plan_data is None:
            messagebox.showerror("Error", "No plan data received!")
            self.destroy()
            return
            
        self.plan_data = self._deep_copy_plan_data(plan_data)
        
        self._setup_ui()
        self._populate_tree()
        
    def _deep_copy_plan_data(self, source):
        """AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST 깊은 복사"""
        copied = AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST()
        copied.usPlanListCnt = source.usPlanListCnt
        
        for i in range(15):
            src_list = source.stMinePlanList[i]
            dst_list = copied.stMinePlanList[i]
            
            # chDescription 복사
            for j in range(50):
                dst_list.chDescription[j] = src_list.chDescription[j]
            
            dst_list.sListID = src_list.sListID
            dst_list.usOwnshipWaypointCnt = src_list.usOwnshipWaypointCnt
            
            # stPlan 복사 (15개)
            for j in range(15):
                self._copy_plan_info(src_list.stPlan[j], dst_list.stPlan[j])
            
            # stOwnshipWaypoint 복사 (40개)
            for j in range(40):
                self._copy_ownship_waypoint(
                    src_list.stOwnshipWaypoint[j],
                    dst_list.stOwnshipWaypoint[j]
                )
        
        return copied
    
    def _copy_plan_info(self, src, dst):
        """ST_M_MINE_PLAN_INFO 복사"""
        dst.sListID = src.sListID
        dst.usDroppingPlanNumber = src.usDroppingPlanNumber
        dst.ePlanState = src.ePlanState
        dst.usWeaponID = src.usWeaponID
        
        # cAdditionalText 복사
        for i in range(50):
            dst.cAdditionalText[i] = src.cAdditionalText[i]
        
        # 위치 정보 복사
        self._copy_waypoint(src.stDropPos, dst.stDropPos)
        self._copy_waypoint(src.stLaunchPos, dst.stLaunchPos)
        
        dst.usWaypointCnt = src.usWaypointCnt
        for i in range(8):
            self._copy_waypoint(src.stWaypoint[i], dst.stWaypoint[i])
    
    def _copy_waypoint(self, src, dst):
        """ST_WEAPON_WAYPOINT 복사"""
        dst.dLatitude = src.dLatitude
        dst.dLongitude = src.dLongitude
        dst.fDepth = src.fDepth
        dst.fSpeed = src.fSpeed
        dst.bValid = src.bValid
    
    def _copy_ownship_waypoint(self, src, dst):
        """ST_M_MINE_PLAN_OWNSHIP_WAYPOINT 복사"""
        dst.dLatitude = src.dLatitude
        dst.dLongitude = src.dLongitude
        dst.fDepth = src.fDepth
        dst.fSpeed = src.fSpeed
        dst.fHeading = src.fHeading
        dst.bLaunchPoint = src.bLaunchPoint
        dst.usListID = src.usListID
        
    def _setup_ui(self):
        """UI 구성"""
        # 상단 프레임: 정보 표시
        info_frame = tk.Frame(self)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(info_frame, text=f"Total Plan Lists: {self.plan_data.usPlanListCnt}",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # 중앙 프레임: Treeview
        tree_frame = tk.Frame(self)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview 생성
        columns = ("Index", "Name", "ID", "Plans", "OwnWP", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 설정
        self.tree.heading("Index", text="Index")
        self.tree.heading("Name", text="List Name")
        self.tree.heading("ID", text="List ID")
        self.tree.heading("Plans", text="# Plans")
        self.tree.heading("OwnWP", text="# Own WP")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Index", width=50, anchor="center")
        self.tree.column("Name", width=250, anchor="w")
        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Plans", width=80, anchor="center")
        self.tree.column("OwnWP", width=80, anchor="center")
        self.tree.column("Status", width=100, anchor="center")
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭 이벤트
        self.tree.bind("<Double-1>", lambda e: self._edit_selected_list())
        
        # 하단 프레임: 버튼들
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="Add New List", command=self._add_new_list,
                  width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Selected", command=self._edit_selected_list,
                  width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=self._delete_selected_list,
                  width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save & Send", command=self._save_and_send,
                  width=15, bg="lightgreen").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh View", command=self._populate_tree,
                  width=15).pack(side=tk.LEFT, padx=5)
        
    def _populate_tree(self):
        """Treeview에 데이터 채우기"""
        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 15개 슬롯 표시
        for i in range(15):
            plan_list = self.plan_data.stMinePlanList[i]
            
            if is_plan_list_empty(plan_list):
                # 비어있는 슬롯
                self.tree.insert("", "end", iid=str(i), values=(
                    i+1,
                    "<Empty>",
                    "N/A",
                    "0",
                    "0",
                    "Empty"
                ), tags=("empty",))
            else:
                # 사용 중인 슬롯
                name = extract_string_from_char_array(plan_list.chDescription)
                list_id = plan_list.sListID
                plan_count = self._count_valid_plans(plan_list)
                own_wp_cnt = plan_list.usOwnshipWaypointCnt
                
                self.tree.insert("", "end", iid=str(i), values=(
                    i+1,
                    name if name else "<Unnamed>",
                    list_id,
                    plan_count,
                    own_wp_cnt,
                    "Active"
                ))
        
        # 스타일 설정
        self.tree.tag_configure("empty", foreground="gray")
    
    def _count_valid_plans(self, plan_list):
        """유효한 계획 개수 세기"""
        count = 0
        for i in range(15):
            if not is_plan_info_empty(plan_list.stPlan[i]):
                count += 1
        return count
        
    def _add_new_list(self):
      """Add new plan list"""
      selection = self.tree.selection()
      
      if not selection:
          # 선택 없으면 빈 슬롯 찾기
          insert_index = self._find_first_empty_slot()
          if insert_index == -1:
              messagebox.showwarning("Warning", "All 15 slots are full!")
              return
      else:
          # 선택한 항목 앞에 삽입
          insert_index = int(self.tree.item(selection[0])["values"][0]) - 1
      
      # 이름 입력 대화상자
      name_dialog = tk.Toplevel(self)
      name_dialog.title("New Plan List Name")
      name_dialog.geometry("350x120")
      name_dialog.transient(self)  # 부모 창 위에 표시
      name_dialog.grab_set()  # 모달 다이얼로그
      
      tk.Label(name_dialog, text="Enter list name:").pack(pady=10)
      name_entry = tk.Entry(name_dialog, width=30)
      name_entry.pack(pady=5)
      name_entry.focus()
      
      # 기본 이름 제안
      default_name = f"Plan List {insert_index + 1}"
      name_entry.insert(0, default_name)
      name_entry.select_range(0, tk.END)  # 텍스트 전체 선택
      
      result = {"confirmed": False}
      
      def confirm():
          name = name_entry.get().strip()
          if not name:
              messagebox.showwarning("Warning", "Please enter a name!", parent=name_dialog)
              return
          
          result["confirmed"] = True
          result["name"] = name
          name_dialog.destroy()
      
      def cancel():
          name_dialog.destroy()
      
      # Enter 키로 확인
      name_entry.bind("<Return>", lambda e: confirm())
      
      btn_frame = tk.Frame(name_dialog)
      btn_frame.pack(pady=10)
      tk.Button(btn_frame, text="OK", command=confirm, width=10).pack(side=tk.LEFT, padx=5)
      tk.Button(btn_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)
      
      # 다이얼로그가 닫힐 때까지 대기
      self.wait_window(name_dialog)
      
      if result.get("confirmed"):
          # insert_index 위치에 삽입
          self._insert_list_at_index(insert_index, result["name"])
          self._populate_tree()
          
          # 추가된 항목 선택
          self.tree.selection_set(str(insert_index))
          self.tree.see(str(insert_index))
          
          messagebox.showinfo("Success", 
                             f"List '{result['name']}' added at position {insert_index+1}",
                             parent=self)
    
    def _find_first_empty_slot(self):
        """첫 번째 빈 슬롯 찾기"""
        for i in range(15):
            if is_plan_list_empty(self.plan_data.stMinePlanList[i]):
                return i
        return -1
    
    def _insert_list_at_index(self, index, name):
        """Insert list at specific position (shift others back)"""
        # 뒤에서부터 한 칸씩 뒤로 이동
        for i in range(14, index, -1):
            self._copy_entire_list(
                self.plan_data.stMinePlanList[i-1],
                self.plan_data.stMinePlanList[i]
            )
        
        # index 위치에 새 목록 생성
        new_list = self.plan_data.stMinePlanList[index]
        self._clear_plan_list(new_list)
        set_string_to_char_array(new_list.chDescription, name, 50)
        
        # sListID 재정렬 (이 함수가 자동으로 설정함)
        self._reorder_list_ids()
    
    def _copy_entire_list(self, src, dst):
        """ST_M_MINE_PLAN_LIST 전체 복사"""
        for i in range(50):
            dst.chDescription[i] = src.chDescription[i]
        
        dst.sListID = src.sListID
        dst.usOwnshipWaypointCnt = src.usOwnshipWaypointCnt
        
        for i in range(15):
            self._copy_plan_info(src.stPlan[i], dst.stPlan[i])
        
        for i in range(40):
            self._copy_ownship_waypoint(
                src.stOwnshipWaypoint[i],
                dst.stOwnshipWaypoint[i]
            )
    
    def _clear_plan_list(self, plan_list):
        """ST_M_MINE_PLAN_LIST 초기화"""
        for i in range(50):
            plan_list.chDescription[i] = 0
        
        plan_list.sListID = 0
        plan_list.usOwnshipWaypointCnt = 0
        
        for i in range(15):
            self._clear_plan_info(plan_list.stPlan[i])
        
        for i in range(40):
            self._clear_ownship_waypoint(plan_list.stOwnshipWaypoint[i])
    
    def _clear_plan_info(self, plan_info):
        """ST_M_MINE_PLAN_INFO 초기화"""
        plan_info.sListID = 0
        plan_info.usDroppingPlanNumber = 0
        plan_info.ePlanState = 0
        plan_info.usWeaponID = 0
        
        for i in range(50):
            plan_info.cAdditionalText[i] = 0
        
        plan_info.stDropPos.dLatitude = 0.0
        plan_info.stDropPos.dLongitude = 0.0
        plan_info.stDropPos.fDepth = 0.0
        plan_info.stDropPos.fSpeed = 0.0
        plan_info.stDropPos.bValid = 0
        
        plan_info.stLaunchPos.dLatitude = 0.0
        plan_info.stLaunchPos.dLongitude = 0.0
        plan_info.stLaunchPos.fDepth = 0.0
        plan_info.stLaunchPos.fSpeed = 0.0
        plan_info.stLaunchPos.bValid = 0
        
        plan_info.usWaypointCnt = 0
        for i in range(8):
            plan_info.stWaypoint[i].dLatitude = 0.0
            plan_info.stWaypoint[i].dLongitude = 0.0
            plan_info.stWaypoint[i].fDepth = 0.0
            plan_info.stWaypoint[i].fSpeed = 0.0
            plan_info.stWaypoint[i].bValid = 0
    
    def _clear_ownship_waypoint(self, wp):
        """ST_M_MINE_PLAN_OWNSHIP_WAYPOINT 초기화"""
        wp.dLatitude = 0.0
        wp.dLongitude = 0.0
        wp.fDepth = 0.0
        wp.fSpeed = 0.0
        wp.fHeading = 0.0
        wp.bLaunchPoint = 0
        wp.usListID = 0
    
    def _edit_selected_list(self):
        """선택된 목록 편집"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a plan list!")
            return
        
        list_index = int(self.tree.item(selection[0])["values"][0]) - 1
        
        # 비어있는 슬롯이면 편집 불가
        if is_plan_list_empty(self.plan_data.stMinePlanList[list_index]):
            messagebox.showinfo("Info", "Cannot edit empty slot. Add a new list first.")
            return
        
        # PlanListEditorWindow 오픈
        editor = PlanListEditorWindow(
            self,
            self.plan_data.stMinePlanList[list_index],
            list_index
        )
        
        # 에디터가 닫힐 때까지 대기
        self.wait_window(editor)
        
        # 리프레시
        self._populate_tree()
    
    def _delete_selected_list(self):
        """선택된 목록 삭제"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a plan list!")
            return
        
        list_index = int(self.tree.item(selection[0])["values"][0]) - 1
        
        # 확인 대화상자
        if not messagebox.askyesno("Confirm", 
                                    f"Delete plan list at position {list_index+1}?"):
            return
        
        # 앞으로 당기기
        for i in range(list_index, 14):
            self._copy_entire_list(
                self.plan_data.stMinePlanList[i+1],
                self.plan_data.stMinePlanList[i]
            )
        
        # 마지막 슬롯 초기화
        self._clear_plan_list(self.plan_data.stMinePlanList[14])
        
        # sListID 재정렬
        self._reorder_list_ids()
        
        # 리프레시
        self._populate_tree()
        messagebox.showinfo("Success", "Plan list deleted!")
    
    def _reorder_list_ids(self):
        """sListID 재정렬 (비어있지 않은 목록만 1부터 순차적으로)"""
        current_id = 1
        valid_count = 0
        
        for i in range(15):
            plan_list = self.plan_data.stMinePlanList[i]
            
            if is_plan_list_empty(plan_list):
                plan_list.sListID = 0
            else:
                plan_list.sListID = current_id
                current_id += 1
                valid_count += 1
        
        # usPlanListCnt 업데이트
        self.plan_data.usPlanListCnt = valid_count
    
    def _save_and_send(self):
        """저장 및 DDS 메시지 송신"""
        # sListID 재정렬
        self._reorder_list_ids()
        
        # CMSHCI_AIEP_M_MINE_EDITED_PLAN_LIST 생성
        edited_msg = CMSHCI_AIEP_M_MINE_EDITED_PLAN_LIST()
        edited_msg.usPlanListCnt = self.plan_data.usPlanListCnt
        
        # 데이터 복사
        for i in range(15):
            self._copy_entire_list(
                self.plan_data.stMinePlanList[i],
                edited_msg.stMinePlanList[i]
            )
        
        # 메시지 송신
        try:
            self.publisher.writerCMSHCI_AIEP_M_MINE_EDITED_PLAN_LIST.write(edited_msg)
            messagebox.showinfo("Success", 
                                f"Plan lists saved and sent!\nTotal lists: {edited_msg.usPlanListCnt}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")


# =============================================================================
# Level 2: Plan List Editor Window
# =============================================================================

class PlanListEditorWindow(tk.Toplevel):
    """특정 목록 내 개별 계획들 편집 (최대 15개)"""
    
    def __init__(self, parent, plan_list, list_index):
        super().__init__(parent)
        self.title(f"Edit Plan List #{list_index+1}")
        self.geometry("1000x700")
        
        self.plan_list = plan_list  # ST_M_MINE_PLAN_LIST 참조
        self.list_index = list_index
        
        self._setup_ui()
        self._populate_tree()
    
    def _setup_ui(self):
        """UI 구성"""
        # 상단: 목록 정보
        info_frame = tk.LabelFrame(self, text="List Information", padx=10, pady=5)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # 목록 이름
        tk.Label(info_frame, text="List Name:").grid(row=0, column=0, sticky="w", padx=5)
        self.name_entry = tk.Entry(info_frame, width=40)
        current_name = extract_string_from_char_array(self.plan_list.chDescription)
        self.name_entry.insert(0, current_name)
        self.name_entry.grid(row=0, column=1, sticky="w", padx=5)
        
        # List ID (읽기 전용)
        tk.Label(info_frame, text="List ID:").grid(row=0, column=2, sticky="w", padx=20)
        tk.Label(info_frame, text=str(self.plan_list.sListID), 
                 font=("Arial", 10, "bold")).grid(row=0, column=3, sticky="w")
        
        # Ownship Waypoint Count
        tk.Label(info_frame, text="Ownship WP Count:").grid(row=1, column=0, sticky="w", padx=5)
        tk.Label(info_frame, text=str(self.plan_list.usOwnshipWaypointCnt),
                 font=("Arial", 10, "bold")).grid(row=1, column=1, sticky="w", padx=5)
        
        tk.Button(info_frame, text="Edit Ownship Waypoints",
                  command=self._edit_ownship_waypoints).grid(row=1, column=2, columnspan=2, padx=20)
        
        # 중앙: 계획 목록 Treeview
        tree_frame = tk.LabelFrame(self, text="Dropping Plans (Max 15)", padx=5, pady=5)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("Plan#", "Name", "State", "WP_Cnt", "Drop_Lat", "Drop_Lon", "Weapon_ID")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("Plan#", text="Plan #")
        self.tree.heading("Name", text="Description")
        self.tree.heading("State", text="State")
        self.tree.heading("WP_Cnt", text="WP Cnt")
        self.tree.heading("Drop_Lat", text="Drop Lat")
        self.tree.heading("Drop_Lon", text="Drop Lon")
        self.tree.heading("Weapon_ID", text="Weapon ID")
        
        self.tree.column("Plan#", width=60, anchor="center")
        self.tree.column("Name", width=200, anchor="w")
        self.tree.column("State", width=80, anchor="center")
        self.tree.column("WP_Cnt", width=70, anchor="center")
        self.tree.column("Drop_Lat", width=100, anchor="e")
        self.tree.column("Drop_Lon", width=100, anchor="e")
        self.tree.column("Weapon_ID", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭 이벤트
        self.tree.bind("<Double-1>", lambda e: self._edit_selected_plan())
        
        # 하단: 버튼들
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="Add Plan", command=self._add_new_plan,
                  width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Selected", command=self._edit_selected_plan,
                  width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=self._delete_selected_plan,
                  width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Apply Changes", command=self._apply_changes,
                  width=12, bg="lightgreen").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=self.destroy,
                  width=12).pack(side=tk.LEFT, padx=5)
    
    def _populate_tree(self):
        """Treeview에 계획 데이터 채우기"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i in range(15):
            plan_info = self.plan_list.stPlan[i]
            
            if is_plan_info_empty(plan_info):
                self.tree.insert("", "end", iid=str(i), values=(
                    i+1, "<Empty>", "-", "0", "-", "-", "-"
                ), tags=("empty",))
            else:
                name = extract_string_from_char_array(plan_info.cAdditionalText)
                state = plan_info.ePlanState
                wp_cnt = plan_info.usWaypointCnt
                drop_lat = f"{plan_info.stDropPos.dLatitude:.5f}"
                drop_lon = f"{plan_info.stDropPos.dLongitude:.5f}"
                weapon_id = plan_info.usWeaponID
                
                self.tree.insert("", "end", iid=str(i), values=(
                    i+1,
                    name if name else "<Unnamed>",
                    state,
                    wp_cnt,
                    drop_lat,
                    drop_lon,
                    weapon_id
                ))
        
        self.tree.tag_configure("empty", foreground="gray")
    
    def _add_new_plan(self):
        """새 계획 추가"""
        # 빈 슬롯 찾기
        empty_index = -1
        for i in range(15):
            if is_plan_info_empty(self.plan_list.stPlan[i]):
                empty_index = i
                break
        
        if empty_index == -1:
            messagebox.showwarning("Warning", "All 15 plan slots are full!")
            return
        
        # PlanDetailEditorWindow 오픈 (새 계획)
        editor = PlanDetailEditorWindow(self, self.plan_list, empty_index, is_new=True)
        self.wait_window(editor)
        self._populate_tree()
    
    def _edit_selected_plan(self):
        """선택된 계획 편집"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a plan!")
            return
        
        plan_index = int(self.tree.item(selection[0])["values"][0]) - 1
        
        if is_plan_info_empty(self.plan_list.stPlan[plan_index]):
            messagebox.showinfo("Info", "Cannot edit empty plan. Add a new plan first.")
            return
        
        editor = PlanDetailEditorWindow(self, self.plan_list, plan_index, is_new=False)
        self.wait_window(editor)
        self._populate_tree()
    
    def _delete_selected_plan(self):
        """선택된 계획 삭제"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a plan!")
            return
        
        plan_index = int(self.tree.item(selection[0])["values"][0]) - 1
        
        if not messagebox.askyesno("Confirm", f"Delete plan #{plan_index+1}?"):
            return
        
        # 계획 초기화
        plan_info = self.plan_list.stPlan[plan_index]
        self._clear_plan_info(plan_info)
        
        self._populate_tree()
        messagebox.showinfo("Success", "Plan deleted!")
    
    def _clear_plan_info(self, plan_info):
        """ST_M_MINE_PLAN_INFO 초기화"""
        plan_info.sListID = 0
        plan_info.usDroppingPlanNumber = 0
        plan_info.ePlanState = 0
        plan_info.usWeaponID = 0
        
        for i in range(50):
            plan_info.cAdditionalText[i] = 0
        
        plan_info.stDropPos.dLatitude = 0.0
        plan_info.stDropPos.dLongitude = 0.0
        plan_info.stDropPos.fDepth = 0.0
        plan_info.stDropPos.fSpeed = 0.0
        plan_info.stDropPos.bValid = 0
        
        plan_info.stLaunchPos.dLatitude = 0.0
        plan_info.stLaunchPos.dLongitude = 0.0
        plan_info.stLaunchPos.fDepth = 0.0
        plan_info.stLaunchPos.fSpeed = 0.0
        plan_info.stLaunchPos.bValid = 0
        
        plan_info.usWaypointCnt = 0
        for i in range(8):
            plan_info.stWaypoint[i].dLatitude = 0.0
            plan_info.stWaypoint[i].dLongitude = 0.0
            plan_info.stWaypoint[i].fDepth = 0.0
            plan_info.stWaypoint[i].fSpeed = 0.0
            plan_info.stWaypoint[i].bValid = 0
    
    def _edit_ownship_waypoints(self):
        """자함 변침점 편집"""
        editor = OwnshipWaypointEditorWindow(self, self.plan_list)
        self.wait_window(editor)
        
        # usOwnshipWaypointCnt 업데이트 (UI 리프레시)
        for widget in self.winfo_children():
            if isinstance(widget, tk.LabelFrame) and widget.cget("text") == "List Information":
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and child.cget("text").isdigit():
                        child.config(text=str(self.plan_list.usOwnshipWaypointCnt))
                        break
                break
    
    def _apply_changes(self):
        """변경사항 적용"""
        # 목록 이름 업데이트
        new_name = self.name_entry.get().strip()
        set_string_to_char_array(self.plan_list.chDescription, new_name, 50)
        
        messagebox.showinfo("Success", "Changes applied!")
        self.destroy()


# =============================================================================
# Level 2-1: Plan Detail Editor Window
# =============================================================================

class PlanDetailEditorWindow(tk.Toplevel):
    """개별 부설계획 상세 편집"""
    
    def __init__(self, parent, plan_list, plan_index, is_new=False):
        super().__init__(parent)
        self.title(f"Edit Plan #{plan_index+1}")
        self.geometry("800x700")
        
        self.plan_list = plan_list  # ST_M_MINE_PLAN_LIST 참조
        self.plan_index = plan_index
        self.plan_info = plan_list.stPlan[plan_index]
        self.is_new = is_new
        
        self._setup_ui()
        
        if not is_new:
            self._load_data()
    
    def _setup_ui(self):
        """UI 구성"""
        # 좌측 프레임: 기본 정보
        left_frame = tk.LabelFrame(self, text="Basic Information", padx=10, pady=5)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        tk.Label(left_frame, text="Plan Number:").grid(row=0, column=0, sticky="w", pady=3)
        self.plan_num_entry = tk.Entry(left_frame, width=10)
        self.plan_num_entry.grid(row=0, column=1, sticky="w", pady=3)
        
        tk.Label(left_frame, text="Description:").grid(row=1, column=0, sticky="w", pady=3)
        self.desc_entry = tk.Entry(left_frame, width=30)
        self.desc_entry.grid(row=1, column=1, sticky="w", pady=3)
        
        tk.Label(left_frame, text="Weapon ID:").grid(row=2, column=0, sticky="w", pady=3)
        self.weapon_id_entry = tk.Entry(left_frame, width=10)
        self.weapon_id_entry.grid(row=2, column=1, sticky="w", pady=3)
        
        tk.Label(left_frame, text="State (0-6):").grid(row=3, column=0, sticky="w", pady=3)
        self.state_entry = tk.Entry(left_frame, width=10)
        self.state_entry.grid(row=3, column=1, sticky="w", pady=3)
        
        # 중앙 프레임: 위치 정보
        center_frame = tk.LabelFrame(self, text="Positions", padx=10, pady=5)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Launch Position
        tk.Label(center_frame, text="Launch Position", 
                 font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        tk.Label(center_frame, text="Latitude:").grid(row=1, column=0, sticky="w")
        self.launch_lat_entry = tk.Entry(center_frame, width=15)
        self.launch_lat_entry.grid(row=1, column=1, pady=2)
        
        tk.Label(center_frame, text="Longitude:").grid(row=2, column=0, sticky="w")
        self.launch_lon_entry = tk.Entry(center_frame, width=15)
        self.launch_lon_entry.grid(row=2, column=1, pady=2)
        
        tk.Label(center_frame, text="Depth:").grid(row=3, column=0, sticky="w")
        self.launch_depth_entry = tk.Entry(center_frame, width=15)
        self.launch_depth_entry.grid(row=3, column=1, pady=2)
        
        tk.Label(center_frame, text="Speed:").grid(row=4, column=0, sticky="w")
        self.launch_speed_entry = tk.Entry(center_frame, width=15)
        self.launch_speed_entry.grid(row=4, column=1, pady=2)
        
        # Drop Position
        tk.Label(center_frame, text="Drop Position",
                 font=("Arial", 9, "bold")).grid(row=5, column=0, columnspan=2, pady=5)
        
        tk.Label(center_frame, text="Latitude:").grid(row=6, column=0, sticky="w")
        self.drop_lat_entry = tk.Entry(center_frame, width=15)
        self.drop_lat_entry.grid(row=6, column=1, pady=2)
        
        tk.Label(center_frame, text="Longitude:").grid(row=7, column=0, sticky="w")
        self.drop_lon_entry = tk.Entry(center_frame, width=15)
        self.drop_lon_entry.grid(row=7, column=1, pady=2)
        
        tk.Label(center_frame, text="Depth:").grid(row=8, column=0, sticky="w")
        self.drop_depth_entry = tk.Entry(center_frame, width=15)
        self.drop_depth_entry.grid(row=8, column=1, pady=2)
        
        tk.Label(center_frame, text="Speed:").grid(row=9, column=0, sticky="w")
        self.drop_speed_entry = tk.Entry(center_frame, width=15)
        self.drop_speed_entry.grid(row=9, column=1, pady=2)
        
        # 하단: 경로점 편집
        wp_frame = tk.LabelFrame(self, text="Waypoints (Max 8)", padx=10, pady=5)
        wp_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Waypoint Treeview
        wp_columns = ("WP#", "Lat", "Lon", "Depth", "Speed", "Valid")
        self.wp_tree = ttk.Treeview(wp_frame, columns=wp_columns, show="headings", height=6)
        
        for col in wp_columns:
            self.wp_tree.heading(col, text=col)
            self.wp_tree.column(col, width=100, anchor="center")
        
        self.wp_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Waypoint 버튼
        wp_btn_frame = tk.Frame(wp_frame)
        wp_btn_frame.pack(side=tk.BOTTOM, pady=5)
        
        tk.Button(wp_btn_frame, text="Add WP", command=self._add_waypoint).pack(side=tk.LEFT, padx=3)
        tk.Button(wp_btn_frame, text="Edit WP", command=self._edit_waypoint).pack(side=tk.LEFT, padx=3)
        tk.Button(wp_btn_frame, text="Delete WP", command=self._delete_waypoint).pack(side=tk.LEFT, padx=3)
        
        # 최하단: Apply/Cancel 버튼
        bottom_frame = tk.Frame(self)
        bottom_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(bottom_frame, text="Apply", command=self._apply,
                  width=15, bg="lightgreen").pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="Cancel", command=self.destroy,
                  width=15).pack(side=tk.LEFT, padx=10)
        
        # Grid 설정
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
    
    def _load_data(self):
        """기존 데이터 로드"""
        # 기본 정보
        self.plan_num_entry.insert(0, str(self.plan_info.usDroppingPlanNumber))
        self.desc_entry.insert(0, extract_string_from_char_array(self.plan_info.cAdditionalText))
        self.weapon_id_entry.insert(0, str(self.plan_info.usWeaponID))
        self.state_entry.insert(0, str(self.plan_info.ePlanState))
        
        # Launch Position
        self.launch_lat_entry.insert(0, str(self.plan_info.stLaunchPos.dLatitude))
        self.launch_lon_entry.insert(0, str(self.plan_info.stLaunchPos.dLongitude))
        self.launch_depth_entry.insert(0, str(self.plan_info.stLaunchPos.fDepth))
        self.launch_speed_entry.insert(0, str(self.plan_info.stLaunchPos.fSpeed))
        
        # Drop Position
        self.drop_lat_entry.insert(0, str(self.plan_info.stDropPos.dLatitude))
        self.drop_lon_entry.insert(0, str(self.plan_info.stDropPos.dLongitude))
        self.drop_depth_entry.insert(0, str(self.plan_info.stDropPos.fDepth))
        self.drop_speed_entry.insert(0, str(self.plan_info.stDropPos.fSpeed))
        
        # Waypoints
        self._populate_waypoint_tree()
    
    def _populate_waypoint_tree(self):
        """경로점 트리 채우기"""
        for item in self.wp_tree.get_children():
            self.wp_tree.delete(item)
        
        wp_cnt = self.plan_info.usWaypointCnt
        for i in range(8):
            if i < wp_cnt:
                wp = self.plan_info.stWaypoint[i]
                self.wp_tree.insert("", "end", iid=str(i), values=(
                    i+1,
                    f"{wp.dLatitude:.5f}",
                    f"{wp.dLongitude:.5f}",
                    f"{wp.fDepth:.2f}",
                    f"{wp.fSpeed:.2f}",
                    wp.bValid
                ))
            else:
                self.wp_tree.insert("", "end", iid=str(i), values=(
                    i+1, "-", "-", "-", "-", "-"
                ), tags=("empty",))
        
        self.wp_tree.tag_configure("empty", foreground="gray")
    
    def _add_waypoint(self):
        """경로점 추가"""
        wp_cnt = self.plan_info.usWaypointCnt
        if wp_cnt >= 8:
            messagebox.showwarning("Warning", "Maximum 8 waypoints allowed!")
            return
        
        # 입력 다이얼로그
        dialog = tk.Toplevel(self)
        dialog.title(f"Add Waypoint #{wp_cnt+1}")
        dialog.geometry("300x200")
        
        tk.Label(dialog, text="Latitude:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        lat_entry = tk.Entry(dialog, width=20)
        lat_entry.grid(row=0, column=1, padx=5, pady=3)
        
        tk.Label(dialog, text="Longitude:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        lon_entry = tk.Entry(dialog, width=20)
        lon_entry.grid(row=1, column=1, padx=5, pady=3)
        
        tk.Label(dialog, text="Depth:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        depth_entry = tk.Entry(dialog, width=20)
        depth_entry.grid(row=2, column=1, padx=5, pady=3)
        
        tk.Label(dialog, text="Speed:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        speed_entry = tk.Entry(dialog, width=20)
        speed_entry.grid(row=3, column=1, padx=5, pady=3)
        
        def confirm():
            try:
                wp = self.plan_info.stWaypoint[wp_cnt]
                wp.dLatitude = float(lat_entry.get())
                wp.dLongitude = float(lon_entry.get())
                wp.fDepth = float(depth_entry.get())
                wp.fSpeed = float(speed_entry.get())
                wp.bValid = 1
                
                self.plan_info.usWaypointCnt += 1
                self._populate_waypoint_tree()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid input!")
        
        tk.Button(dialog, text="OK", command=confirm).grid(row=4, column=0, columnspan=2, pady=10)
    
    def _edit_waypoint(self):
        """경로점 편집"""
        selection = self.wp_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a waypoint!")
            return
        
        wp_index = int(self.wp_tree.item(selection[0])["values"][0]) - 1
        
        if wp_index >= self.plan_info.usWaypointCnt:
            messagebox.showinfo("Info", "Cannot edit empty waypoint!")
            return
        
        wp = self.plan_info.stWaypoint[wp_index]
        
        # 입력 다이얼로그
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Waypoint #{wp_index+1}")
        dialog.geometry("300x200")
        
        tk.Label(dialog, text="Latitude:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        lat_entry = tk.Entry(dialog, width=20)
        lat_entry.insert(0, str(wp.dLatitude))
        lat_entry.grid(row=0, column=1, padx=5, pady=3)
        
        tk.Label(dialog, text="Longitude:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        lon_entry = tk.Entry(dialog, width=20)
        lon_entry.insert(0, str(wp.dLongitude))
        lon_entry.grid(row=1, column=1, padx=5, pady=3)
        
        tk.Label(dialog, text="Depth:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        depth_entry = tk.Entry(dialog, width=20)
        depth_entry.insert(0, str(wp.fDepth))
        depth_entry.grid(row=2, column=1, padx=5, pady=3)
        
        tk.Label(dialog, text="Speed:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        speed_entry = tk.Entry(dialog, width=20)
        speed_entry.insert(0, str(wp.fSpeed))
        speed_entry.grid(row=3, column=1, padx=5, pady=3)
        
        def confirm():
            try:
                wp.dLatitude = float(lat_entry.get())
                wp.dLongitude = float(lon_entry.get())
                wp.fDepth = float(depth_entry.get())
                wp.fSpeed = float(speed_entry.get())
                
                self._populate_waypoint_tree()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid input!")
        
        tk.Button(dialog, text="OK", command=confirm).grid(row=4, column=0, columnspan=2, pady=10)
    
    def _delete_waypoint(self):
        """경로점 삭제"""
        selection = self.wp_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a waypoint!")
            return
        
        wp_index = int(self.wp_tree.item(selection[0])["values"][0]) - 1
        
        if wp_index >= self.plan_info.usWaypointCnt:
            messagebox.showinfo("Info", "Cannot delete empty waypoint!")
            return
        
        # 뒤의 경로점들을 앞으로 당기기
        for i in range(wp_index, 7):
            if i+1 < 8:
                self.plan_info.stWaypoint[i].dLatitude = self.plan_info.stWaypoint[i+1].dLatitude
                self.plan_info.stWaypoint[i].dLongitude = self.plan_info.stWaypoint[i+1].dLongitude
                self.plan_info.stWaypoint[i].fDepth = self.plan_info.stWaypoint[i+1].fDepth
                self.plan_info.stWaypoint[i].fSpeed = self.plan_info.stWaypoint[i+1].fSpeed
                self.plan_info.stWaypoint[i].bValid = self.plan_info.stWaypoint[i+1].bValid
        
        # 마지막 경로점 초기화
        last_wp = self.plan_info.stWaypoint[7]
        last_wp.dLatitude = 0.0
        last_wp.dLongitude = 0.0
        last_wp.fDepth = 0.0
        last_wp.fSpeed = 0.0
        last_wp.bValid = 0
        
        self.plan_info.usWaypointCnt -= 1
        self._populate_waypoint_tree()
    
    def _apply(self):
        """변경사항 적용"""
        try:
            # 기본 정보
            self.plan_info.usDroppingPlanNumber = int(self.plan_num_entry.get())
            self.plan_info.usWeaponID = int(self.weapon_id_entry.get())
            self.plan_info.ePlanState = int(self.state_entry.get())
            
            desc = self.desc_entry.get().strip()
            set_string_to_char_array(self.plan_info.cAdditionalText, desc, 50)
            
            # sListID 설정 (목록의 sListID와 동일하게)
            self.plan_info.sListID = self.plan_list.sListID
            
            # Launch Position
            self.plan_info.stLaunchPos.dLatitude = float(self.launch_lat_entry.get())
            self.plan_info.stLaunchPos.dLongitude = float(self.launch_lon_entry.get())
            self.plan_info.stLaunchPos.fDepth = float(self.launch_depth_entry.get())
            self.plan_info.stLaunchPos.fSpeed = float(self.launch_speed_entry.get())
            self.plan_info.stLaunchPos.bValid = 1
            
            # Drop Position
            self.plan_info.stDropPos.dLatitude = float(self.drop_lat_entry.get())
            self.plan_info.stDropPos.dLongitude = float(self.drop_lon_entry.get())
            self.plan_info.stDropPos.fDepth = float(self.drop_depth_entry.get())
            self.plan_info.stDropPos.fSpeed = float(self.drop_speed_entry.get())
            self.plan_info.stDropPos.bValid = 1
            
            messagebox.showinfo("Success", "Plan updated successfully!")
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")


# =============================================================================
# Level 2-2: Ownship Waypoint Editor Window
# =============================================================================

class OwnshipWaypointEditorWindow(tk.Toplevel):
    """자함 변침점 편집 (최대 40개)"""
    
    def __init__(self, parent, plan_list):
        super().__init__(parent)
        self.title("Edit Ownship Waypoints")
        self.geometry("900x600")
        
        self.plan_list = plan_list  # ST_M_MINE_PLAN_LIST 참조
        
        self._setup_ui()
        self._populate_tree()
    
    def _setup_ui(self):
        """UI 구성"""
        # 상단 정보
        info_frame = tk.Frame(self)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(info_frame, text=f"Ownship Waypoint Count: {self.plan_list.usOwnshipWaypointCnt}",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # Treeview
        tree_frame = tk.Frame(self)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("WP#", "Lat", "Lon", "Depth", "Speed", "Heading", "Launch", "ListID")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            width = 80 if col != "Lat" and col != "Lon" else 100
            self.tree.column(col, width=width, anchor="center")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 버튼
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        
        tk.Button(btn_frame, text="Add WP", command=self._add_waypoint, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit WP", command=self._edit_waypoint, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete WP", command=self._delete_waypoint, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Apply", command=self.destroy, width=12, bg="lightgreen").pack(side=tk.LEFT, padx=5)
    
    def _populate_tree(self):
        """트리 채우기"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        wp_cnt = self.plan_list.usOwnshipWaypointCnt
        
        for i in range(40):
            if i < wp_cnt:
                wp = self.plan_list.stOwnshipWaypoint[i]
                self.tree.insert("", "end", iid=str(i), values=(
                    i+1,
                    f"{wp.dLatitude:.5f}",
                    f"{wp.dLongitude:.5f}",
                    f"{wp.fDepth:.2f}",
                    f"{wp.fSpeed:.2f}",
                    f"{wp.fHeading:.2f}",
                    wp.bLaunchPoint,
                    wp.usListID
                ))
            else:
                self.tree.insert("", "end", iid=str(i), values=(
                    i+1, "-", "-", "-", "-", "-", "-", "-"
                ), tags=("empty",))
        
        self.tree.tag_configure("empty", foreground="gray")
    
    def _add_waypoint(self):
        """경로점 추가"""
        wp_cnt = self.plan_list.usOwnshipWaypointCnt
        if wp_cnt >= 40:
            messagebox.showwarning("Warning", "Maximum 40 waypoints allowed!")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Add Ownship WP #{wp_cnt+1}")
        dialog.geometry("350x250")
        
        fields = [
            ("Latitude:", "lat"),
            ("Longitude:", "lon"),
            ("Depth:", "depth"),
            ("Speed:", "speed"),
            ("Heading:", "heading"),
            ("Launch Point (0/1):", "launch"),
        ]
        
        entries = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(dialog, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            entry = tk.Entry(dialog, width=20)
            entry.grid(row=i, column=1, padx=5, pady=3)
            entries[key] = entry
        
        def confirm():
            try:
                wp = self.plan_list.stOwnshipWaypoint[wp_cnt]
                wp.dLatitude = float(entries["lat"].get())
                wp.dLongitude = float(entries["lon"].get())
                wp.fDepth = float(entries["depth"].get())
                wp.fSpeed = float(entries["speed"].get())
                wp.fHeading = float(entries["heading"].get())
                wp.bLaunchPoint = int(entries["launch"].get())
                wp.usListID = self.plan_list.sListID
                
                self.plan_list.usOwnshipWaypointCnt += 1
                self._populate_tree()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid input!")
        
        tk.Button(dialog, text="OK", command=confirm).grid(row=len(fields), column=0, columnspan=2, pady=10)
    
    def _edit_waypoint(self):
        """경로점 편집"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a waypoint!")
            return
        
        wp_index = int(self.tree.item(selection[0])["values"][0]) - 1
        
        if wp_index >= self.plan_list.usOwnshipWaypointCnt:
            messagebox.showinfo("Info", "Cannot edit empty waypoint!")
            return
        
        wp = self.plan_list.stOwnshipWaypoint[wp_index]
        
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Ownship WP #{wp_index+1}")
        dialog.geometry("350x250")
        
        fields = [
            ("Latitude:", "lat", wp.dLatitude),
            ("Longitude:", "lon", wp.dLongitude),
            ("Depth:", "depth", wp.fDepth),
            ("Speed:", "speed", wp.fSpeed),
            ("Heading:", "heading", wp.fHeading),
            ("Launch Point (0/1):", "launch", wp.bLaunchPoint),
        ]
        
        entries = {}
        for i, (label, key, value) in enumerate(fields):
            tk.Label(dialog, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            entry = tk.Entry(dialog, width=20)
            entry.insert(0, str(value))
            entry.grid(row=i, column=1, padx=5, pady=3)
            entries[key] = entry
        
        def confirm():
            try:
                wp.dLatitude = float(entries["lat"].get())
                wp.dLongitude = float(entries["lon"].get())
                wp.fDepth = float(entries["depth"].get())
                wp.fSpeed = float(entries["speed"].get())
                wp.fHeading = float(entries["heading"].get())
                wp.bLaunchPoint = int(entries["launch"].get())
                
                self._populate_tree()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid input!")
        
        tk.Button(dialog, text="OK", command=confirm).grid(row=len(fields), column=0, columnspan=2, pady=10)
    
    def _delete_waypoint(self):
        """경로점 삭제"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a waypoint!")
            return
        
        wp_index = int(self.tree.item(selection[0])["values"][0]) - 1
        
        if wp_index >= self.plan_list.usOwnshipWaypointCnt:
            messagebox.showinfo("Info", "Cannot delete empty waypoint!")
            return
        
        # 뒤의 경로점들을 앞으로 당기기
        for i in range(wp_index, 39):
            if i+1 < 40:
                src = self.plan_list.stOwnshipWaypoint[i+1]
                dst = self.plan_list.stOwnshipWaypoint[i]
                dst.dLatitude = src.dLatitude
                dst.dLongitude = src.dLongitude
                dst.fDepth = src.fDepth
                dst.fSpeed = src.fSpeed
                dst.fHeading = src.fHeading
                dst.bLaunchPoint = src.bLaunchPoint
                dst.usListID = src.usListID
        
        # 마지막 경로점 초기화
        last_wp = self.plan_list.stOwnshipWaypoint[39]
        last_wp.dLatitude = 0.0
        last_wp.dLongitude = 0.0
        last_wp.fDepth = 0.0
        last_wp.fSpeed = 0.0
        last_wp.fHeading = 0.0
        last_wp.bLaunchPoint = 0
        last_wp.usListID = 0
        
        self.plan_list.usOwnshipWaypointCnt -= 1
        self._populate_tree()
