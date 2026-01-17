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
        self.root.geometry("360x400")
        self.root.resizable(True, True)
        self.root.minsize(300, 350)
        

        # 윈도우 작업 표시줄 진행률 초기화
        self.taskbar = WindowsTaskbar(root)
        
        # 윈도우 아이콘 설정
        self.set_window_icon()

        # 윈도우 닫기 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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

        # 버튼 프레임
        self.btn_frame = tk.Frame(root, bg=self.colors["bg"])
        self.btn_frame.pack(pady=(0, 5))

        self.start_button = tk.Button(self.btn_frame, text="▶", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["start_btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.toggle_timer)
        self.start_button.pack(side=tk.LEFT, padx=10)
        self.start_button.bind("<Enter>", lambda e: self.start_button.config(bg=self.colors["start_btn_hover"]))
        self.start_button.bind("<Leave>", lambda e: self.update_start_button_color())

        self.settings_button = tk.Button(self.btn_frame, text="⚙", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=10)
        self.settings_button.bind("<Enter>", lambda e: self.settings_button.config(bg=self.colors["btn_hover"]) if self.settings_button['state'] != tk.DISABLED else None)
        self.settings_button.bind("<Leave>", lambda e: self.settings_button.config(bg=self.colors["btn_bg"]) if self.settings_button['state'] != tk.DISABLED else None)

        self.stats_button = tk.Button(self.btn_frame, text="📊", font=("Helvetica", 16), width=4, bd=0, bg=self.colors["btn_bg"], fg=self.colors["btn_fg"], pady=3, command=self.open_stats)
        self.stats_button.pack(side=tk.LEFT, padx=10)
        self.stats_button.bind("<Enter>", lambda e: self.stats_button.config(bg=self.colors["btn_hover"]))
        self.stats_button.bind("<Leave>", lambda e: self.stats_button.config(bg=self.colors["btn_bg"]))

        # 아이콘 이미지 생성
        self.icon_play = self.create_button_icon("play", self.colors["icon_color"])
        self.icon_stop = self.create_button_icon("stop", "white")
        self.icon_settings = self.create_button_icon("settings", self.colors["icon_color"])
        self.icon_settings_disabled = self.create_button_icon("settings", "#CCCCCC")
        self.icon_stats = self.create_button_icon("stats", self.colors["icon_color"])
        
        # 버튼에 이미지 적용 (초기 상태)
        self.start_button.config(image=self.icon_play, text="", width=50, height=40)
        self.settings_button.config(image=self.icon_settings, text="", width=50, height=40)
        self.stats_button.config(image=self.icon_stats, text="", width=50, height=40)

        self.tk_image = None

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
        font_size = max(16, int(radius * 0.07))
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
        center_radius = radius * 0.175
        draw.ellipse((cx-center_radius, cy-center_radius, cx+center_radius, cy+center_radius), fill=self.colors["timer_center"])
        
        mins, secs = divmod(int(self.current_time), 60)
        time_str = "{:02d}:{:02d}".format(mins, secs)
        
        font_size_time = max(20, int(radius * 0.09))
        try:
            font_time = ImageFont.truetype(resource_path("arialbd.ttf"), font_size_time)
        except IOError:
            try:
                font_time = ImageFont.truetype("arialbd.ttf", font_size_time)
            except IOError:
                try:
                    font_time = ImageFont.truetype("arial.ttf", font_size_time)
                except IOError:
                    font_time = ImageFont.load_default()
            
        draw.text((cx, cy), time_str, font=font_time, fill=self.colors["fg"], anchor="mm")

        # 이미지 리사이즈 (안티앨리어싱) 및 캔버스에 표시
        image = image.resize((w, h), resample=Image.BILINEAR)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

        # 윈도우 타이틀 업데이트
        if self.is_running:
            new_title = f"{time_str} - God-Mode Timer"
            if self.root.title() != new_title:
                self.root.title(new_title)
            
            # 작업 표시줄 진행률 업데이트
            total_time = self.work_time if self.mode == "work" else self.break_time
            self.taskbar.set_progress(self.current_time, total_time)
        elif self.root.title() != "God-Mode Timer":
            self.root.title("God-Mode Timer")
            self.taskbar.reset()

    def toggle_timer(self):
        if self.is_running:
            # 실행 중이면 중지(초기화)
            self.reset_timer()
        else:
            # 정지 상태면 시작
            self.is_running = True
            self.update_start_button_color()
            self.disable_settings_button()
            
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
            log_godmode()
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
                self.update_start_button_color()
                self.draw_timer()

    def reset_timer(self):
        self.is_running = False
        self.enable_settings_button()
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
        center_radius = radius * 0.175
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
        self.save_settings_to_file()
        self.root.attributes('-topmost', self.setting_always_on_top)
        self.update_theme_colors()
        self.apply_theme()

    def save_settings_to_file(self):
        data = {
            "always_on_top": self.setting_always_on_top,
            "auto_start": self.setting_auto_start,
            "sound": self.setting_sound,
            "work_min": self.setting_work_min,
            "short_break_min": self.setting_short_break_min,
            "long_break_min": self.setting_long_break_min,
            "long_break_interval": self.setting_long_break_interval
        }
        try:
            with open(get_user_data_path("settings.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def on_closing(self):
        if messagebox.askokcancel("종료", "정말 종료하시겠습니까?"):
            self.save_settings_to_file()
            self.root.destroy()

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
        
        self.icon_play = self.create_button_icon("play", self.colors["icon_color"])
        self.icon_settings = self.create_button_icon("settings", self.colors["icon_color"])
        self.icon_settings_disabled = self.create_button_icon("settings", "#CCCCCC")
        self.icon_stats = self.create_button_icon("stats", self.colors["icon_color"])
        
        self.settings_button.config(image=self.icon_settings)
        self.stats_button.config(image=self.icon_stats)
        self.update_start_button_color()
        
        self.draw_timer()

if __name__ == "__main__":
    root = tk.Tk()
    app = GodModeApp(root)
    root.mainloop()