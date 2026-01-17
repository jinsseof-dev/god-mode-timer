import tkinter as tk
from tkinter import messagebox
from utils import play_sound, log_godmode, show_toast, play_tick_sound
from taskbar import WindowsTaskbar
from common import resource_path, get_user_data_path
from settings_window import open_settings_window
from stats_window import open_stats_window
import time
import math
import sys
import ctypes
import re
from PIL import Image, ImageDraw, ImageFont, ImageTk
import json
import os
import pystray
from pystray import MenuItem as item
import threading

# 윈도우 High DPI 설정 (선명하게 보이기 위함)
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

class GodModeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("God-Mode Timer")
        self.root.geometry("300x350")
        self.root.resizable(True, True)
        self.root.minsize(300, 350)
        

        # 윈도우 작업 표시줄 진행률 초기화
        self.taskbar = WindowsTaskbar(root)
        
        # 윈도우 아이콘 설정
        self.set_window_icon()

        # 시스템 트레이 아이콘 설정
        self.init_tray_icon()

        # 윈도우 닫기 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 최소화 이벤트 처리 (트레이로 숨기기)
        self.root.bind("<Unmap>", self.minimize_to_tray)

        # 윈도우 자석 효과 (Snap to Edge)
        self.root.bind("<Configure>", self.snap_to_edge)

        # 상태 변수
        self.is_running = False
        self.setting_always_on_top = True
        self.setting_auto_start = False
        self.setting_sound = True
        self.setting_work_min = 25
        self.setting_short_break_min = 5
        self.setting_long_break_min = 15
        self.setting_long_break_interval = 4
        self.setting_show_task_input = False
        self.is_mini_mode = False
        self.normal_geometry = "300x350"
        
        # 설정 파일 로드
        self.load_settings()
        
        # 테마 색상 정의 및 적용
        self.update_theme_colors()
        
        self.root.attributes('-topmost', self.setting_always_on_top)
        self.root.configure(bg=self.colors["bg"])
        
        self.work_time = self.setting_work_min * 60
        self.break_time = self.setting_short_break_min * 60
        self.current_time = self.work_time
        self.godmode_count = 0
        self.mode = "work"  # 'work' or 'break'

        # 타이머 표시 (도형)
        self.canvas = tk.Canvas(root, bg=self.colors["bg"], highlightthickness=0)
        self.canvas.pack(pady=0, expand=True, fill=tk.BOTH)

        self.draw_timer()
        self.canvas.bind("<Configure>", lambda e: self.draw_timer())
        self.canvas.bind("<Button-1>", self.handle_mouse_input)
        self.canvas.bind("<B1-Motion>", self.handle_mouse_input)
        
        # 마우스 커서 변경
        self.canvas.bind("<Enter>", lambda e: self.root.config(cursor="hand2"))
        self.canvas.bind("<Leave>", lambda e: self.root.config(cursor=""))

        # 보조 버튼 프레임 (통계, 설정, 미니모드) - 하단 배치
        self.btn_frame = tk.Frame(root, bg=self.colors["bg"])
        self.btn_frame.pack(pady=(0, 15))

        self.start_button = tk.Button(self.btn_frame, text="▶", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["start_btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.toggle_timer)
        self.start_button.pack(side=tk.LEFT, padx=10)
        self.start_button.bind("<Enter>", lambda e: self.start_button.config(bg=self.colors["start_btn_hover"]))
        self.start_button.bind("<Leave>", lambda e: self.update_start_button_color())

        self.stats_button = tk.Button(self.btn_frame, text="📊", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.open_stats)
        self.stats_button.pack(side=tk.LEFT, padx=10)
        self.stats_button.bind("<Enter>", lambda e: self.stats_button.config(bg=self.colors["btn_hover"]))
        self.stats_button.bind("<Leave>", lambda e: self.stats_button.config(bg=self.colors["btn_bg"]))

        self.settings_button = tk.Button(self.btn_frame, text="⚙", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=10)
        self.settings_button.bind("<Enter>", lambda e: self.settings_button.config(bg=self.colors["btn_hover"]) if self.settings_button['state'] != tk.DISABLED else None)
        self.settings_button.bind("<Leave>", lambda e: self.settings_button.config(bg=self.colors["btn_bg"]) if self.settings_button['state'] != tk.DISABLED else None)

        self.mini_button = tk.Button(self.btn_frame, text="🗖", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.toggle_mini_mode)
        self.mini_button.pack(side=tk.LEFT, padx=10)
        self.mini_button.bind("<Enter>", lambda e: self.mini_button.config(bg=self.colors["btn_hover"]))
        self.mini_button.bind("<Leave>", lambda e: self.mini_button.config(bg=self.colors["btn_bg"]))

        # 아이콘 이미지 생성
        self.icon_play = self.create_button_icon("play", self.colors["icon_color"], size=(24, 24))
        self.icon_stop = self.create_button_icon("stop", "#FF5252", size=(24, 24))
        self.icon_settings = self.create_button_icon("settings", self.colors["icon_color"])
        self.icon_settings_disabled = self.create_button_icon("settings", "#CCCCCC")
        self.icon_stats = self.create_button_icon("stats", self.colors["icon_color"])
        self.icon_mini = self.create_button_icon("mini", self.colors["icon_color"])
        
        # 버튼에 이미지 적용 (초기 상태)
        self.start_button.config(image=self.icon_play, text="", width=50, height=40)
        self.settings_button.config(image=self.icon_settings, text="", width=50, height=40)
        self.stats_button.config(image=self.icon_stats, text="", width=50, height=40)
        self.mini_button.config(image=self.icon_mini, text="", width=50, height=40)

        # 할 일 입력 프레임 (Task Input)
        self.task_frame = tk.Frame(root, bg=self.colors["bg"])
        
        self.task_var = tk.StringVar()
        self.task_placeholder = "지금 할 일 입력..."
        
        self.task_entry = tk.Entry(self.task_frame, textvariable=self.task_var, font=("Helvetica", 10), bg=self.colors["btn_bg"], fg=self.colors["fg_sub"], bd=0, justify="center")
        self.task_entry.pack(fill=tk.X, ipady=6)
        self.task_entry.insert(0, self.task_placeholder)
        
        self.task_entry.bind("<FocusIn>", self.on_task_focus_in)
        self.task_entry.bind("<FocusOut>", self.on_task_focus_out)
        self.task_entry.bind("<Return>", self.on_task_return)

        self.tk_image = None
        
        # 설정에 따라 할 일 입력창 표시 여부 결정
        self.update_task_input_visibility()

    def set_window_icon(self):
        # 윈도우 아이콘 동적 생성 (황금 번개 - 갓생 모드)
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 배경 원 (다크 그레이)
        draw.ellipse((2, 2, 62, 62), fill="#333333", outline="#555555")
        
        # Lightning Bolt Points (Zigzag shape)
        points = [(36, 4), (20, 34), (32, 34), (16, 60), (48, 26), (36, 26)]
        draw.polygon(points, fill="#FFD700", outline="#B8860B", width=2)
        
        self.tk_icon = ImageTk.PhotoImage(image)
        self.root.iconphoto(True, self.tk_icon)

    def init_tray_icon(self):
        # 트레이 아이콘용 이미지 생성
        image = self.create_tray_image()
        
        # 메뉴 정의
        menu = (
            item('열기', self.show_window_from_tray, default=True),
            item('종료', self.quit_app_from_tray)
        )
        
        self.tray_icon = pystray.Icon("GodModeTimer", image, "God-Mode Timer", menu)
        
        # 별도 스레드에서 실행 (Tkinter 메인루프와 충돌 방지)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def create_tray_image(self):
        # 64x64 아이콘 생성 (set_window_icon 로직 재사용)
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 배경 원 (다크 그레이)
        draw.ellipse((2, 2, 62, 62), fill="#333333", outline="#555555")
        
        # Lightning Bolt Points (Zigzag shape)
        points = [(36, 4), (20, 34), (32, 34), (16, 60), (48, 26), (36, 26)]
        draw.polygon(points, fill="#FFD700", outline="#B8860B", width=2)
        
        return image

    def show_window_from_tray(self, icon=None, item=None):
        self.root.after(0, self._show_window_safe)

    def _show_window_safe(self):
        self.root.deiconify()
        self.root.attributes('-topmost', self.setting_always_on_top)
        self.root.lift()
        self.root.focus_force()

    def quit_app_from_tray(self, icon=None, item=None):
        self.tray_icon.stop()
        self.root.after(0, self._quit_app_safe)

    def _quit_app_safe(self):
        self.save_settings_to_file()
        self.root.destroy()

    def create_button_icon(self, shape, color, size=(24, 24)):
        # 고품질 렌더링을 위한 슈퍼샘플링
        scale = 4 
        w, h = size[0] * scale, size[1] * scale
        image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        if shape == "play":
            # 삼각형 (오른쪽 방향)
            draw.polygon([(w*0.25, h*0.2), (w*0.25, h*0.8), (w*0.85, h*0.5)], fill=color)
        elif shape == "stop":
            # 정지(Stop) 아이콘 - 사각형
            draw.rectangle([(w*0.25, h*0.25), (w*0.75, h*0.75)], fill=color)
        elif shape == "settings":
            # 톱니바퀴 아이콘 (Solid)
            cx, cy = w/2, h/2
            r_body = w * 0.28
            r_tooth_start = w * 0.25
            r_tooth_end = w * 0.42
            tooth_width = w * 0.14
            
            # Draw teeth
            for i in range(8):
                angle = math.radians(i * 45)
                x0 = cx + r_tooth_start * math.cos(angle)
                y0 = cy + r_tooth_start * math.sin(angle)
                x1 = cx + r_tooth_end * math.cos(angle)
                y1 = cy + r_tooth_end * math.sin(angle)
                draw.line([(x0, y0), (x1, y1)], fill=color, width=int(tooth_width))
            
            # Draw body
            draw.ellipse((cx-r_body, cy-r_body, cx+r_body, cy+r_body), fill=color)
            
        elif shape == "stats":
            # 막대 그래프 아이콘
            # Bar 1
            draw.rectangle([(w*0.2, h*0.6), (w*0.35, h*0.8)], fill=color)
            # Bar 2
            draw.rectangle([(w*0.425, h*0.4), (w*0.575, h*0.8)], fill=color)
            # Bar 3
            draw.rectangle([(w*0.65, h*0.2), (w*0.8, h*0.8)], fill=color)
            
        elif shape == "mini":
            # 축소 아이콘 (네 모서리 안쪽 표시)
            m = w * 0.25
            l = w * 0.2
            # TL
            draw.line([(m, m), (m, m+l)], fill=color, width=int(scale*1.5))
            draw.line([(m, m), (m+l, m)], fill=color, width=int(scale*1.5))
            # TR
            draw.line([(w-m, m), (w-m, m+l)], fill=color, width=int(scale*1.5))
            draw.line([(w-m, m), (w-m-l, m)], fill=color, width=int(scale*1.5))
            # BL
            draw.line([(m, h-m), (m, h-m-l)], fill=color, width=int(scale*1.5))
            draw.line([(m, h-m), (m+l, h-m)], fill=color, width=int(scale*1.5))
            # BR
            draw.line([(w-m, h-m), (w-m, h-m-l)], fill=color, width=int(scale*1.5))
            draw.line([(w-m, h-m), (w-m-l, h-m)], fill=color, width=int(scale*1.5))

        image = image.resize(size, resample=Image.LANCZOS)
        return ImageTk.PhotoImage(image)

    def draw_timer(self):
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1: w = 320
        if h <= 1: h = 320
        
        # 고품질 렌더링을 위한 슈퍼샘플링 (2배 확대 후 축소)
        scale = 2
        img_w, img_h = w * scale, h * scale
        
        # 투명 배경 대신 캔버스 배경색으로 이미지 생성
        image = Image.new("RGBA", (img_w, img_h), self.colors["bg"])
        draw = ImageDraw.Draw(image)
        
        cx, cy = img_w / 2, img_h / 2
        radius = min(img_w, img_h) / 2 * 0.88
        arc_radius = radius * 0.65
        
        # 0. 배경 원
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=self.colors["timer_bg"], outline=self.colors["timer_outline"], width=int(2*scale))
        
        # 1. 남은 시간 영역 그리기
        display_time = min(self.current_time, 3600)
        angle = (display_time / 3600) * 360
        color = "#FF5252" if self.mode == "work" else "#4CAF50"
        
        if display_time >= 3600:
            draw.ellipse((cx-arc_radius, cy-arc_radius, cx+arc_radius, cy+arc_radius), fill=color, outline=color)
        elif display_time > 0:
            # PIL은 3시 방향이 0도, 시계 방향으로 증가
            # 12시 방향은 270도
            start_angle = 270
            end_angle = 270 + angle
            draw.pieslice((cx-arc_radius, cy-arc_radius, cx+arc_radius, cy+arc_radius), start=start_angle, end=end_angle, fill=color, outline=color)

        # 2. 눈금 그리기 (0~60분)
        font_size = max(10, int(radius * 0.1))
        try:
            font = ImageFont.truetype(resource_path("arialbd.ttf"), font_size)
        except IOError:
            try:
                font = ImageFont.truetype("arialbd.ttf", font_size)
            except IOError:
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()

        for i in range(60):
            angle_deg = 90 - (i * 6)
            angle_rad = math.radians(angle_deg)
            
            if i % 5 == 0:
                tick_len = 20 * scale
                width = 2 * scale
                
                # 5분 단위 숫자 표시
                text_radius = radius - (35 * scale)
                tx = cx + text_radius * math.cos(angle_rad)
                ty = cy - text_radius * math.sin(angle_rad)
                text = str(i if i != 0 else 60)
                draw.text((tx, ty), text, font=font, fill=self.colors["timer_outline"], anchor="mm")
            else:
                tick_len = 10 * scale
                width = 1 * scale
                
            x_out = cx + radius * math.cos(angle_rad)
            y_out = cy - radius * math.sin(angle_rad)
            x_in = cx + (radius - tick_len) * math.cos(angle_rad)
            y_in = cy - (radius - tick_len) * math.sin(angle_rad)
            
            draw.line((x_in, y_in, x_out, y_out), fill=self.colors["timer_outline"], width=int(width))

        # 4. 중앙 디지털 시간 표시
        center_radius = radius * 0.22
        draw.ellipse((cx-center_radius, cy-center_radius, cx+center_radius, cy+center_radius), fill=self.colors["timer_center"])
        
        mins, secs = divmod(int(self.current_time), 60)
        time_str = "{:02d}:{:02d}".format(mins, secs)
        
        font_size_time = max(20, int(radius * 0.16))
        try:
            font_time = ImageFont.truetype(resource_path("arialbd.ttf"), font_size_time)
        except IOError:
            try:
                font_time = ImageFont.truetype("arialbd.ttf", font_size_time)
            except IOError:
                font_time = ImageFont.load_default()
            
        draw.text((cx, cy), time_str, font=font_time, fill=self.colors["fg"], anchor="mm")
        
        # 이미지 리사이즈 (안티앨리어싱) 및 캔버스에 표시
        image = image.resize((w, h), resample=Image.BILINEAR)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

        # 윈도우 타이틀 업데이트
        if self.is_running:
            mins, secs = divmod(int(self.current_time), 60)
            time_str = "{:02d}:{:02d}".format(mins, secs)
            new_title = f"{time_str} - God-Mode Timer"
            if self.root.title() != new_title:
                self.root.title(new_title)
            
            # 작업 표시줄 진행률 업데이트
            total_time = self.work_time if self.mode == "work" else self.break_time
            self.taskbar.set_progress(self.current_time, total_time)
        elif self.root.title() != "God-Mode Timer":
            self.root.title("God-Mode Timer")
            self.taskbar.reset()

    def toggle_mini_mode(self):
        if not self.is_mini_mode:
            # 미니 모드 진입
            self.is_mini_mode = True
            self.normal_geometry = self.root.geometry()
            
            # UI 숨기기
            self.btn_frame.pack_forget()
            self.task_frame.pack_forget()
            
            # 윈도우 설정 (타이틀바 제거, 크기 축소)
            self.root.overrideredirect(True)
            self.root.minsize(0, 0)
            self.root.geometry("200x200")
            self.root.attributes('-topmost', True)
            
            # 드래그 이동 및 복귀 이벤트 바인딩
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            
            self.canvas.bind("<ButtonPress-1>", self.start_move)
            self.canvas.bind("<ButtonRelease-1>", self.stop_move)
            self.canvas.bind("<B1-Motion>", self.do_move)
            self.canvas.bind("<Double-Button-1>", self.exit_mini_mode)
            
            show_toast("미니 모드", "더블 클릭하면 원래대로 돌아옵니다.")
        else:
            self.exit_mini_mode()

    def exit_mini_mode(self, event=None):
        if not self.is_mini_mode: return
        
        self.is_mini_mode = False
        
        # 윈도우 복원
        self.root.overrideredirect(False)
        self.root.minsize(300, 350)
        self.root.geometry(self.normal_geometry)
        self.root.attributes('-topmost', self.setting_always_on_top)
        
        # UI 복원
        self.update_task_input_visibility()
        self.btn_frame.pack(pady=(0, 15))
        
        # 이벤트 복원
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Double-Button-1>")
        
        self.canvas.bind("<Button-1>", self.handle_mouse_input)
        self.canvas.bind("<B1-Motion>", self.handle_mouse_input)
        
        self.draw_timer()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def toggle_timer(self):
        if self.is_running:
            # 실행 중이면 중지(초기화)
            self.reset_timer()
        else:
            # 정지 상태면 시작
            self.is_running = True
            self.update_start_button_color()
            self.disable_settings_button()
            self.disable_task_entry()
            
            if self.mode == "work":
                show_toast("집중 시작", "집중 타이머가 시작되었습니다.")
            else:
                show_toast("휴식 시작", "휴식 타이머가 시작되었습니다.")
            
            self.last_time = time.time()
            self.count_down()

    def count_down(self):
        if self.is_running and self.current_time > 0:
            now = time.time()
            elapsed = now - self.last_time
            self.last_time = now
            
            self.current_time -= elapsed
            if self.current_time < 0: self.current_time = 0
            
            self.draw_timer()
            self.root.after(50, self.count_down)
        elif self.current_time <= 0 and self.is_running:
            self.finish_cycle()

    def finish_cycle(self):
        # 윈도우를 맨 앞으로 가져오기
        self.root.deiconify()
        if self.setting_sound:
            play_sound()
        
        if self.mode == "work":
            task_content = self.task_var.get()
            if task_content == self.task_placeholder:
                task_content = None
            log_godmode(task_content, self.setting_work_min, status="success")
            
            # 로그 저장 후 입력창 초기화 (다음 작업을 위해)
            self.task_var.set("")
            self.on_task_focus_out(None) # 플레이스홀더 복구
            
            self.godmode_count += 1
            self.mode = "break"
            
            # 4번 집중(4의 배수)마다 15분 긴 휴식
            if self.godmode_count > 0 and self.godmode_count % self.setting_long_break_interval == 0:
                self.break_time = self.setting_long_break_min * 60
                msg = f"{self.setting_long_break_interval}번의 집중({self.godmode_count}회) 완료! {self.setting_long_break_min}분간 긴 휴식을 취하세요."
            else:
                self.break_time = self.setting_short_break_min * 60
                msg = "집중 시간이 끝났습니다! 휴식을 취하세요."
            
            self.current_time = self.break_time
            
            if self.setting_auto_start:
                show_toast("집중 완료", msg + " (자동 시작)")
                self.is_running = True
                self.update_start_button_color()
                self.last_time = time.time()
                self.draw_timer()
                self.root.after(50, self.count_down)
            else:
                show_toast("집중 완료", msg)
                self.is_running = False
                self.enable_settings_button()
                self.enable_task_entry()
                self.update_start_button_color()
                self.draw_timer()
        else:
            self.mode = "work"
            self.current_time = self.work_time
            
            if self.setting_auto_start:
                show_toast("휴식 완료", "휴식 시간이 끝났습니다! 집중 시간이 시작됩니다.")
                self.is_running = True
                self.update_start_button_color()
                self.last_time = time.time()
                self.draw_timer()
                self.root.after(50, self.count_down)
            else:
                show_toast("휴식 완료", "휴식 시간이 끝났습니다! 다시 집중해볼까요?")
                self.is_running = False
                self.enable_settings_button()
                self.enable_task_entry()
                self.update_start_button_color()
                self.draw_timer()

    def reset_timer(self):
        self.is_running = False
        self.enable_settings_button()
        self.enable_task_entry()
        self.update_start_button_color()
        self.mode = "work"
        self.work_time = self.setting_work_min * 60
        self.current_time = self.work_time
        self.draw_timer()

    def update_start_button_color(self):
        if self.is_running:
            self.start_button.config(image=self.icon_stop, bg=self.colors["stop_btn_bg"])
        else:
            self.start_button.config(image=self.icon_play, bg=self.colors["start_btn_bg"])

    def enable_settings_button(self):
        self.settings_button.config(state=tk.NORMAL, image=self.icon_settings)

    def disable_settings_button(self):
        self.settings_button.config(state=tk.DISABLED, image=self.icon_settings_disabled)

    def enable_task_entry(self):
        self.task_entry.config(state=tk.NORMAL)

    def disable_task_entry(self):
        self.task_entry.config(state=tk.DISABLED)

    def on_task_focus_in(self, event):
        if self.task_var.get() == self.task_placeholder:
            self.task_entry.delete(0, tk.END)
            self.task_entry.config(fg=self.colors["fg"])

    def on_task_focus_out(self, event):
        if not self.task_var.get():
            self.task_entry.insert(0, self.task_placeholder)
            self.task_entry.config(fg=self.colors["fg_sub"])

    def on_task_return(self, event):
        if not self.is_running:
            self.root.focus_set()
            self.toggle_timer()

    def handle_mouse_input(self, event):
        if self.is_running:
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1: w = 320
        if h <= 1: h = 320
        cx, cy = w / 2, h / 2
        dx = event.x - cx
        dy = event.y - cy
        
        # 중앙 시간 표시 영역(흰색 원) 내부 클릭 시 무시
        radius = min(w, h) / 2 * 0.88
        center_radius = radius * 0.22
        if math.sqrt(dx*dx + dy*dy) < center_radius:
            return
        
        deg = math.degrees(math.atan2(dy, dx))
        angle = (deg + 90) % 360
        
        minutes = round(angle / 6 / 5) * 5
        if minutes == 0: minutes = 60
        
        if self.setting_work_min != minutes and self.setting_sound:
            play_tick_sound()

        self.setting_work_min = minutes
        self.work_time = minutes * 60
        self.reset_timer()

    def load_settings(self):
        settings_path = get_user_data_path("settings.json")
        if not os.path.exists(settings_path):
            self.save_settings_to_file()
            return

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.setting_always_on_top = data.get("always_on_top", True)
                self.setting_auto_start = data.get("auto_start", False)
                self.setting_sound = data.get("sound", True)
                self.setting_work_min = data.get("work_min", 25)
                self.setting_short_break_min = data.get("short_break_min", 5)
                self.setting_long_break_min = data.get("long_break_min", 15)
                self.setting_long_break_interval = data.get("long_break_interval", 4)
                self.setting_show_task_input = data.get("show_task_input", False)
        except Exception:
            self.restore_default_settings()

    def restore_default_settings(self):
        self.setting_always_on_top = True
        self.setting_auto_start = False
        self.setting_sound = True
        self.setting_work_min = 25
        self.setting_short_break_min = 5
        self.setting_long_break_min = 15
        self.setting_long_break_interval = 4
        self.setting_show_task_input = False
        self.save_settings_to_file()
        self.root.attributes('-topmost', self.setting_always_on_top)
        self.update_theme_colors()
        self.apply_theme()
        self.update_task_input_visibility()

    def save_settings_to_file(self):
        data = {
            "always_on_top": self.setting_always_on_top,
            "auto_start": self.setting_auto_start,
            "sound": self.setting_sound,
            "work_min": self.setting_work_min,
            "short_break_min": self.setting_short_break_min,
            "long_break_min": self.setting_long_break_min,
            "long_break_interval": self.setting_long_break_interval,
            "show_task_input": self.setting_show_task_input
        }
        try:
            with open(get_user_data_path("settings.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def on_closing(self):
        self.show_exit_popup()

    def show_exit_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("종료")
        popup.geometry("280x140")
        popup.resizable(False, False)
        popup.configure(bg=self.colors["bg"])
        popup.transient(self.root)
        popup.grab_set()
        popup.focus_set()
        
        # 화면 중앙 배치
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 140
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 70
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text="정말 종료하시겠습니까?", font=("Helvetica", 11), bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=(30, 20))

        btn_frame = tk.Frame(popup, bg=self.colors["bg"])
        btn_frame.pack(pady=5)

        def do_exit(event=None):
            popup.destroy()
            self.save_settings_to_file()
            self.tray_icon.stop()
            self.root.destroy()

        tk.Button(btn_frame, text="종료", font=("Helvetica", 10, "bold"), bg=self.colors["stop_btn_bg"], fg="white", bd=0, padx=15, pady=5, command=do_exit).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="취소", font=("Helvetica", 10), bg="#E0E0E0", fg="#555555", bd=0, padx=15, pady=5, command=popup.destroy).pack(side=tk.LEFT, padx=10)
        
        popup.bind('<Return>', do_exit)

    def minimize_to_tray(self, event):
        if event.widget == self.root and self.root.state() == 'iconic':
            self.root.withdraw()
            show_toast("백그라운드 실행", "앱이 시스템 트레이로 최소화되었습니다.")

    def snap_to_edge(self, event):
        if event.widget != self.root:
            return

        threshold = 20
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        geom = self.root.geometry()
        # Parse geometry string: WxH+X+Y
        match = re.match(r"(\d+)x(\d+)([\+\-]\d+)([\+\-]\d+)", geom)
        if not match:
            return
            
        w, h = int(match.group(1)), int(match.group(2))
        x, y = int(match.group(3)), int(match.group(4))
        
        new_x = x
        new_y = y
        
        # Snap Left
        if abs(x) < threshold:
            new_x = 0
        # Snap Right
        elif abs(screen_width - (x + w)) < threshold:
            new_x = screen_width - w
            
        # Snap Top
        if abs(y) < threshold:
            new_y = 0
        # Snap Bottom
        elif abs(screen_height - (y + h)) < threshold:
            new_y = screen_height - h
            
        if new_x != x or new_y != y:
            self.root.geometry(f"+{new_x}+{new_y}")

    def open_settings(self):
        open_settings_window(self)

    def open_stats(self):
        open_stats_window(self)

    def update_task_input_visibility(self):
        if self.setting_show_task_input:
            self.task_frame.pack(pady=(0, 10), fill=tk.X, padx=30)
        else:
            self.task_frame.pack_forget()

    def update_theme_colors(self):
        self.colors = {
            "bg": "#FFF8F0",
            "fg": "#555555",
            "fg_sub": "#888888",
            "btn_bg": "#F0F0F0",
            "btn_fg": "#555555",
            "btn_hover": "#E0E0E0",
            "timer_bg": "#FFFFFF",
            "timer_center": "#F0F0F0",
            "timer_work": "#FF5252",
            "timer_break": "#4CAF50",
            "timer_outline": "black",
            "start_btn_bg": "#FFDAC1",
            "start_btn_hover": "#FFC8A0",
            "stop_btn_bg": "#FF9AA2",
            "icon_color": "#555555",
            "stats_bar_today": "#FF5252",
            "stats_bar_other": "#FFCDD2"
        }

    def apply_theme(self):
        self.root.configure(bg=self.colors["bg"])
        self.canvas.configure(bg=self.colors["bg"])
        self.btn_frame.configure(bg=self.colors["bg"])
        
        self.start_button.configure(fg=self.colors["btn_fg"])
        self.settings_button.configure(bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
        self.stats_button.configure(bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
        self.mini_button.configure(bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
        
        if hasattr(self, 'task_frame'):
            self.task_frame.configure(bg=self.colors["bg"])
            self.task_entry.configure(bg=self.colors["btn_bg"])
            if self.task_var.get() == self.task_placeholder:
                self.task_entry.configure(fg=self.colors["fg_sub"])
            else:
                self.task_entry.configure(fg=self.colors["fg"])
        
        self.icon_play = self.create_button_icon("play", self.colors["icon_color"], size=(32, 32))
        self.icon_settings = self.create_button_icon("settings", self.colors["icon_color"])
        self.icon_settings_disabled = self.create_button_icon("settings", "#CCCCCC")
        self.icon_stats = self.create_button_icon("stats", self.colors["icon_color"])
        self.icon_mini = self.create_button_icon("mini", self.colors["icon_color"])
        
        self.settings_button.config(image=self.icon_settings)
        self.stats_button.config(image=self.icon_stats)
        self.mini_button.config(image=self.icon_mini)
        self.update_start_button_color()
        
        self.draw_timer()

if __name__ == "__main__":
    root = tk.Tk()
    app = GodModeApp(root)
    root.mainloop()