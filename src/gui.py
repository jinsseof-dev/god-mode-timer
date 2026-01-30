import tkinter as tk
from tkinter import messagebox
from utils import play_sound, log_godmode, show_toast, play_tick_sound, parse_logs
from taskbar import WindowsTaskbar
from common import resource_path, get_user_data_path
from settings_window import open_settings_window
from stats_window import open_stats_window
from ad_window import show_ad_window
from localization import Localization
import time
import math
import sys
import re
from PIL import Image, ImageDraw, ImageFont, ImageTk
import json
import os
from datetime import datetime

class GodModeApp:
    def __init__(self, root):
        self.root = root
        # 초기 로컬라이제이션 (시스템 언어 감지)
        self.loc = Localization()
        self.root.title(self.loc.get("app_title"))

        # --- 상태 변수 및 설정 로드 (UI 스케일 계산 전 선행) ---
        self.load_env()
        self.app_version = os.environ.get("VERSION", "v1.21")
        self.is_running = False
        self.setting_always_on_top = True
        self.setting_auto_start = False
        self.setting_sound = True
        self.setting_work_min = 25
        self.setting_short_break_min = 5
        self.setting_long_break_min = 15
        self.setting_long_break_interval = 4
        self.setting_show_task_input = False
        self.setting_strict_mode = False
        self.setting_opacity = 1.0
        self.setting_ui_scale = 100 # 사용자 UI 크기 설정 (%)
        self.setting_theme = "Light"
        self.setting_language = self.loc.lang_code # 기본 언어 (시스템 언어)
        self.is_mini_mode = False
        
        self.window_x = None
        self.window_y = None
        self.settings_window_x = None
        self.settings_window_y = None
        self.settings_window_w = None
        self.settings_window_h = None
        self.stats_window_x = None
        self.stats_window_y = None
        self.stats_window_w = None
        self.stats_window_h = None
        self.stats_window = None
        self.last_scale = 1.0
        self.transition_job = None

        self.load_settings()
        
        # 설정된 언어가 감지된 언어와 다르면 다시 로드
        if self.setting_language != self.loc.lang_code:
            self.loc.load_language(self.setting_language)
            self.root.title(self.loc.get("app_title"))
        
        # 화면 해상도에 비례하여 초기 크기 설정 (FHD 기준)
        self.update_scale_factor()
        
        self.root.geometry(f"{self.initial_w}x{self.initial_h}")
        self.root.resizable(True, True)
        self.root.minsize(300, 400)
        
        # 윈도우 작업 표시줄 진행률 초기화
        self.taskbar = WindowsTaskbar(root)
        
        # 윈도우 아이콘 설정
        self.set_window_icon()

        # 윈도우 닫기 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 윈도우 자석 효과 (Snap to Edge)
        self.root.bind("<Configure>", self.on_window_configure)

        # 스페이스바 단축키
        self.root.bind("<space>", self.toggle_timer_shortcut)

        # 마우스 휠로 시간 조절
        self.root.bind("<MouseWheel>", self.handle_mouse_wheel)

        self.normal_geometry = f"{self.initial_w}x{self.initial_h}"
        
        self.refresh_today_count()
        
        if self.window_x is not None and self.window_y is not None:
            self.root.geometry(f"+{self.window_x}+{self.window_y}")
        
        # 테마 색상 정의 및 적용
        self.update_theme_colors()
        
        self.update_topmost_status()
        self.update_opacity()
        self.root.configure(bg=self.colors["bg"])
        
        self.work_time = self.setting_work_min * 60
        self.break_time = self.setting_short_break_min * 60
        self.current_time = self.work_time
        self.mode = "work"  # 'work' or 'break'

        # 보조 버튼 프레임 (통계, 설정, 미니모드) - 하단 배치 (가장 먼저 pack하여 공간 확보)
        self.btn_frame = tk.Frame(root, bg=self.colors["bg"])
        self.btn_frame.pack(side=tk.BOTTOM, pady=(0, 15))

        self.start_button = tk.Button(self.btn_frame, text="▶", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["start_btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.toggle_timer)
        self.start_button.pack(side=tk.LEFT, padx=2)
        self.start_button.bind("<Enter>", lambda e: self.start_button.config(bg=self.colors["start_btn_hover"]))
        self.start_button.bind("<Leave>", lambda e: self.update_start_button_color())

        self.stats_button = tk.Button(self.btn_frame, text="📊", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.open_stats)
        self.stats_button.pack(side=tk.LEFT, padx=2)
        self.stats_button.bind("<Enter>", lambda e: self.stats_button.config(bg=self.colors["btn_hover"]))
        self.stats_button.bind("<Leave>", lambda e: self.stats_button.config(bg=self.colors["btn_bg"]))

        self.settings_button = tk.Button(self.btn_frame, text="⚙", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=2)
        self.settings_button.bind("<Enter>", lambda e: self.settings_button.config(bg=self.colors["btn_hover"]) if self.settings_button['state'] != tk.DISABLED else None)
        self.settings_button.bind("<Leave>", lambda e: self.settings_button.config(bg=self.colors["btn_bg"]) if self.settings_button['state'] != tk.DISABLED else None)

        self.skip_button = tk.Button(self.btn_frame, text="⏭", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.skip_break)
        self.skip_button.bind("<Enter>", lambda e: self.skip_button.config(bg=self.colors["btn_hover"]))
        self.skip_button.bind("<Leave>", lambda e: self.skip_button.config(bg=self.colors["btn_bg"]))
        # skip_button은 휴식 시간에만 표시되므로 초기에는 pack하지 않음
        
        self.repeat_button = tk.Button(self.btn_frame, text="🔁", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.repeat_break)
        self.repeat_button.bind("<Enter>", lambda e: self.repeat_button.config(bg=self.colors["btn_hover"]))
        self.repeat_button.bind("<Leave>", lambda e: self.repeat_button.config(bg=self.colors["btn_bg"]))
        # repeat_button은 집중 모드 대기 상태에서만 표시됨

        # 아이콘 이미지 생성
        self.icon_play = self.create_button_icon("play", self.colors["icon_color"], size=(24, 24))
        self.icon_stop = self.create_button_icon("stop", "#FF5252", size=(24, 24))
        self.icon_settings = self.create_button_icon("settings", self.colors["icon_color"])
        self.icon_settings_disabled = self.create_button_icon("settings", "#CCCCCC")
        self.icon_stats = self.create_button_icon("stats", self.colors["icon_color"])
        self.icon_skip = self.create_button_icon("skip", self.colors["icon_color"])
        self.icon_repeat = self.create_button_icon("repeat", self.colors["icon_color"])
        
        # 버튼에 이미지 적용 (초기 상태)
        self.start_button.config(image=self.icon_play, text="", width=50, height=40)
        self.settings_button.config(image=self.icon_settings, text="", width=50, height=40)
        self.stats_button.config(image=self.icon_stats, text="", width=50, height=40)
        self.skip_button.config(image=self.icon_skip, text="", width=50, height=40)
        self.repeat_button.config(image=self.icon_repeat, text="", width=50, height=40)

        # 할 일 입력 프레임 (Task Input)
        self.task_frame = tk.Frame(root, bg=self.colors["bg"])
        
        self.task_var = tk.StringVar()
        self.task_placeholder = self.loc.get("task_placeholder")
        
        self.task_entry = tk.Entry(self.task_frame, textvariable=self.task_var, font=("Helvetica", 10), bg=self.colors["btn_bg"], fg=self.colors["fg_sub"], bd=0, justify="center")
        self.task_entry.pack(fill=tk.X, ipady=6)
        self.task_entry.insert(0, self.task_placeholder)
        
        self.task_entry.bind("<FocusIn>", self.on_task_focus_in)
        self.task_entry.bind("<FocusOut>", self.on_task_focus_out)
        self.task_entry.bind("<Return>", self.on_task_return)

        # 타이머 표시 (도형) - 나머지 공간 채움
        self.canvas = tk.Canvas(root, bg=self.colors["bg"], highlightthickness=0)
        self.canvas.pack(pady=0, expand=True, fill=tk.BOTH)

        self.draw_timer()
        self.canvas.bind("<Configure>", lambda e: self.draw_timer())
        self.canvas.bind("<Button-1>", self.handle_mouse_input)
        self.canvas.bind("<B1-Motion>", self.handle_mouse_input)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        
        # 마우스 커서 변경
        self.canvas.bind("<Enter>", lambda e: self.root.config(cursor="hand2"))
        self.canvas.bind("<Leave>", lambda e: self.root.config(cursor=""))

        self.tk_image = None
        
        # 설정에 따라 할 일 입력창 표시 여부 결정
        self.update_task_input_visibility()
        self.update_control_buttons_visibility()

    def load_env(self):
        """프로젝트 루트의 .env 파일에서 환경 변수를 로드합니다."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_path = os.path.join(base_dir, ".env")
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip().strip('"').strip("'")
        except Exception:
            pass

    def update_scale_factor(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 너비와 높이 비율을 모두 고려하여 스케일 계산 (FHD 1920x1080 기준)
        ratio_w = screen_width / 1920
        ratio_h = screen_height / 1080
        base_scale = min(ratio_w, ratio_h)
        
        # DPI 스케일링 감지 (Windows 디스플레이 배율 설정 반영)
        try:
            dpi = self.root.winfo_fpixels('1i')
            dpi_scale = dpi / 96.0
        except Exception:
            dpi_scale = 1.0
        
        # 해상도/DPI에 따른 자동 스케일 계산
        auto_scale = max(1.0, min(3.0, max(base_scale, dpi_scale)))
        
        # 사용자 UI 크기 설정 적용
        self.scale_factor = auto_scale * (self.setting_ui_scale / 100.0)
        
        self.initial_w = int(300 * self.scale_factor)
        self.initial_h = int(400 * self.scale_factor)
        
        # 화면 높이의 90%를 넘지 않도록 안전장치 (세로 해상도가 낮은 경우)
        if self.initial_h > screen_height * 0.9:
            self.scale_factor = (screen_height * 0.9) / 400
            self.initial_w = int(300 * self.scale_factor)
            self.initial_h = int(400 * self.scale_factor)

    def apply_ui_scale(self):
        self.update_scale_factor()
        self.root.geometry(f"{self.initial_w}x{self.initial_h}")
        self.normal_geometry = f"{self.initial_w}x{self.initial_h}"
        
        # 통계 창이 열려있다면 크기 및 UI 업데이트
        if hasattr(self, 'stats_window') and self.stats_window and self.stats_window.winfo_exists():
            if hasattr(self.stats_window, 'refresh_ui_scale'):
                self.stats_window.refresh_ui_scale()

    def set_window_icon(self):
        # 윈도우 아이콘 동적 생성 (황금 번개 - 갓생 모드)
        # 고해상도 아이콘을 위해 크기 증가 (64 -> 256)
        size = 256
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 배경 원 (다크 그레이)
        margin = size * 2 / 64
        draw.ellipse((margin, margin, size - margin, size - margin), fill="#333333", outline="#555555")
        
        # Lightning Bolt Points (Zigzag shape)
        base_points = [(36, 4), (20, 34), (32, 34), (16, 60), (48, 26), (36, 26)]
        points = [(x * size / 64, y * size / 64) for x, y in base_points]
        
        width = int(max(1, 2 * size / 64))
        draw.polygon(points, fill="#FFD700", outline="#B8860B", width=width)
        
        self.tk_icon = ImageTk.PhotoImage(image)
        self.root.iconphoto(True, self.tk_icon)

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
            
        elif shape == "skip":
            # Skip icon (Next track style: |>|)
            # Triangle
            draw.polygon([(w*0.25, h*0.2), (w*0.25, h*0.8), (w*0.65, h*0.5)], fill=color)
            # Line
            draw.rectangle([(w*0.65, h*0.2), (w*0.75, h*0.8)], fill=color)
            
        elif shape == "repeat":
            # Rest icon (Coffee Cup)
            # Cup body
            draw.rectangle([(w*0.2, h*0.4), (w*0.75, h*0.8)], fill=color)
            # Handle
            draw.line([(w*0.75, h*0.5), (w*0.9, h*0.5), (w*0.9, h*0.7), (w*0.75, h*0.7)], fill=color, width=int(w*0.08))
            # Steam
            draw.line([(w*0.35, h*0.2), (w*0.35, h*0.3)], fill=color, width=int(w*0.06))
            draw.line([(w*0.5, h*0.15), (w*0.5, h*0.3)], fill=color, width=int(w*0.06))
            draw.line([(w*0.65, h*0.2), (w*0.65, h*0.3)], fill=color, width=int(w*0.06))

        image = image.resize(size, resample=Image.LANCZOS)
        return ImageTk.PhotoImage(image)

    def draw_timer(self):
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1: w = 320
        if h <= 1: h = 320
        
        # 고품질 렌더링을 위한 슈퍼샘플링 (2배 확대 후 축소)
        supersample = 2
        img_w, img_h = w * supersample, h * supersample
        
        # UI 스케일링 비율 (기본 1.0)
        ui_scale = getattr(self, 'last_scale', 1.0)
        
        # 투명 배경 대신 캔버스 배경색으로 이미지 생성
        image = Image.new("RGBA", (img_w, img_h), self.colors["bg"])
        draw = ImageDraw.Draw(image)
        
        cx, cy = img_w / 2, img_h / 2
        radius = min(img_w, img_h) / 2 * 0.88
        arc_radius = radius * 0.65
        
        # 선 두께 계산 (UI 스케일 반영)
        outline_width = max(1, int(3 * supersample * ui_scale))
        
        # 0. 배경 원
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=self.colors["timer_bg"], outline=self.colors["timer_outline"], width=outline_width)
        
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
        font_size = max(9, int(radius * 0.09))
        font = self.load_font(font_size, bold=True)

        for i in range(60):
            angle_deg = 90 - (i * 6)
            angle_rad = math.radians(angle_deg)
            
            if i % 5 == 0:
                tick_len = 10 * supersample * ui_scale
                width = 3.2805 * supersample * ui_scale
                
                # 5분 단위 숫자 표시
                text_radius = radius - (35 * supersample * ui_scale)
                tx = cx + text_radius * math.cos(angle_rad)
                ty = cy - text_radius * math.sin(angle_rad)
                text = str(i if i != 0 else 60)
                draw.text((tx, ty), text, font=font, fill=self.colors["timer_outline"], anchor="mm")
            else:
                tick_len = 5 * supersample * ui_scale
                width = 1.64025 * supersample * ui_scale
            
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
        
        font_size_time = max(18, int(radius * 0.14))
        font_time = self.load_font(font_size_time, bold=True)
            
        draw.text((cx, cy), time_str, font=font_time, fill=self.colors["fg"], anchor="mm")
        
        # 6. 집중 사이클 트래커 (Cycle Tracker) - 중앙 하단
        if not self.is_mini_mode:
            cycle_len = self.setting_long_break_interval
            # 현재 사이클 내 완료 횟수 계산
            if self.mode == "break" and self.today_count > 0 and self.today_count % cycle_len == 0:
                # 롱 브레이크 중일 때는 꽉 찬 상태로 표시
                current_cycle_count = cycle_len
            else:
                current_cycle_count = self.today_count % cycle_len
            
            # 점 그리기 설정
            dot_radius = 4 * supersample * ui_scale
            dot_spacing = 10 * supersample * ui_scale
            total_width = (cycle_len * dot_radius * 2) + ((cycle_len - 1) * dot_spacing)
            start_x = cx - (total_width / 2) + dot_radius
            dot_y = cy + (radius * 0.45) # 시간 텍스트 아래 적절한 위치
            
            dot_outline_width = max(1, int(1.5 * supersample * ui_scale))
            
            for i in range(cycle_len):
                dx = start_x + i * (dot_radius * 2 + dot_spacing)
                
                if i < current_cycle_count:
                    fill_color = self.colors["fg"]
                    outline_color = self.colors["fg"]
                else:
                    fill_color = self.colors["timer_center"]
                    outline_color = "#AAAAAA"
                
                draw.ellipse((dx - dot_radius, dot_y - dot_radius, dx + dot_radius, dot_y + dot_radius), 
                             fill=fill_color, outline=outline_color, width=dot_outline_width)
        
        # 이미지 리사이즈 (안티앨리어싱) 및 캔버스에 표시
        image = image.resize((w, h), resample=Image.BILINEAR)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

        # 윈도우 타이틀 업데이트
        if self.is_running:
            mins, secs = divmod(int(self.current_time), 60)
            time_str = "{:02d}:{:02d}".format(mins, secs)
            app_title = self.loc.get("app_title")
            new_title = f"{time_str} - {app_title}"
            if self.root.title() != new_title and self.root.title() != app_title:
                self.root.title(new_title)
            
            # 작업 표시줄 진행률 업데이트
            total_time = self.work_time if self.mode == "work" else self.break_time
            self.taskbar.set_progress(self.current_time, total_time)
        elif self.root.title() != self.loc.get("app_title"):
            self.root.title(self.loc.get("app_title"))
            self.taskbar.reset()

    def load_font(self, size, bold=False):
        """시스템 폰트를 우선적으로 로드하여 고해상도에서 깨짐을 방지합니다."""
        font_candidates = []
        if sys.platform == "win32":
            if bold:
                font_candidates.extend(["arlrdbd.ttf", "segoeuib.ttf", "malgunbd.ttf", "arialbd.ttf"])
            else:
                font_candidates.extend(["segoeui.ttf", "malgun.ttf", "arial.ttf"])
        
        # 기본 후보 (리소스 경로 포함)
        if bold:
            font_candidates.append("arialbd.ttf")
        else:
            font_candidates.append("arial.ttf")

        for font_name in font_candidates:
            try:
                return ImageFont.truetype(font_name, size)
            except IOError:
                try:
                    return ImageFont.truetype(resource_path(font_name), size)
                except IOError:
                    continue
        
        return ImageFont.load_default()

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
            self.update_topmost_status()
            
            # 드래그 이동 및 복귀 이벤트 바인딩
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            
            self.canvas.bind("<ButtonPress-1>", self.start_move)
            self.canvas.bind("<ButtonRelease-1>", self.stop_move)
            self.canvas.bind("<B1-Motion>", self.do_move)
            self.canvas.bind("<Double-Button-1>", self.exit_mini_mode)
            
            show_toast(self.loc.get("mini_mode_title"), self.loc.get("mini_mode_msg"))
        else:
            self.exit_mini_mode()

    def exit_mini_mode(self, event=None):
        if not self.is_mini_mode: return
        
        self.is_mini_mode = False
        
        # 현재 미니모드 위치 및 크기
        mini_x = self.root.winfo_x()
        mini_y = self.root.winfo_y()
        mini_w = self.root.winfo_width()
        mini_h = self.root.winfo_height()
        
        # 일반 모드 크기 파싱
        match = re.match(r"(\d+)x(\d+)", self.normal_geometry)
        if match:
            norm_w = int(match.group(1))
            norm_h = int(match.group(2))
        else:
            norm_w, norm_h = 300, 400
            
        # 미니모드 중심점을 기준으로 일반 모드 위치 계산 (확장 효과)
        new_x = int(mini_x + (mini_w / 2) - (norm_w / 2))
        new_y = int(mini_y + (mini_h / 2) - (norm_h / 2))
        
        # 화면 경계 보정 (화면 밖으로 나가는 것 방지)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 오른쪽/아래쪽 벗어남 방지
        if new_x + norm_w > screen_width:
            new_x = screen_width - norm_w
        if new_y + norm_h > screen_height:
            new_y = screen_height - norm_h
            
        # 왼쪽/위쪽 벗어남 방지 (우선순위 높음)
        if new_x < 0: new_x = 0
        if new_y < 0: new_y = 0
        
        # 윈도우 복원 (깜빡임 방지 및 확실한 적용을 위해 withdraw/deiconify 사용)
        self.root.withdraw()
        self.root.overrideredirect(False)
        self.root.resizable(True, True)
        self.root.minsize(300, 400)
        self.root.geometry(f"{norm_w}x{norm_h}+{new_x}+{new_y}")
        self.root.deiconify()
        
        self.update_topmost_status()
        
        # UI 복원
        self.btn_frame.pack(side=tk.BOTTOM, before=self.canvas, pady=(0, 15))
        self.update_task_input_visibility()
        self.update_control_buttons_visibility()
        
        # 이벤트 복원
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Double-Button-1>")
        
        self.canvas.bind("<Button-1>", self.handle_mouse_input)
        self.canvas.bind("<B1-Motion>", self.handle_mouse_input)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        
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

    def on_canvas_double_click(self, event):
        if not self.is_mini_mode:
            self.toggle_mini_mode()

    def skip_break(self):
        """휴식을 건너뛰고 즉시 집중 모드로 전환합니다."""
        if self.mode != "break": return
        
        self.mode = "work"
        self.current_time = self.work_time
        
        # 타이머를 즉시 시작하지 않고 대기 상태로 전환
        self.is_running = False
        self.update_topmost_status()
        
        self.update_start_button_color()
        self.update_control_buttons_visibility()
        self.enable_settings_button()
        self.enable_task_entry()
        
        show_toast(self.loc.get("focus_wait_title"), self.loc.get("skip_break_msg"))
        self.draw_timer()

    def repeat_break(self):
        """휴식을 반복합니다 (현재 집중 모드 대기 상태에서 다시 휴식 모드로 전환)."""
        if self.mode != "work": return
        
        self.mode = "break"
        self.current_time = self.break_time
        
        was_running = self.is_running
        self.is_running = True
        self.update_topmost_status()
        self.last_time = time.time()
        
        self.update_start_button_color()
        self.update_control_buttons_visibility()
        self.disable_settings_button()
        self.disable_task_entry()
        
        show_toast(self.loc.get("break_repeat_title"), self.loc.get("break_repeat_msg"))
        self.draw_timer()
        
        if not was_running:
            self.count_down()

    def toggle_timer(self):
        if self.is_running:
            # 엄격 모드 체크 (집중 모드일 때만)
            if self.mode == "work" and self.setting_strict_mode:
                show_toast(self.loc.get("strict_mode_title"), self.loc.get("strict_mode_msg"))
                return

            # 실행 중이면 중지(초기화)
            self.reset_timer()
        else:
            # 정지 상태면 시작
            self.is_running = True
            self.update_topmost_status()
            self.update_start_button_color()
            self.update_control_buttons_visibility()
            self.disable_settings_button()
            self.disable_task_entry()
            
            if self.mode == "work":
                show_toast(self.loc.get("focus_start_title"), self.loc.get("focus_start_msg"))
            else:
                show_toast(self.loc.get("break_start_title"), self.loc.get("break_start_msg"))
            
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
            
            self.refresh_today_count()
            self.mode = "break"
            
            # 집중 완료 시 광고(후원) 팝업 표시 (2회마다)
            if self.today_count > 0 and self.today_count % 2 == 0:
                show_ad_window(self)
            
            # 4번 집중(4의 배수)마다 15분 긴 휴식
            if self.today_count > 0 and self.today_count % self.setting_long_break_interval == 0:
                self.break_time = self.setting_long_break_min * 60
                msg = self.loc.get("long_break_msg_fmt", interval=self.setting_long_break_interval, count=self.today_count, min=self.setting_long_break_min)
            else:
                self.break_time = self.setting_short_break_min * 60
                msg = self.loc.get("short_break_msg")
            
            self.current_time = self.break_time
            
            if self.setting_auto_start:
                show_toast(self.loc.get("focus_complete_title"), msg + " " + self.loc.get("auto_start_suffix"))
                self.is_running = True
                self.update_topmost_status()
                self.update_start_button_color()
                self.update_control_buttons_visibility()
                self.last_time = time.time()
                self.draw_timer()
                self.root.after(50, self.count_down)
            else:
                show_toast(self.loc.get("focus_complete_title"), msg)
                self.is_running = False
                self.update_topmost_status()
                self.update_control_buttons_visibility()
                self.enable_settings_button()
                self.enable_task_entry()
                self.update_start_button_color()
                self.draw_timer()
        else:
            self.mode = "work"
            self.current_time = self.work_time
            
            if self.setting_auto_start:
                show_toast(self.loc.get("break_complete_title"), self.loc.get("break_complete_auto_start_msg"))
                self.is_running = True
                self.update_topmost_status()
                self.update_start_button_color()
                self.last_time = time.time()
                self.draw_timer()
                self.root.after(50, self.count_down)
            else:
                show_toast(self.loc.get("break_complete_title"), self.loc.get("break_complete_msg"))
                self.is_running = False
                self.update_topmost_status()
                self.update_control_buttons_visibility()
                self.enable_settings_button()
                self.enable_task_entry()
                self.update_start_button_color()
                self.draw_timer()

    def reset_timer(self):
        self.is_running = False
        self.update_topmost_status()
        self.enable_settings_button()
        self.enable_task_entry()
        self.update_start_button_color()
        self.work_time = self.setting_work_min * 60
        
        if self.mode == "work":
            self.current_time = self.work_time
        else:
            self.current_time = self.break_time
            
        self.update_control_buttons_visibility()
        self.draw_timer()

    def update_start_button_color(self):
        if self.is_running:
            self.start_button.config(image=self.icon_stop, bg=self.colors["stop_btn_bg"])
        else:
            self.start_button.config(image=self.icon_play, bg=self.colors["start_btn_bg"])

    def update_control_buttons_visibility(self):
        self.skip_button.pack_forget()
        self.repeat_button.pack_forget()
        
        if self.mode == "break":
            self.skip_button.pack(side=tk.LEFT, padx=2)
        elif self.mode == "work" and not self.is_running:
            self.repeat_button.pack(side=tk.LEFT, padx=2)

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

    def toggle_timer_shortcut(self, event):
        focused = self.root.focus_get()
        # 입력창이나 버튼에 포커스가 있으면 해당 위젯의 기본 동작을 우선함
        if isinstance(focused, (tk.Entry, tk.Button)):
            return
        self.toggle_timer()

    def handle_mouse_input(self, event):
        self.root.focus_set()
        if self.is_running:
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1: w = 320
        if h <= 1: h = 320
        cx, cy = w / 2, h / 2
        dx = event.x - cx
        dy = event.y - cy
        
        # 거리 계산
        dist = math.sqrt(dx*dx + dy*dy)
        
        # 중앙 시간 표시 영역(흰색 원) 내부 또는 원 바깥 클릭 시 무시
        radius = min(w, h) / 2 * 0.88
        center_radius = radius * 0.22
        if dist < center_radius or dist > radius:
            return
        
        deg = math.degrees(math.atan2(dy, dx))
        angle = (deg + 90) % 360
        
        minutes = round(angle / 6 / 5) * 5
        if minutes == 0: minutes = 60
        
        if self.mode == "work":
            if self.setting_work_min != minutes and self.setting_sound:
                play_tick_sound()
            self.setting_work_min = minutes
            self.work_time = minutes * 60
            self.current_time = self.work_time
        else:
            current_break_min = round(self.break_time / 60)
            if current_break_min != minutes and self.setting_sound:
                play_tick_sound()
            self.break_time = minutes * 60
            self.current_time = self.break_time
        
        self.draw_timer()

    def handle_mouse_wheel(self, event):
        if self.is_running:
            return
            
        # 5분 단위 증감
        step = 5 if event.delta > 0 else -5
        
        if self.mode == "work":
            new_min = self.setting_work_min + step
            new_min = max(5, min(60, new_min))
            
            if self.setting_work_min != new_min:
                if self.setting_sound:
                    play_tick_sound()
                self.setting_work_min = new_min
                self.work_time = new_min * 60
                self.current_time = self.work_time
        else:
            current_break_min = round(self.break_time / 60)
            new_min = current_break_min + step
            new_min = max(5, min(60, new_min))
            
            if current_break_min != new_min:
                if self.setting_sound:
                    play_tick_sound()
                self.break_time = new_min * 60
                self.current_time = self.break_time
        
        self.draw_timer()

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
                self.setting_strict_mode = data.get("strict_mode", False)
                self.setting_opacity = data.get("opacity", 1.0)
                self.setting_ui_scale = data.get("ui_scale", 100)
                self.setting_theme = data.get("theme", "Light")
                self.setting_language = data.get("language", self.loc.lang_code)
                self.window_x = data.get("window_x")
                self.window_y = data.get("window_y")
                self.settings_window_x = data.get("settings_window_x")
                self.settings_window_y = data.get("settings_window_y")
                self.settings_window_w = data.get("settings_window_w")
                self.settings_window_h = data.get("settings_window_h")
                self.stats_window_x = data.get("stats_window_x")
                self.stats_window_y = data.get("stats_window_y")
                self.stats_window_w = data.get("stats_window_w")
                self.stats_window_h = data.get("stats_window_h")
        except Exception:
            self.restore_default_settings()

    def refresh_today_count(self):
        """오늘의 집중 횟수를 로그에서 다시 읽어옵니다."""
        daily_stats = parse_logs()
        today_str = datetime.now().strftime("%Y-%m-%d")
        stats = daily_stats.get(today_str, {'count': 0, 'duration': 0})
        self.today_count = stats['count']
        self.today_duration = stats.get('duration', 0)

    def restore_default_settings(self):
        self.setting_always_on_top = True
        self.setting_auto_start = False
        self.setting_sound = True
        self.setting_work_min = 25
        self.setting_short_break_min = 5
        self.setting_long_break_min = 15
        self.setting_long_break_interval = 4
        self.setting_show_task_input = False
        self.setting_strict_mode = False
        self.setting_ui_scale = 100
        self.window_x = None
        self.window_y = None
        self.setting_theme = "Light"
        self.setting_language = self.loc.get_system_language()
        self.settings_window_x = None
        self.settings_window_y = None
        self.settings_window_w = None
        self.settings_window_h = None
        self.stats_window_x = None
        self.stats_window_y = None
        self.stats_window_w = None
        self.stats_window_h = None
        self.save_settings_to_file()
        self.setting_opacity = 1.0
        self.update_topmost_status()
        self.update_theme_colors()
        self.apply_theme()
        self.update_task_input_visibility()
        self.update_opacity()

    def save_settings_to_file(self):
        data = {
            "always_on_top": self.setting_always_on_top,
            "auto_start": self.setting_auto_start,
            "sound": self.setting_sound,
            "work_min": self.setting_work_min,
            "short_break_min": self.setting_short_break_min,
            "long_break_min": self.setting_long_break_min,
            "long_break_interval": self.setting_long_break_interval,
            "show_task_input": self.setting_show_task_input,
            "strict_mode": self.setting_strict_mode,
            "opacity": self.setting_opacity,
            "ui_scale": self.setting_ui_scale,
            "theme": self.setting_theme,
            "language": self.setting_language,
            "window_x": self.root.winfo_x(),
            "window_y": self.root.winfo_y(),
            "settings_window_x": self.settings_window_x,
            "settings_window_y": self.settings_window_y,
            "settings_window_w": getattr(self, "settings_window_w", None),
            "settings_window_h": getattr(self, "settings_window_h", None),
            "stats_window_x": self.stats_window_x,
            "stats_window_y": self.stats_window_y,
            "stats_window_w": getattr(self, "stats_window_w", None),
            "stats_window_h": getattr(self, "stats_window_h", None)
        }
        try:
            with open(get_user_data_path("settings.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def on_closing(self):
        if self.is_running and self.mode == "work":
            show_toast(self.loc.get("focus_mode_title"), self.loc.get("strict_mode_exit_msg"))
            return
        self.save_settings_to_file()
        self.root.destroy()

    def show_exit_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title(self.loc.get("confirm_exit_title"))
        w = int(320 * self.scale_factor)
        h = int(160 * self.scale_factor)
        popup.geometry(f"{w}x{h}")
        popup.resizable(False, False)
        popup.minsize(200, 100)
        popup.configure(bg=self.colors["bg"])
        popup.transient(self.root)
        popup.grab_set()
        popup.focus_set()
        
        # 화면 중앙 배치
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (w // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (h // 2)
        popup.geometry(f"+{x}+{y}")

        container = tk.Frame(popup, bg=self.colors["bg"])
        container.pack(expand=True)

        tk.Label(container, text=self.loc.get("confirm_exit_msg"), font=("Helvetica", int(11 * self.scale_factor)), bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=(0, int(20 * self.scale_factor)))

        btn_frame = tk.Frame(container, bg=self.colors["bg"])
        btn_frame.pack()

        def do_exit(event=None):
            popup.destroy()
            self.save_settings_to_file()
            self.root.destroy()

        tk.Button(btn_frame, text=self.loc.get("exit"), font=("Helvetica", 10, "bold"), bg=self.colors["stop_btn_bg"], fg="white", bd=0, padx=15, pady=5, command=do_exit).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text=self.loc.get("cancel"), font=("Helvetica", 10), bg="#E0E0E0", fg="#555555", bd=0, padx=15, pady=5, command=popup.destroy).pack(side=tk.LEFT, padx=10)
        
        popup.bind('<Return>', do_exit)

    def on_window_configure(self, event):
        if event.widget == self.root:
            self.snap_to_edge(event)
            self.scale_ui()

    def scale_ui(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        
        if w <= 1 or h <= 1: return
        
        # 기본 크기(300x400) 기준 스케일 계산
        scale = min(w / 300, h / 400)
        
        # 변화가 작으면 무시 (성능 최적화)
        if abs(self.last_scale - scale) < 0.05:
            return
            
        self.last_scale = scale
        self.apply_theme() # 아이콘 재생성 및 적용
        
        btn_w = int(50 * scale)
        btn_h = int(40 * scale)
        font_size = max(8, int(9 * scale))
        
        for btn in [self.start_button, self.stats_button, self.settings_button, self.skip_button, self.repeat_button]:
            btn.config(width=btn_w, height=btn_h)
        
        self.task_entry.config(font=("Helvetica", font_size))

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

    def update_topmost_status(self):
        """현재 상태에 따라 윈도우의 최상위 속성을 업데이트합니다."""
        if self.is_mini_mode:
            self.root.attributes('-topmost', True)
        elif self.is_running and self.setting_always_on_top:
            self.root.attributes('-topmost', True)
        else:
            self.root.attributes('-topmost', False)

    def update_opacity(self):
        self.root.attributes('-alpha', self.setting_opacity)

    def update_task_input_visibility(self):
        if self.setting_show_task_input:
            self.task_frame.pack(side=tk.BOTTOM, before=self.canvas, pady=(0, 10), fill=tk.X, padx=30)
        else:
            self.task_frame.pack_forget()

    def get_theme_colors(self, theme):
        if theme == "Dark":
            return {
                "bg": "#212121",
                "fg": "#FFFFFF",
                "fg_sub": "#E0E0E0",
                "btn_bg": "#424242",
                "btn_fg": "#FFFFFF",
                "btn_hover": "#616161",
                "timer_bg": "#303030",
                "timer_center": "#616161",
                "timer_work": "#FF5252",
                "timer_break": "#66BB6A",
                "timer_outline": "#FFFFFF",
                "start_btn_bg": "#E64A19",
                "start_btn_hover": "#D84315",
                "stop_btn_bg": "#C62828",
                "icon_color": "#FFFFFF",
                "stats_bar_today": "#FF5252",
                "stats_bar_other": "#EF9A9A"
            }
        else:
            # Light Theme (Default)
            return {
                "bg": "#FFFFFF",
                "fg": "#555555",
                "fg_sub": "#888888",
                "btn_bg": "#F5F5F5",
                "btn_fg": "#555555",
                "btn_hover": "#FFE0B2",
                "timer_bg": "#FFFFFF",
                "timer_center": "#F5F5F5",
                "timer_work": "#FF5252",
                "timer_break": "#4CAF50",
                "timer_outline": "#000000",
                "start_btn_bg": "#FFDAC1",
                "start_btn_hover": "#FFC8A0",
                "stop_btn_bg": "#FF9AA2",
                "icon_color": "#555555",
                "stats_bar_today": "#FF5252",
                "stats_bar_other": "#FFCDD2"
            }

    def update_theme_colors(self):
        if self.transition_job:
            self.root.after_cancel(self.transition_job)
            self.transition_job = None
        self.colors = self.get_theme_colors(self.setting_theme)

    def transition_theme(self, target_theme, callback=None):
        if self.transition_job:
            self.root.after_cancel(self.transition_job)
            self.transition_job = None
            
        self.setting_theme = target_theme
        self.update_theme_colors()
        self.apply_theme()
        
        if callback:
            callback()

    def apply_theme(self):
        self.root.configure(bg=self.colors["bg"])
        self.canvas.configure(bg=self.colors["bg"])
        self.btn_frame.configure(bg=self.colors["bg"])
        
        self.start_button.configure(fg=self.colors["btn_fg"])
        self.settings_button.configure(bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
        self.stats_button.configure(bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
        self.skip_button.configure(bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
        self.repeat_button.configure(bg=self.colors["btn_bg"], fg=self.colors["btn_fg"])
        
        if hasattr(self, 'task_frame'):
            self.task_frame.configure(bg=self.colors["bg"])
            self.task_entry.configure(bg=self.colors["btn_bg"])
            if self.task_var.get() == self.task_placeholder:
                self.task_entry.configure(fg=self.colors["fg_sub"])
            else:
                self.task_entry.configure(fg=self.colors["fg"])
        
        icon_s = int(24 * self.last_scale)
        self.icon_play = self.create_button_icon("play", self.colors["icon_color"], size=(icon_s, icon_s))
        self.icon_stop = self.create_button_icon("stop", "#FF5252", size=(icon_s, icon_s))
        self.icon_settings = self.create_button_icon("settings", self.colors["icon_color"], size=(icon_s, icon_s))
        self.icon_settings_disabled = self.create_button_icon("settings", "#CCCCCC", size=(icon_s, icon_s))
        self.icon_stats = self.create_button_icon("stats", self.colors["icon_color"], size=(icon_s, icon_s))
        self.icon_skip = self.create_button_icon("skip", self.colors["icon_color"], size=(icon_s, icon_s))
        self.icon_repeat = self.create_button_icon("repeat", self.colors["icon_color"], size=(icon_s, icon_s))
        
        self.settings_button.config(image=self.icon_settings)
        self.stats_button.config(image=self.icon_stats)
        self.skip_button.config(image=self.icon_skip)
        self.repeat_button.config(image=self.icon_repeat)
        self.update_start_button_color()
        
        # 통계 창이 열려있다면 테마 업데이트
        if hasattr(self, 'stats_window') and self.stats_window and self.stats_window.winfo_exists():
            if hasattr(self.stats_window, 'refresh_theme'):
                self.stats_window.refresh_theme()
        
        self.draw_timer()

    def refresh_language(self):
        """UI에 표시된 모든 텍스트를 현재 언어 설정에 맞게 새로고침합니다."""
        # 1. 메인 윈도우 UI 업데이트
        if not self.is_running:
            self.root.title(self.loc.get("app_title"))
        
        self.task_placeholder = self.loc.get("task_placeholder")
        if not self.task_var.get() or self.task_entry.cget('fg') == self.colors['fg_sub']:
            self.task_var.set("")
            self.on_task_focus_out(None)
            
        # 2. 통계 창이 열려있다면 언어 새로고침
        if hasattr(self, 'stats_window') and self.stats_window and self.stats_window.winfo_exists():
            if hasattr(self.stats_window, 'refresh_language'):
                self.stats_window.refresh_language()

if __name__ == "__main__":
    # 윈도우 환경 설정 (콘솔 숨기기 및 High DPI)
    if sys.platform == "win32":
        try:
            import ctypes
            
            # 콘솔 창 숨기기 (python.exe로 실행 시 불필요한 콘솔 제거)
            if not getattr(sys, 'frozen', False):
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd != 0:
                    ctypes.windll.user32.ShowWindow(hwnd, 0)

            # High DPI 설정
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    root = tk.Tk()
    app = GodModeApp(root)
    root.mainloop()