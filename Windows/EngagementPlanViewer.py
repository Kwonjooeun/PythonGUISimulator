# -*- coding: utf-8 -*-
"""
EngagementPlanViewer.py
교전계획 전시 시스템 (수정됨)
- 자함 위치 전시 기능 추가
- 금지 구역 원통 형태로 전시 (심도 100m ~ 수면)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Circle
import matplotlib.patches as mpatches
import numpy as np
import threading
import time
from Communication.aiep_msg_subscriber import MySubscriber
from dds.AIEP_AIEP_ import (
    AIEP_M_MINE_EP_RESULT,
    AIEP_ALM_ASM_EP_RESULT,
    AIEP_WGT_EP_RESULT,
    AIEP_AAM_EP_RESULT,
    NAVINF_SHIP_NAVIGATION_INFO,
    CMSHCI_AIEP_PA_INFO
)


# =============================================================================
# Weapon Type Mapping
# =============================================================================

WEAPON_TYPES = {
    1: "WGT (Torpedo)",
    2: "M_MINE (Mine)",
    3: "ASM (Anti-Ship)",
    4: "ALM (Anti-Land)",
    5: "AAM (Anti-Air)"
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_tube_ep_data(tube_num):
    """Get engagement plan data for specific tube"""
    # M_MINE
    if hasattr(MySubscriber, 'data_AIEP_M_MINE_EP_RESULT'):
        data = MySubscriber.data_AIEP_M_MINE_EP_RESULT
        if data and data.enTubeNum == tube_num:
            return ('M_MINE', data)
    
    # ALM/ASM
    if hasattr(MySubscriber, 'data_AIEP_ALM_ASM_EP_RESULT'):
        data = MySubscriber.data_AIEP_ALM_ASM_EP_RESULT
        if data and data.enTubeNum == tube_num:
            return ('ALM_ASM', data)
    
    # WGT
    if hasattr(MySubscriber, 'data_AIEP_WGT_EP_RESULT'):
        data = MySubscriber.data_AIEP_WGT_EP_RESULT
        if data and data.enTubeNum == tube_num:
            return ('WGT', data)
    
    # AAM
    if hasattr(MySubscriber, 'data_AIEP_AAM_EP_RESULT'):
        data = MySubscriber.data_AIEP_AAM_EP_RESULT
        if data and data.eTubeNum == tube_num:
            return ('AAM', data)
    
    return (None, None)


def get_ownship_info():
    """Get ownship navigation info"""
    if hasattr(MySubscriber, 'data_NAVINF_SHIP_NAVIGATION_INFO'):
        return MySubscriber.data_NAVINF_SHIP_NAVIGATION_INFO
    return None


def get_pa_info():
    """Get prohibited area info"""
    if hasattr(MySubscriber, 'data_CMSHCI_AIEP_PA_INFO'):
        return MySubscriber.data_CMSHCI_AIEP_PA_INFO
    return None


# =============================================================================
# Engagement Plan Viewer Class
# =============================================================================

class EngagementPlanViewer:
    """
    교전계획 3D 시각화 뷰어
    - 무장별 궤적 전시
    - 경로점 및 표적 위치 전시
    - 자함 위치 전시 (신규)
    - 금지구역 원통형 전시 (신규)
    """
    
    def __init__(self, parent, tube_num, gui_instance=None):
        self.parent = parent
        self.tube_num = tube_num
        self.gui_instance = gui_instance
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Engagement Plan - Tube {tube_num}")
        self.window.geometry("1200x900")
        
        # Matplotlib figure setup
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = tk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Refresh button
        refresh_btn = tk.Button(
            control_frame,
            text="Refresh",
            command=self.update_plot
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_check = tk.Checkbutton(
            control_frame,
            text="Auto Refresh (1s)",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        auto_refresh_check.pack(side=tk.LEFT, padx=5)
        
        # Initial plot
        self.update_plot()
        
        # Auto-refresh thread
        self.auto_refresh_thread = None
        self.auto_refresh_running = False
        
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality"""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        """Start auto-refresh thread"""
        if not self.auto_refresh_running:
            self.auto_refresh_running = True
            self.auto_refresh_thread = threading.Thread(
                target=self._auto_refresh_loop,
                daemon=True
            )
            self.auto_refresh_thread.start()
    
    def stop_auto_refresh(self):
        """Stop auto-refresh thread"""
        self.auto_refresh_running = False
    
    def _auto_refresh_loop(self):
        """Auto-refresh loop"""
        while self.auto_refresh_running:
            try:
                self.window.after(0, self.update_plot)
                time.sleep(1.0)
            except:
                break
    
    def update_plot(self):
        """Update the 3D plot with engagement plan data"""
        self.ax.clear()
        
        # Get engagement plan data
        wpn_type, ep_data = get_tube_ep_data(self.tube_num)
        
        if wpn_type is None or ep_data is None:
            self.ax.text2D(
                0.5, 0.5,
                f"No engagement plan data for Tube {self.tube_num}",
                transform=self.ax.transAxes,
                ha='center'
            )
            self.canvas.draw()
            return
        
        # Collect all coordinates for axis scaling
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Plot based on weapon type
        if wpn_type == 'M_MINE':
            lons, lats, depths = self._plot_m_mine(ep_data)
        elif wpn_type == 'ALM_ASM':
            lons, lats, depths = self._plot_alm_asm(ep_data)
        elif wpn_type == 'WGT':
            lons, lats, depths = self._plot_wgt(ep_data)
        elif wpn_type == 'AAM':
            lons, lats, depths = self._plot_aam(ep_data)
        else:
            lons, lats, depths = [], [], []
        
        all_lons.extend(lons)
        all_lats.extend(lats)
        all_depths.extend(depths)
        
        # Plot ownship position (신규 기능)
        ownship_lons, ownship_lats, ownship_depths = self._plot_ownship()
        all_lons.extend(ownship_lons)
        all_lats.extend(ownship_lats)
        all_depths.extend(ownship_depths)
        
        # Plot prohibited areas (신규 기능)
        pa_lons, pa_lats, pa_depths = self._plot_prohibited_areas()
        all_lons.extend(pa_lons)
        all_lats.extend(pa_lats)
        all_depths.extend(pa_depths)
        
        # Set axis labels and limits
        self.ax.set_xlabel('Longitude (deg)')
        self.ax.set_ylabel('Latitude (deg)')
        self.ax.set_zlabel('Depth (m)')
        
        if all_lons and all_lats and all_depths:
            self._set_axis_limits(all_lons, all_lats, all_depths)
        
        # Title
        weapon_name = WEAPON_TYPES.get(wpn_type, wpn_type)
        self.ax.set_title(
            f'Engagement Plan - Tube {self.tube_num} ({weapon_name})',
            fontsize=14,
            fontweight='bold'
        )
        
        # Legend
        self.ax.legend(loc='upper right')
        
        # Invert Z-axis (depth increases downward)
        self.ax.invert_zaxis()
        
        # Draw
        self.canvas.draw()
    
    def _plot_ownship(self):
        """
        자함 위치 전시 (신규 기능)
        Returns: (lons, lats, depths) lists for axis scaling
        """
        ownship_info = get_ownship_info()
        
        if ownship_info is None:
            return [], [], []
        
        # 자함 위치 좌표 추출
        ownship_lon = ownship_info.dLongitude
        ownship_lat = ownship_info.dLatitude
        ownship_depth = -ownship_info.fDepth  # 심도는 음수로 표현 (아래방향)
        
        # 유효한 좌표인지 확인
        if ownship_lon == 0 and ownship_lat == 0:
            return [], [], []
        
        # 자함 위치를 큰 마커로 표시
        self.ax.scatter(
            [ownship_lon],
            [ownship_lat],
            [ownship_depth],
            c='blue',
            s=300,
            marker='^',  # 삼각형 마커
            edgecolors='black',
            linewidths=2,
            label='Ownship',
            zorder=100  # 다른 요소들 위에 표시
        )
        
        # 자함 위치에 텍스트 레이블 추가
        self.ax.text(
            ownship_lon,
            ownship_lat,
            ownship_depth,
            '  Ownship',
            fontsize=10,
            fontweight='bold',
            color='blue'
        )
        
        return [ownship_lon], [ownship_lat], [ownship_depth]
    
    def _plot_prohibited_areas(self):
        """
        금지구역 원통형 전시 (신규 기능)
        심도 100m ~ 수면(0m)까지 원통 형태로 표시
        Returns: (lons, lats, depths) lists for axis scaling
        """
        pa_info = get_pa_info()
        
        if pa_info is None or pa_info.nCountPA <= 0:
            return [], [], []
        
        all_lons = []
        all_lats = []
        all_depths = []
        
        # 각 금지구역을 원통으로 그림
        for i in range(pa_info.nCountPA):
            pa_point = pa_info.stPaPoint[i]
            
            # 금지구역 중심 좌표 및 반지름
            center_lon = pa_point.dLongitude
            center_lat = pa_point.dLatitude
            radius = pa_point.dRadius  # 단위: meter
            
            # 유효한 좌표인지 확인
            if center_lon == 0 and center_lat == 0:
                continue
            
            # 반지름을 대략적인 경위도 변환 (간단한 근사)
            # 1도 경도 ≈ 111km * cos(위도)
            # 1도 위도 ≈ 111km
            lat_rad = np.radians(center_lat)
            radius_lon = radius / (111000 * np.cos(lat_rad))  # meter를 경도로 변환
            radius_lat = radius / 111000  # meter를 위도로 변환
            
            # 원통의 상단(수면, 0m)과 하단(심도 100m) 정의
            top_depth = 0  # 수면
            bottom_depth = -100  # 심도 100m (음수)
            
            # 원의 둘레를 그리기 위한 각도 배열
            theta = np.linspace(0, 2 * np.pi, 50)
            
            # 상단 원 (수면)
            top_circle_lons = center_lon + radius_lon * np.cos(theta)
            top_circle_lats = center_lat + radius_lat * np.sin(theta)
            top_circle_depths = np.full_like(theta, top_depth)
            
            # 하단 원 (심도 100m)
            bottom_circle_lons = center_lon + radius_lon * np.cos(theta)
            bottom_circle_lats = center_lat + radius_lat * np.sin(theta)
            bottom_circle_depths = np.full_like(theta, bottom_depth)
            
            # 원통의 상단 원 그리기
            label = f'PA #{i+1} (Top)' if i == 0 else None
            self.ax.plot(
                top_circle_lons,
                top_circle_lats,
                top_circle_depths,
                'r-',
                linewidth=2,
                alpha=0.7,
                label=label
            )
            
            # 원통의 하단 원 그리기
            self.ax.plot(
                bottom_circle_lons,
                bottom_circle_lats,
                bottom_circle_depths,
                'r-',
                linewidth=2,
                alpha=0.7
            )
            
            # 원통의 옆면을 수직선으로 연결 (8개 방향)
            for j in range(0, len(theta), len(theta) // 8):
                self.ax.plot(
                    [top_circle_lons[j], bottom_circle_lons[j]],
                    [top_circle_lats[j], bottom_circle_lats[j]],
                    [top_circle_depths[j], bottom_circle_depths[j]],
                    'r-',
                    linewidth=1,
                    alpha=0.5
                )
            
            # 반투명 원통 표면 (mesh)
            # 원통의 옆면을 메쉬로 채우기
            z_cylinder = np.linspace(bottom_depth, top_depth, 10)
            theta_mesh, z_mesh = np.meshgrid(theta, z_cylinder)
            x_mesh = center_lon + radius_lon * np.cos(theta_mesh)
            y_mesh = center_lat + radius_lat * np.sin(theta_mesh)
            
            self.ax.plot_surface(
                x_mesh,
                y_mesh,
                z_mesh,
                color='red',
                alpha=0.15,
                rstride=1,
                cstride=1,
                linewidth=0,
                antialiased=True
            )
            
            # 좌표 수집 (축 범위 설정용)
            all_lons.extend(top_circle_lons.tolist())
            all_lats.extend(top_circle_lats.tolist())
            all_depths.extend([top_depth, bottom_depth])
        
        return all_lons, all_lats, all_depths
    
    def _plot_m_mine(self, ep_data):
        """
        Plot M_MINE engagement plan
        Returns: (lons, lats, depths) for axis scaling
        """
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Trajectory
        traj_lons = []
        traj_lats = []
        traj_depths = []
        
        for i in range(ep_data.unCntTrajectory):
            traj = ep_data.stTrajectories[i]
            if traj.dLatitude != 0 or traj.dLongitude != 0:
                traj_lons.append(traj.dLongitude)
                traj_lats.append(traj.dLatitude)
                traj_depths.append(-traj.fDepth)  # Depth is negative
        
        if traj_lons:
            self.ax.plot(
                traj_lons, traj_lats, traj_depths,
                'b-', linewidth=2, label='Trajectory'
            )
            all_lons.extend(traj_lons)
            all_lats.extend(traj_lats)
            all_depths.extend(traj_depths)
        
        # Waypoints
        wp_lons = []
        wp_lats = []
        wp_depths = []
        
        for i in range(ep_data.unCntWaypoint):
            wp = ep_data.stWaypoints[i]
            if wp.bValid and (wp.dLatitude != 0 or wp.dLongitude != 0):
                wp_lons.append(wp.dLongitude)
                wp_lats.append(wp.dLatitude)
                wp_depths.append(-wp.fDepth)
        
        if wp_lons:
            self.ax.scatter(
                wp_lons, wp_lats, wp_depths,
                c='green', s=100, marker='o',
                label='Waypoints', zorder=10
            )
            all_lons.extend(wp_lons)
            all_lats.extend(wp_lats)
            all_depths.extend(wp_depths)
        
        # Launch point
        launch = ep_data.stLaunchPos
        if launch.dLatitude != 0 or launch.dLongitude != 0:
            self.ax.scatter(
                [launch.dLongitude],
                [launch.dLatitude],
                [-launch.fDepth],
                c='cyan', s=150, marker='s',
                label='Launch Point', zorder=20
            )
            all_lons.append(launch.dLongitude)
            all_lats.append(launch.dLatitude)
            all_depths.append(-launch.fDepth)
        
        # Drop point (target)
        drop = ep_data.stDropPos
        if drop.dLatitude != 0 or drop.dLongitude != 0:
            self.ax.scatter(
                [drop.dLongitude],
                [drop.dLatitude],
                [-drop.fDepth],
                c='red', s=200, marker='X',
                label='Drop Point', zorder=30
            )
            all_lons.append(drop.dLongitude)
            all_lats.append(drop.dLatitude)
            all_depths.append(-drop.fDepth)
        
        # Current missile position
        if ep_data.bValidMslPos:
            msl = ep_data.MslPos
            self.ax.scatter(
                [msl.dLongitude],
                [msl.dLatitude],
                [-msl.fDepth],
                c='orange', s=150, marker='D',
                label='Current Position', zorder=40
            )
            all_lons.append(msl.dLongitude)
            all_lats.append(msl.dLatitude)
            all_depths.append(-msl.fDepth)
        
        return all_lons, all_lats, all_depths
    
    def _plot_alm_asm(self, ep_data):
        """
        Plot ALM/ASM engagement plan
        Returns: (lons, lats, depths) for axis scaling
        """
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Trajectory
        traj_lons = []
        traj_lats = []
        traj_depths = []
        
        for i in range(ep_data.unCntTrajectory):
            traj = ep_data.stTrajectories[i]
            if traj.dLatitude != 0 or traj.dLongitude != 0:
                traj_lons.append(traj.dLongitude)
                traj_lats.append(traj.dLatitude)
                traj_depths.append(-traj.fDepth)
        
        if traj_lons:
            self.ax.plot(
                traj_lons, traj_lats, traj_depths,
                'b-', linewidth=2, label='Trajectory'
            )
            all_lons.extend(traj_lons)
            all_lats.extend(traj_lats)
            all_depths.extend(traj_depths)
        
        # Waypoints
        wp_lons = []
        wp_lats = []
        wp_depths = []
        
        for i in range(ep_data.unCntWaypoint):
            wp = ep_data.stWaypoints[i]
            if wp.dLatitude != 0 or wp.dLongitude != 0:
                wp_lons.append(wp.dLongitude)
                wp_lats.append(wp.dLatitude)
                wp_depths.append(-wp.fDepth)
        
        if wp_lons:
            self.ax.scatter(
                wp_lons, wp_lats, wp_depths,
                c='green', s=100, marker='o',
                label='Waypoints', zorder=10
            )
            all_lons.extend(wp_lons)
            all_lats.extend(wp_lats)
            all_depths.extend(wp_depths)
        
        # Turning points
        if hasattr(ep_data, 'unCntTurningpoints') and ep_data.unCntTurningpoints > 0:
            tp_lons = []
            tp_lats = []
            tp_depths = []
            
            for i in range(ep_data.unCntTurningpoints):
                tp = ep_data.stTurningpoints[i]
                if tp.dLatitude != 0 or tp.dLongitude != 0:
                    tp_lons.append(tp.dLongitude)
                    tp_lats.append(tp.dLatitude)
                    tp_depths.append(-tp.fDepth)
            
            if tp_lons:
                self.ax.scatter(
                    tp_lons, tp_lats, tp_depths,
                    c='purple', s=80, marker='v',
                    label='Turning Points', zorder=15
                )
                all_lons.extend(tp_lons)
                all_lats.extend(tp_lats)
                all_depths.extend(tp_depths)
        
        # Current missile position
        if ep_data.bValidMslPos:
            msl = ep_data.MslPos
            self.ax.scatter(
                [msl.dLongitude],
                [msl.dLatitude],
                [-msl.fDepth],
                c='orange', s=150, marker='D',
                label='Current Position', zorder=40
            )
            all_lons.append(msl.dLongitude)
            all_lats.append(msl.dLatitude)
            all_depths.append(-msl.fDepth)
        
        return all_lons, all_lats, all_depths
    
    def _plot_wgt(self, ep_data):
        """
        Plot WGT (Wire-Guided Torpedo) engagement plan
        Returns: (lons, lats, depths) for axis scaling
        """
        all_lons = []
        all_lats = []
        all_depths = []
        
        # WGT trajectory
        if hasattr(ep_data, 'CntTrajectoryWGT') and ep_data.CntTrajectoryWGT > 0:
            traj_lons = []
            traj_lats = []
            traj_depths = []
            
            for i in range(min(ep_data.CntTrajectoryWGT, 128)):
                traj = ep_data.stTrajectories_WGT[i]
                if traj.dLatitude != 0 or traj.dLongitude != 0:
                    traj_lons.append(traj.dLongitude)
                    traj_lats.append(traj.dLatitude)
                    traj_depths.append(-traj.fDepth)
            
            if traj_lons:
                self.ax.plot(
                    traj_lons, traj_lats, traj_depths,
                    'b-', linewidth=2, label='WGT Trajectory'
                )
                all_lons.extend(traj_lons)
                all_lats.extend(traj_lats)
                all_depths.extend(traj_depths)
        
        # Target trajectory
        if hasattr(ep_data, 'CntTrajectoryTGT') and ep_data.CntTrajectoryTGT > 0:
            tgt_lons = []
            tgt_lats = []
            tgt_depths = []
            
            for i in range(min(ep_data.CntTrajectoryTGT, 128)):
                traj = ep_data.stTrajectories_TGT[i]
                if traj.dLatitude != 0 or traj.dLongitude != 0:
                    tgt_lons.append(traj.dLongitude)
                    tgt_lats.append(traj.dLatitude)
                    tgt_depths.append(-traj.fDepth)
            
            if tgt_lons:
                self.ax.plot(
                    tgt_lons, tgt_lats, tgt_depths,
                    'r--', linewidth=2, label='Target Trajectory'
                )
                all_lons.extend(tgt_lons)
                all_lats.extend(tgt_lats)
                all_depths.extend(tgt_depths)
        
        # Hit point
        if ep_data.bHitPointFound:
            self.ax.scatter(
                [ep_data.dHit_Longitude],
                [ep_data.dHit_Latitude],
                [0],  # Assuming surface
                c='red', s=200, marker='X',
                label='Hit Point', zorder=30
            )
            all_lons.append(ep_data.dHit_Longitude)
            all_lats.append(ep_data.dHit_Latitude)
            all_depths.append(0)
        
        # Current torpedo position
        if ep_data.bValidTorpedoCurrentPosition:
            pos = ep_data.stTorpedoCurrentPosition
            self.ax.scatter(
                [pos.dLongitude],
                [pos.dLatitude],
                [-pos.fDepth],
                c='orange', s=150, marker='D',
                label='Current Position', zorder=40
            )
            all_lons.append(pos.dLongitude)
            all_lats.append(pos.dLatitude)
            all_depths.append(-pos.fDepth)
        
        return all_lons, all_lats, all_depths
    
    def _plot_aam(self, ep_data):
        """
        Plot AAM (Anti-Air Missile) engagement plan
        Returns: (lons, lats, depths) for axis scaling
        """
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Early scenario trajectory
        if hasattr(ep_data, 'Early_Traj'):
            early_lons = []
            early_lats = []
            early_alts = []
            
            for i in range(128):
                traj = ep_data.Early_Traj[i]
                if traj.dLatitude != 0 or traj.dLongitude != 0:
                    early_lons.append(traj.dLongitude)
                    early_lats.append(traj.dLatitude)
                    early_alts.append(traj.fAltitude)
            
            if early_lons:
                self.ax.plot(
                    early_lons, early_lats, early_alts,
                    'b-', linewidth=2, alpha=0.7, label='Early Scenario'
                )
                all_lons.extend(early_lons)
                all_lats.extend(early_lats)
                all_depths.extend(early_alts)
        
        # Short scenario trajectory
        if hasattr(ep_data, 'Short_Traj'):
            short_lons = []
            short_lats = []
            short_alts = []
            
            for i in range(128):
                traj = ep_data.Short_Traj[i]
                if traj.dLatitude != 0 or traj.dLongitude != 0:
                    short_lons.append(traj.dLongitude)
                    short_lats.append(traj.dLatitude)
                    short_alts.append(traj.fAltitude)
            
            if short_lons:
                self.ax.plot(
                    short_lons, short_lats, short_alts,
                    'g-', linewidth=2, alpha=0.7, label='Short Scenario'
                )
                all_lons.extend(short_lons)
                all_lats.extend(short_lats)
                all_depths.extend(short_alts)
        
        # Late scenario trajectory
        if hasattr(ep_data, 'Late_Traj'):
            late_lons = []
            late_lats = []
            late_alts = []
            
            for i in range(128):
                traj = ep_data.Late_Traj[i]
                if traj.dLatitude != 0 or traj.dLongitude != 0:
                    late_lons.append(traj.dLongitude)
                    late_lats.append(traj.dLatitude)
                    late_alts.append(traj.fAltitude)
            
            if late_lons:
                self.ax.plot(
                    late_lons, late_lats, late_alts,
                    'r-', linewidth=2, alpha=0.7, label='Late Scenario'
                )
                all_lons.extend(late_lons)
                all_lats.extend(late_lats)
                all_depths.extend(late_alts)
        
        # Target position
        if hasattr(ep_data, 'Target_Lat') and (ep_data.Target_Lat != 0 or ep_data.Target_Lon != 0):
            self.ax.scatter(
                [ep_data.Target_Lon],
                [ep_data.Target_Lat],
                [ep_data.Target_Alt],
                c='red', s=200, marker='X',
                label='Target', zorder=50
            )
            all_lons.append(ep_data.Target_Lon)
            all_lats.append(ep_data.Target_Lat)
            all_depths.append(ep_data.Target_Alt)
        
        # Current missile position
        if hasattr(ep_data, 'bValidMslPos') and ep_data.bValidMslPos:
            self.ax.scatter(
                [ep_data.MslPos.dLongitude],
                [ep_data.MslPos.dLatitude],
                [ep_data.MslPos.fAltitude],
                c='orange', s=150, marker='D',
                label='Current Position', zorder=60
            )
            all_lons.append(ep_data.MslPos.dLongitude)
            all_lats.append(ep_data.MslPos.dLatitude)
            all_depths.append(ep_data.MslPos.fAltitude)
        
        return all_lons, all_lats, all_depths
    
    def _set_axis_limits(self, all_lons, all_lats, all_depths):
        """Set axis limits based on data range with padding"""
        if not all_lons or not all_lats or not all_depths:
            return
        
        # Calculate ranges
        lon_min, lon_max = min(all_lons), max(all_lons)
        lat_min, lat_max = min(all_lats), max(all_lats)
        depth_min, depth_max = min(all_depths), max(all_depths)
        
        # Add padding (10%)
        lon_range = lon_max - lon_min
        lat_range = lat_max - lat_min
        depth_range = depth_max - depth_min
        
        padding_lon = lon_range * 0.1 if lon_range > 0 else 0.01
        padding_lat = lat_range * 0.1 if lat_range > 0 else 0.01
        padding_depth = depth_range * 0.1 if depth_range > 0 else 10
        
        # Set limits
        self.ax.set_xlim(lon_min - padding_lon, lon_max + padding_lon)
        self.ax.set_ylim(lat_min - padding_lat, lat_max + padding_lat)
        self.ax.set_zlim(depth_min - padding_depth, depth_max + padding_depth)
