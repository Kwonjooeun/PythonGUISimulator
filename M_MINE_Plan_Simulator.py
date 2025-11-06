# _*_ coding: utf-8 _*_
#from rti.connextdds import Int8Seq
from tkinter.constants import FALSE
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Circle
import numpy as np
from Communication.aiep_msg_subscriber import MySubscriber
from Communication.aiep_msg_publisher import MYPublisher
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import time
import json
import os
import sys
import array
import ast
import re
from DDSDisplayConverter import DdsDisplayConverter
from dds_display import  DisplayST_M_MINE_PLAN_INFO, DisplayST_MINE_POINT
from dds.AIEP_AIEP_ import CMSHCI_AIEP_M_MINE_SELECTED_PLAN, AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST, CMSHCI_AIEP_M_MINE_EDITED_PLAN_LIST, ST_M_MINE_PLAN_INFO, ST_M_MINE_PLAN_LIST, ST_WEAPON_WAYPOINT, CMSHCI_AIEP_WPN_GEO_WAYPOINTS, NAVINF_SHIP_NAVIGATION_INFO, TEWA_WA_TUBE_LOAD_INFO, TRKMGR_SYSTEMTARGET_INFO, AIEP_WPN_CTRL_STATUS_INFO
from TEWA_ASSIGN_CMD_Window import TEWAAssignCmdWindow
from WpnCtrlCmdWindow import WpnCtrlCmdWindow
from PAInfoWindow import PAInfoWindow
from WpnGeoWaypointsWindow import WpnGeoWaypointsWindow
from AIWaypointsInferenceRequestWindow import AIWaypointsInferenceRequestWindow


# --- Main GUI Class ---
class M_MINE_PlanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dropping Plan Application")

        # DDS publishers/subscribers
        self.req_publisher = MYPublisher()
        self.req_publisher.initialize_participant(83)

        # 애플리케이션 시작 시 subscriber 스레드 시작
        threading.Thread(target=self.run_subscriber_thread, args=(83,), daemon=True).start()

        # Main button: "Plan List" (to request all plan lists from other program)
        self.plan_list_request_btn = tk.Button(root, text="Plan List", command=self.request_plan_list)
        self.plan_list_request_btn.pack(pady=10)

        self.TEWA_ASSIGN_CMD_btn = tk.Button(
            root, 
            text="TEWA_ASSIGN", 
            command=TEWAAssignCmdWindow(self.root, self.req_publisher)
            )

        # 무장 통제 명령 버튼 추가
        self.wpn_ctrl_cmd_btn = tk.Button(
            root,
            text="Weapon Control",
            command=WpnCtrlCmdWindow(self.root, self.req_publisher)
        )
        self.wpn_ctrl_cmd_btn.pack(pady=5)
      
        # 교전계획 플롯 버튼 추가
        self.plot_ep_btn = tk.Button(
            root, 
            text="Show Engagement Plan", 
            command=self.show_engagement_plan
        )
        self.plot_ep_btn.pack(pady=5)
      
        # Prohibited area info button
        self.pa_info_btn = tk.Button(
            root,
            text="Prohibited Areas",
            command=PAInfoWindow(self.root, self.req_publisher, self)
        )
        self.pa_info_btn.pack(pady=5)

        # 경로점 수정 버튼 추가
        self.wpn_waypoints_btn = tk.Button(
            root,
            text="Modify Waypoints",
            command=WpnGeoWaypointsWindow(self.root, self.req_publisher)
        )
        self.wpn_waypoints_btn.pack(pady=5)

        # AI 경로점 추천 요청 버튼 추가 (버튼 텍스트 변경)
        self.ai_waypoints_req_btn = tk.Button(
            root,
            text="Request AI Waypoints",
            command=AIWaypointsInferenceRequestWindow(self.root, self.req_publisher)
        )
        self.ai_waypoints_req_btn.pack(pady=5)

    def run_subscriber_thread(self, domainID):
        MySubscriber.run_subscriber(domain_id=domainID, sample_count=sys.maxsize)

    # --- DDS Request/Response ---
    def request_plan_list(self):
        # 전송: AIEP_DROPPING_PLAN_REQ 메시지
        print("'Dropping plan' button selected.")
        self.req_publisher.publish_CMSHCI_AIEP_M_MINE_DROPPING_PLAN_REQ()

        # 데이터가 수신되었는지 확인합니다.
        self.open_plan_list_window()

    def open_plan_list_window(self):
        # 데이터가 수신되었는지 확인합니다.
        if MySubscriber.data_AIEP_CMSHCI_M_MINE_ALL_PLAN_LIST is None:
            # 또는 주기적으로 체크하는 타이머를 설정할 수도 있습니다.
            self.root.after(500, self.open_plan_list_window)
        else:
            # 데이터가 수신되었으면 Plan List 창을 생성합니다. 
            self.create_plan_list_window() # TODO. 이 함수를 다른 버튼들의 동작처럼 외부 파일에서 구현 후 사용하도록 구현 수정 필요
