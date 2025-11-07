# -*- coding: utf-8 -*-
"""
EngagementPlanViewer.py
교전계획 전시 시스템
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
    NAVINF_SHIP_NAVIGATION_INFO
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


# =============================================================================
# Level 1: Engagement Plan Viewer (Tube Selection)
# =============================================================================

class EngagementPlanViewer(tk.Toplevel):
    """Tube selection window with layout: [6 4 3 5] [2 1]"""
    
    def __init__(self, parent, main_gui):
        super().__init__(parent)
        self.title("Engagement Plan Viewer - Select Tube")
        self.geometry("600x400")
        
        self.main_gui = main_gui  # Reference to main GUI for PA info
        self.plot_windows = {}  # tube_num -> EPPlotWindow
        
        self._setup_ui()
        self._start_status_update()
    
    def _setup_ui(self):
        """Setup UI with tube button layout"""
        # Title
        title_label = tk.Label(
            self, 
            text="Select Launch Tube", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # Main frame for tube buttons
        main_frame = tk.Frame(self)
        main_frame.pack(expand=True)
        
        # Top row: 6, 4, 3, 5
        top_frame = tk.Frame(main_frame)
        top_frame.pack(pady=10)
        
        self.tube_buttons = {}
        self.tube_status_labels = {}
        
        top_tubes = [6, 4, 3, 5]
        for tube_num in top_tubes:
            btn_frame = tk.Frame(top_frame)
            btn_frame.pack(side=tk.LEFT, padx=10)
            
            btn = tk.Button(
                btn_frame,
                text=f"Tube {tube_num}",
                command=lambda t=tube_num: self._open_plot_window(t),
                width=12,
                height=3,
                font=("Arial", 12, "bold"),
                bg="lightblue"
            )
            btn.pack()
            
            status_label = tk.Label(
                btn_frame,
                text="No Data",
                font=("Arial", 8),
                fg="gray"
            )
            status_label.pack()
            
            self.tube_buttons[tube_num] = btn
            self.tube_status_labels[tube_num] = status_label
        
        # Bottom row: 2, 1
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(pady=10)
        
        # Add spacers for alignment
        tk.Label(bottom_frame, text="", width=12).pack(side=tk.LEFT)
        
        bottom_tubes = [2, 1]
        for tube_num in bottom_tubes:
            btn_frame = tk.Frame(bottom_frame)
            btn_frame.pack(side=tk.LEFT, padx=10)
            
            btn = tk.Button(
                btn_frame,
                text=f"Tube {tube_num}",
                command=lambda t=tube_num: self._open_plot_window(t),
                width=12,
                height=3,
                font=("Arial", 12, "bold"),
                bg="lightblue"
            )
            btn.pack()
            
            status_label = tk.Label(
                btn_frame,
                text="No Data",
                font=("Arial", 8),
                fg="gray"
            )
            status_label.pack()
            
            self.tube_buttons[tube_num] = btn
            self.tube_status_labels[tube_num] = status_label
        
        # Close button
        tk.Button(
            self,
            text="Close",
            command=self.destroy,
            width=15
        ).pack(pady=20)
    
    def _start_status_update(self):
        """Start periodic status update"""
        self._update_tube_status()
    
    def _update_tube_status(self):
        """Update tube status labels"""
        if not self.winfo_exists():
            return
        
        for tube_num in [1, 2, 3, 4, 5, 6]:
            wpn_type, ep_data = get_tube_ep_data(tube_num)
            
            if wpn_type:
                self.tube_status_labels[tube_num].config(
                    text=f"{wpn_type} Active",
                    fg="green"
                )
                self.tube_buttons[tube_num].config(bg="lightgreen")
            else:
                self.tube_status_labels[tube_num].config(
                    text="No Data",
                    fg="gray"
                )
                self.tube_buttons[tube_num].config(bg="lightgray")
        
        # Schedule next update
        self.after(1000, self._update_tube_status)
    
    def _open_plot_window(self, tube_num):
        """Open plot window for selected tube"""
        wpn_type, ep_data = get_tube_ep_data(tube_num)
        
        if not wpn_type:
            messagebox.showinfo(
                "Info",
                f"No engagement plan data available for Tube {tube_num}"
            )
            return
        
        # Close existing window if open
        if tube_num in self.plot_windows:
            try:
                self.plot_windows[tube_num].destroy()
            except:
                pass
        
        # Open new plot window with reference to main GUI
        plot_window = EPPlotWindow(self, tube_num, wpn_type, self.main_gui)
        self.plot_windows[tube_num] = plot_window


# =============================================================================
# Level 2: 3D Plot Window
# =============================================================================

class EPPlotWindow(tk.Toplevel):
    """3D Engagement Plan Plot Window"""
    
    def __init__(self, parent, tube_num, wpn_type, main_gui):
        super().__init__(parent)
        self.title(f"Tube {tube_num} - {wpn_type} Engagement Plan")
        self.geometry("1200x800")
        
        self.tube_num = tube_num
        self.wpn_type = wpn_type
        self.main_gui = main_gui  # Reference to main GUI for real-time PA info
        self.is_running = True
        
        self._setup_ui()
        self._start_plot_update()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """Setup UI with 3D plot and info panel"""
        # Info panel (top)
        info_frame = tk.LabelFrame(self, text="Status Information", padx=10, pady=5)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        self.info_labels = {}
        info_items = [
            ("Weapon Type:", "wpn_type"),
            ("Next WP Index:", "next_wp"),
            ("Time to Next WP:", "time_to_wp"),
            ("Total Time:", "total_time"),
            ("Remaining Time:", "remaining_time"),
            ("Missile Valid:", "msl_valid"),
        ]
        
        for i, (label_text, key) in enumerate(info_items):
            row = i // 3
            col = (i % 3) * 2
            
            tk.Label(info_frame, text=label_text, font=("Arial", 9, "bold")).grid(
                row=row, column=col, sticky="w", padx=5, pady=2
            )
            value_label = tk.Label(info_frame, text="-", font=("Arial", 9))
            value_label.grid(row=row, column=col+1, sticky="w", padx=5, pady=2)
            self.info_labels[key] = value_label
        
        self.info_labels["wpn_type"].config(text=self.wpn_type)
        
        # 3D Plot (center)
        plot_frame = tk.Frame(self)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.fig = plt.Figure(figsize=(10, 6))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Control panel (bottom)
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.BOTTOM, pady=10)
        
        self.auto_rotate_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            control_frame,
            text="Auto Rotate",
            variable=self.auto_rotate_var
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            control_frame,
            text="Reset View",
            command=self._reset_view
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Close",
            command=self._on_closing
        ).pack(side=tk.LEFT, padx=5)
        
        # Initial view angle
        self.view_azim = -60
        self.view_elev = 30
    
    def _start_plot_update(self):
        """Start periodic plot update"""
        self._update_plot()
    
    def _update_plot(self):
        """Update plot with latest data"""
        if not self.is_running or not self.winfo_exists():
            return
        
        wpn_type, ep_data = get_tube_ep_data(self.tube_num)
        
        if wpn_type and ep_data:
            self._plot_engagement_plan(wpn_type, ep_data)
            self._update_info_panel(wpn_type, ep_data)
        else:
            self.ax.clear()
            self.ax.text(0.5, 0.5, 0.5, "No Data", 
                        ha='center', va='center', fontsize=20, color='red')
        
        self.canvas.draw()
        
        # Auto rotate
        if self.auto_rotate_var.get():
            self.view_azim = (self.view_azim + 2) % 360
            self.ax.view_init(elev=self.view_elev, azim=self.view_azim)
        
        # Schedule next update (1 second)
        self.after(1000, self._update_plot)
    
    def _plot_engagement_plan(self, wpn_type, ep_data):
        """Plot engagement plan based on weapon type"""
        self.ax.clear()
        
        # Collect all points for range calculation
        all_lons = []
        all_lats = []
        all_depths = []
        
        if wpn_type == 'M_MINE':
            all_lons, all_lats, all_depths = self._plot_m_mine(ep_data)
        elif wpn_type == 'ALM_ASM':
            all_lons, all_lats, all_depths = self._plot_alm_asm(ep_data)
        elif wpn_type == 'WGT':
            all_lons, all_lats, all_depths = self._plot_wgt(ep_data)
        elif wpn_type == 'AAM':
            all_lons, all_lats, all_depths = self._plot_aam(ep_data)
        
        # Plot ownship position
        ownship_lon, ownship_lat, ownship_depth = self._plot_ownship()
        if ownship_lon is not None:
            all_lons.append(ownship_lon)
            all_lats.append(ownship_lat)
            all_depths.append(ownship_depth)
        
        # Plot prohibited areas (real-time from main GUI)
        self._plot_prohibited_areas(all_lons, all_lats)
        
        # Set labels
        self.ax.set_xlabel('Longitude (deg)', fontsize=10)
        self.ax.set_ylabel('Latitude (deg)', fontsize=10)
        self.ax.set_zlabel('Depth/Altitude (m)', fontsize=10)
        self.ax.view_init(elev=self.view_elev, azim=self.view_azim)
        
        # Set axis limits based on data range
        self._set_axis_limits(all_lons, all_lats, all_depths)

    def _plot_ownship(self):
        """Plot ownship position (simulator data has priority)"""
        # 1. Try simulator ownship info first (from main GUI)
        if hasattr(self.main_gui, 'ownship_info_data') and self.main_gui.ownship_info_data:
            ownship_info = self.main_gui.ownship_info_data
            source = "Simulator"
        else:
            # 2. Fall back to external subscription
            ownship_info = get_ownship_info()
            source = "External"
        
        if not ownship_info:
            return None, None, None
        
        try:
            lat = ownship_info.stShipMovementInfo.dShipLatitude
            lon = ownship_info.stShipMovementInfo.dShipLongitude
            depth = -ownship_info.stShipMovementInfo.fShipDepth
            
            if lat != 0 or lon != 0:
                # Different color for simulator vs external
                color = 'cyan' if source == "Simulator" else 'lightblue'
                
                self.ax.scatter(
                    [lon], [lat], [depth],
                    c=color, s=300, marker='s', 
                    edgecolors='black', linewidths=2,
                    label=f'Ownship ({source})', zorder=10
                )
                return lon, lat, depth
        except Exception as e:
            print(f"Error plotting ownship: {e}")
        
        return None, None, None
  
    def _plot_m_mine(self, ep_data):
        """Plot M_MINE engagement plan"""
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Extract trajectory
        traj_lats = []
        traj_lons = []
        traj_depths = []
        
        for i in range(ep_data.unCntTrajectory):
            traj = ep_data.stTrajectories[i]
            if traj.dLatitude != 0 or traj.dLongitude != 0:
                traj_lats.append(traj.dLatitude)
                traj_lons.append(traj.dLongitude)
                traj_depths.append(-traj.fDepth)
        
        if traj_lats:
            self.ax.plot(traj_lons, traj_lats, traj_depths, 
                        'b-', linewidth=2, label='Trajectory')
            all_lons.extend(traj_lons)
            all_lats.extend(traj_lats)
            all_depths.extend(traj_depths)
        
        # Waypoints
        wp_lats = []
        wp_lons = []
        wp_depths = []
        
        for i in range(ep_data.unCntWaypoint):
            wp = ep_data.stWaypoints[i]
            if wp.bValid:
                wp_lats.append(wp.dLatitude)
                wp_lons.append(wp.dLongitude)
                wp_depths.append(-wp.fDepth)
        
        if wp_lats:
            self.ax.scatter(wp_lons, wp_lats, wp_depths,
                           c='green', s=100, marker='o', label='Waypoints')
            all_lons.extend(wp_lons)
            all_lats.extend(wp_lats)
            all_depths.extend(wp_depths)
        
        # Launch position
        if ep_data.stLaunchPos.dLatitude != 0:
            self.ax.scatter(
                [ep_data.stLaunchPos.dLongitude],
                [ep_data.stLaunchPos.dLatitude],
                [-ep_data.stLaunchPos.fDepth],
                c='blue', s=200, marker='^', label='Launch Point'
            )
            all_lons.append(ep_data.stLaunchPos.dLongitude)
            all_lats.append(ep_data.stLaunchPos.dLatitude)
            all_depths.append(-ep_data.stLaunchPos.fDepth)
        
        # Drop position (target)
        if ep_data.stDropPos.dLatitude != 0:
            self.ax.scatter(
                [ep_data.stDropPos.dLongitude],
                [ep_data.stDropPos.dLatitude],
                [-ep_data.stDropPos.fDepth],
                c='red', s=200, marker='*', label='Drop Point'
            )
            all_lons.append(ep_data.stDropPos.dLongitude)
            all_lats.append(ep_data.stDropPos.dLatitude)
            all_depths.append(-ep_data.stDropPos.fDepth)
        
        # Current missile position
        if ep_data.bValidMslPos:
            self.ax.scatter(
                [ep_data.MslPos.dLongitude],
                [ep_data.MslPos.dLatitude],
                [-ep_data.MslPos.fDepth],
                c='orange', s=150, marker='D', label='Current Position'
            )
            all_lons.append(ep_data.MslPos.dLongitude)
            all_lats.append(ep_data.MslPos.dLatitude)
            all_depths.append(-ep_data.MslPos.fDepth)
        
        self.ax.legend()
        self.ax.set_title(f'Mine Engagement Plan - Tube {self.tube_num}')
        
        return all_lons, all_lats, all_depths
    
    def _plot_alm_asm(self, ep_data):
        """Plot ALM/ASM engagement plan"""
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Trajectory
        traj_lats = []
        traj_lons = []
        traj_alts = []
        
        for i in range(ep_data.unCntTrajectory):
            traj = ep_data.stTrajectories[i]
            if traj.dLatitude != 0 or traj.dLongitude != 0:
                traj_lats.append(traj.dLatitude)
                traj_lons.append(traj.dLongitude)
                traj_alts.append(traj.fDepth)
        
        if traj_lats:
            self.ax.plot(traj_lons, traj_lats, traj_alts,
                        'b-', linewidth=2, label='Trajectory')
            all_lons.extend(traj_lons)
            all_lats.extend(traj_lats)
            all_depths.extend(traj_alts)
        
        # Waypoints
        for i in range(ep_data.unCntWaypoint):
            wp = ep_data.stWaypoints[i]
            if wp.dLatitude != 0 or wp.dLongitude != 0:
                self.ax.scatter([wp.dLongitude], [wp.dLatitude], [wp.fDepth],
                               c='green', s=100, marker='o')
                all_lons.append(wp.dLongitude)
                all_lats.append(wp.dLatitude)
                all_depths.append(wp.fDepth)
        
        # Turning points
        for i in range(ep_data.unCntTurningpoints):
            tp = ep_data.stTurningpoints[i]
            if tp.dLatitude != 0 or tp.dLongitude != 0:
                self.ax.scatter([tp.dLongitude], [tp.dLatitude], [tp.fDepth],
                               c='purple', s=80, marker='s')
                all_lons.append(tp.dLongitude)
                all_lats.append(tp.dLatitude)
                all_depths.append(tp.fDepth)
        
        # Current missile position
        if ep_data.bValidMslPos:
            self.ax.scatter(
                [ep_data.MslPos.dLongitude],
                [ep_data.MslPos.dLatitude],
                [ep_data.MslPos.fDepth],
                c='orange', s=150, marker='D', label='Current Position'
            )
            all_lons.append(ep_data.MslPos.dLongitude)
            all_lats.append(ep_data.MslPos.dLatitude)
            all_depths.append(ep_data.MslPos.fDepth)
        
        self.ax.legend()
        self.ax.set_title(f'Missile Engagement Plan - Tube {self.tube_num}')
        
        return all_lons, all_lats, all_depths
    
    def _plot_wgt(self, ep_data):
        """Plot WGT (Torpedo) engagement plan"""
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Torpedo trajectory
        for i in range(ep_data.CntTrajectoryWGT):
            traj = ep_data.stTrajectories_WGT[i]
            if traj.dLatitude != 0 or traj.dLongitude != 0:
                all_lons.append(traj.dLongitude)
                all_lats.append(traj.dLatitude)
                all_depths.append(-traj.fDepth)
        
        if all_lons:
            self.ax.plot(all_lons, all_lats, all_depths,
                        'b-', linewidth=2, label='Torpedo Trajectory')
        
        # Target trajectory
        tgt_lons = []
        tgt_lats = []
        tgt_depths = []
        
        for i in range(ep_data.CntTrajectoryTGT):
            traj = ep_data.stTrajectories_TGT[i]
            if traj.dLatitude != 0 or traj.dLongitude != 0:
                tgt_lats.append(traj.dLatitude)
                tgt_lons.append(traj.dLongitude)
                tgt_depths.append(-traj.fDepth)
        
        if tgt_lats:
            self.ax.plot(tgt_lons, tgt_lats, tgt_depths,
                        'r--', linewidth=2, label='Target Trajectory')
            all_lons.extend(tgt_lons)
            all_lats.extend(tgt_lats)
            all_depths.extend(tgt_depths)
        
        # Hit point
        if ep_data.bHitPointFound:
            self.ax.scatter(
                [ep_data.dHit_Longitude],
                [ep_data.dHit_Latitude],
                [0],
                c='red', s=200, marker='*', label='Hit Point'
            )
            all_lons.append(ep_data.dHit_Longitude)
            all_lats.append(ep_data.dHit_Latitude)
            all_depths.append(0)
        
        # Current torpedo position
        if ep_data.bValidTorpedoCurrentPosition:
            self.ax.scatter(
                [ep_data.stTorpedoCurrentPosition.dLongitude],
                [ep_data.stTorpedoCurrentPosition.dLatitude],
                [-ep_data.stTorpedoCurrentPosition.fDepth],
                c='orange', s=150, marker='D', label='Current Position'
            )
            all_lons.append(ep_data.stTorpedoCurrentPosition.dLongitude)
            all_lats.append(ep_data.stTorpedoCurrentPosition.dLatitude)
            all_depths.append(-ep_data.stTorpedoCurrentPosition.fDepth)
        
        self.ax.legend()
        self.ax.set_title(f'Torpedo Engagement Plan - Tube {self.tube_num}')
        
        return all_lons, all_lats, all_depths
    
    def _plot_aam(self, ep_data):
        """Plot AAM engagement plan (3 scenarios)"""
        all_lons = []
        all_lats = []
        all_depths = []
        
        # Early scenario
        for i in range(128):
            traj = ep_data.Early_Traj[i]
            if traj.dLatitude != 0 or traj.dLongitude != 0:
                all_lons.append(traj.dLongitude)
                all_lats.append(traj.dLatitude)
                all_depths.append(traj.fAltitude)
        
        if all_lons:
            self.ax.plot(all_lons, all_lats, all_depths,
                        'b-', linewidth=2, alpha=0.6, label='Early Scenario')
        
        # Short, Late, Target scenarios (similar patterns)
        # ... (생략)
        
        self.ax.legend()
        self.ax.set_title(f'AAM Engagement Plan - Tube {self.tube_num}')
        
        return all_lons, all_lats, all_depths
    
    def _plot_prohibited_areas(self, all_lons, all_lats):
        """Plot prohibited areas (real-time from main GUI)"""
        # Get PA info from main GUI in real-time
        pa_info = None
        if hasattr(self.main_gui, 'pa_info_data'):
            pa_info = self.main_gui.pa_info_data
        
        if not pa_info or pa_info.nCountPA == 0:
            return
        
        for i in range(pa_info.nCountPA):
            pa = pa_info.stPaPoint[i]
            
            # Draw circle at sea level (z=0)
            circle_points = 50
            theta = np.linspace(0, 2*np.pi, circle_points)
            
            # Approximate radius in degrees
            radius_deg = pa.dRadius / 111000  # Convert meters to degrees
            
            circle_lons = pa.dLongitude + radius_deg * np.cos(theta)
            circle_lats = pa.dLatitude + radius_deg * np.sin(theta)
            circle_z = np.zeros(circle_points)
            
            self.ax.plot(circle_lons, circle_lats, circle_z,
                        'r--', linewidth=2, alpha=0.8, 
                        label='Prohibited Area' if i == 0 else '')
            
            # Add to all points for range calculation
            all_lons.extend(circle_lons.tolist())
            all_lats.extend(circle_lats.tolist())
    
    def _set_axis_limits(self, all_lons, all_lats, all_depths):
        """Set axis limits based on data range with margin"""
        if not all_lons or not all_lats:
            return
        
        # Calculate ranges
        lon_min, lon_max = min(all_lons), max(all_lons)
        lat_min, lat_max = min(all_lats), max(all_lats)
        
        # Add 20% margin
        lon_range = lon_max - lon_min
        lat_range = lat_max - lat_min
        
        margin_lon = max(lon_range * 0.2, 0.01)  # Minimum 0.01 degree
        margin_lat = max(lat_range * 0.2, 0.01)
        
        self.ax.set_xlim(lon_min - margin_lon, lon_max + margin_lon)
        self.ax.set_ylim(lat_min - margin_lat, lat_max + margin_lat)
        
        # Depth/altitude
        if all_depths:
            depth_min, depth_max = min(all_depths), max(all_depths)
            depth_range = depth_max - depth_min
            margin_depth = max(depth_range * 0.2, 10)  # Minimum 10 meters
            
            self.ax.set_zlim(depth_min - margin_depth, depth_max + margin_depth)
        
        # Equal aspect ratio for x and y (lat/lon)
        try:
            lon_center = (lon_min + lon_max) / 2
            lat_center = (lat_min + lat_max) / 2
            max_range = max(lon_range, lat_range) * 0.6
            
            self.ax.set_xlim(lon_center - max_range, lon_center + max_range)
            self.ax.set_ylim(lat_center - max_range, lat_center + max_range)
        except:
            pass
    
    def _update_info_panel(self, wpn_type, ep_data):
        """Update information panel"""
        try:
            if wpn_type == 'M_MINE':
                self.info_labels["next_wp"].config(text=str(ep_data.numberOfNextWP))
                self.info_labels["time_to_wp"].config(text=f"{ep_data.timeToNextWP:.1f} s")
                self.info_labels["total_time"].config(text=f"{ep_data.fEstimatedDrivingTime:.1f} s")
                self.info_labels["remaining_time"].config(text=f"{ep_data.fRemainingTime:.1f} s")
                self.info_labels["msl_valid"].config(
                    text="Yes" if ep_data.bValidMslPos else "No"
                )
            
            elif wpn_type == 'ALM_ASM':
                self.info_labels["next_wp"].config(text=str(ep_data.numberOfNextWP))
                self.info_labels["time_to_wp"].config(text=f"{ep_data.timeToNextWP:.1f} s")
                self.info_labels["total_time"].config(text="-")
                self.info_labels["remaining_time"].config(text="-")
                self.info_labels["msl_valid"].config(
                    text="Yes" if ep_data.bValidMslPos else "No"
                )
            
            elif wpn_type == 'WGT':
                self.info_labels["next_wp"].config(text="-")
                self.info_labels["time_to_wp"].config(text="-")
                
                if ep_data.bHitPointFound:
                    self.info_labels["total_time"].config(text=f"{ep_data.dHit_TimeDiff:.1f} s")
                else:
                    self.info_labels["total_time"].config(text="-")
                
                self.info_labels["remaining_time"].config(text="-")
                self.info_labels["msl_valid"].config(
                    text="Yes" if ep_data.bValidTorpedoCurrentPosition else "No"
                )
            
            elif wpn_type == 'AAM':
                self.info_labels["next_wp"].config(text="-")
                self.info_labels["time_to_wp"].config(text="-")
                self.info_labels["total_time"].config(
                    text=f"E:{ep_data.Early_RunTime:.1f} S:{ep_data.Short_RunTime:.1f} L:{ep_data.Late_RunTime:.1f}"
                )
                self.info_labels["remaining_time"].config(
                    text=f"E:{ep_data.Early_LaunchTimeLeft:.1f} S:{ep_data.Short_LaunchTimeLeft:.1f} L:{ep_data.Late_LaunchTimeLeft:.1f}"
                )
                self.info_labels["msl_valid"].config(
                    text="Yes" if ep_data.bValidMslPos else "No"
                )
        
        except Exception as e:
            print(f"Error updating info panel: {e}")
    
    def _reset_view(self):
        """Reset view angle"""
        self.view_azim = -60
        self.view_elev = 30
        self.ax.view_init(elev=self.view_elev, azim=self.view_azim)
        self.canvas.draw()
    
    def _on_closing(self):
        """Handle window closing"""
        self.is_running = False
        self.destroy()
