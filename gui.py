import tkinter as tk
from tkinter import messagebox
from utils import play_sound, log_pomodoro, show_toast, play_tick_sound
import time
import math
import sys
import ctypes
import re
from PIL import Image, ImageDraw, ImageFont, ImageTk
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

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class WindowsTaskbar:
    def __init__(self, root):
        self.root = root
        self.ptr = None
        if sys.platform != "win32":
            return
        
        try:
            from ctypes import wintypes
            ctypes.windll.ole32.CoInitialize(0)
            
            # CLSID_TaskbarList = {56FDF344-FD6D-11d0-958A-006097C9A090}
            CLSID_TaskbarList = (ctypes.c_ubyte * 16)(0x44, 0xF3, 0xFD, 0x56, 0x6D, 0xFD, 0xD0, 0x11, 0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90)
            # IID_ITaskbarList3 = {ea1afb91-9e28-4b86-90e9-9e9f8a5eefaf}
            IID_ITaskbarList3 = (ctypes.c_ubyte * 16)(0x91, 0xfb, 0x1a, 0xea, 0x28, 0x9e, 0x86, 0x4b, 0x90, 0xe9, 0x9e, 0x9f, 0x8a, 0x5e, 0xef, 0xaf)
            
            self.ptr = ctypes.c_void_p()
            ret = ctypes.windll.ole32.CoCreateInstance(
                ctypes.byref(CLSID_TaskbarList), 0, 1, ctypes.byref(IID_ITaskbarList3), ctypes.byref(self.ptr)
            )
            
            if ret == 0 and self.ptr:
                # VTable 접근
                self.lpVtbl = ctypes.cast(self.ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))
                # HrInit (Index 3)
                HrInit = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(self.lpVtbl.contents[3])
                HrInit(self.ptr)
        except Exception:
            self.ptr = None

    def set_progress(self, current, total):
        if not self.ptr or sys.platform != "win32": return
        try:
            from ctypes import wintypes
            hwnd = self.root.winfo_id()
            parent = ctypes.windll.user32.GetParent(hwnd)
            if parent: hwnd = parent
            
            # SetProgressValue (Index 9)
            SetProgressValue = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_ulonglong, ctypes.c_ulonglong)(self.lpVtbl.contents[9])
            SetProgressValue(self.ptr, hwnd, int(current), int(total))
            
            # SetProgressState (Index 10), 2 = Normal (Green)
            SetProgressState = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_int)(self.lpVtbl.contents[10])
            SetProgressState(self.ptr, hwnd, 2)
        except Exception:
            pass

    def reset(self):
        if not self.ptr or sys.platform != "win32": return
        try:
            from ctypes import wintypes
            hwnd = self.root.winfo_id()
            parent = ctypes.windll.user32.GetParent(hwnd)
            if parent: hwnd = parent
            # SetProgressState (Index 10), 0 = NoProgress
            SetProgressState = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.HWND, ctypes.c_int)(self.lpVtbl.contents[10])
            SetProgressState(self.ptr, hwnd, 0)
        except Exception:
            pass

class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.geometry("360x400")
        self.root.resizable(True, True)
        self.root.minsize(300, 350)
        self.root.configure(bg="#FFF8F0")
        self.root.attributes('-topmost', True)

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
        
        self.work_time = self.setting_work_min * 60
        self.break_time = self.setting_short_break_min * 60
        self.current_time = self.work_time
        self.pomodoro_count = 0
        self.mode = "work"  # 'work' or 'break'

        # 타이머 표시 (도형)
        self.canvas = tk.Canvas(root, bg="#FFF8F0", highlightthickness=0)
        self.canvas.pack(pady=0, expand=True, fill=tk.BOTH)
        self.draw_timer()
        self.canvas.bind("<Configure>", lambda e: self.draw_timer())
        self.canvas.bind("<Button-1>", self.handle_mouse_input)
        self.canvas.bind("<B1-Motion>", self.handle_mouse_input)
        
        # 마우스 커서 변경
        self.canvas.bind("<Enter>", lambda e: self.root.config(cursor="hand2"))
        self.canvas.bind("<Leave>", lambda e: self.root.config(cursor=""))

        # 버튼 프레임
        self.btn_frame = tk.Frame(root, bg="#FFF8F0")
        self.btn_frame.pack(pady=(0, 5))

        self.start_button = tk.Button(self.btn_frame, text="▶", font=("Helvetica", 16), width=4, bd=0, bg="#FFDAC1", fg="#555555", pady=3, command=self.toggle_timer)
        self.start_button.pack(side=tk.LEFT, padx=10)
        self.start_button.bind("<Enter>", lambda e: self.start_button.config(bg="#FFC8A0"))
        self.start_button.bind("<Leave>", lambda e: self.update_start_button_color())

        self.settings_button = tk.Button(self.btn_frame, text="⚙", font=("Helvetica", 16), width=4, bd=0, bg="#F0F0F0", fg="#555555", pady=3, command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=10)
        self.settings_button.bind("<Enter>", lambda e: self.settings_button.config(bg="#E0E0E0") if self.settings_button['state'] != tk.DISABLED else None)
        self.settings_button.bind("<Leave>", lambda e: self.settings_button.config(bg="#F0F0F0") if self.settings_button['state'] != tk.DISABLED else None)

        # 아이콘 이미지 생성
        self.icon_play = self.create_button_icon("play", "#555555")
        self.icon_stop = self.create_button_icon("stop", "white")
        self.icon_settings = self.create_button_icon("settings", "#555555")
        self.icon_settings_disabled = self.create_button_icon("settings", "#CCCCCC")
        
        # 버튼에 이미지 적용 (초기 상태)
        self.start_button.config(image=self.icon_play, text="", width=50, height=40)
        self.settings_button.config(image=self.icon_settings, text="", width=50, height=40)

        self.tk_image = None

    def set_window_icon(self):
        # 윈도우 아이콘 동적 생성 (토마토 모양)
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Body
        draw.ellipse((4, 8, 60, 60), fill="#FF5252", outline="#D32F2F", width=2)
        # Leaf
        draw.polygon([(32, 4), (22, 15), (42, 15)], fill="#4CAF50", outline="#388E3C")
        
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
        
        # 투명 배경 대신 캔버스 배경색(#FFF8F0)으로 이미지 생성
        image = Image.new("RGBA", (img_w, img_h), "#FFF8F0")
        draw = ImageDraw.Draw(image)
        
        cx, cy = img_w / 2, img_h / 2
        radius = min(img_w, img_h) / 2 * 0.88
        arc_radius = radius * 0.7
        
        # 0. 배경 원
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill="#FFFFFF", outline="black", width=int(2*scale))
        
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
                tick_len = 10 * scale
                width = 2 * scale
                
                # 5분 단위 숫자 표시
                text_radius = radius - (20 * scale)
                tx = cx + text_radius * math.cos(angle_rad)
                ty = cy - text_radius * math.sin(angle_rad)
                text = str(i if i != 0 else 60)
                draw.text((tx, ty), text, font=font, fill="black", anchor="mm")
            else:
                tick_len = 5 * scale
                width = 1 * scale
                
            x_out = cx + radius * math.cos(angle_rad)
            y_out = cy - radius * math.sin(angle_rad)
            x_in = cx + (radius - tick_len) * math.cos(angle_rad)
            y_in = cy - (radius - tick_len) * math.sin(angle_rad)
            
            draw.line((x_in, y_in, x_out, y_out), fill="black", width=int(width))

        # 4. 중앙 디지털 시간 표시
        center_radius = radius * 0.175
        draw.ellipse((cx-center_radius, cy-center_radius, cx+center_radius, cy+center_radius), fill="#F0F0F0")
        
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
            
        draw.text((cx, cy), time_str, font=font_time, fill="#555555", anchor="mm")

        # 이미지 리사이즈 (안티앨리어싱) 및 캔버스에 표시
        image = image.resize((w, h), resample=Image.BILINEAR)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

        # 윈도우 타이틀 업데이트
        if self.is_running:
            new_title = f"{time_str} - Pomodoro Timer"
            if self.root.title() != new_title:
                self.root.title(new_title)
            
            # 작업 표시줄 진행률 업데이트
            total_time = self.work_time if self.mode == "work" else self.break_time
            self.taskbar.set_progress(self.current_time, total_time)
        elif self.root.title() != "Pomodoro Timer":
            self.root.title("Pomodoro Timer")
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
            log_pomodoro()
            self.pomodoro_count += 1
            self.mode = "break"
            
            # 4번 집중(4의 배수)마다 15분 긴 휴식
            if self.pomodoro_count > 0 and self.pomodoro_count % self.setting_long_break_interval == 0:
                self.break_time = self.setting_long_break_min * 60
                msg = f"{self.setting_long_break_interval}번의 집중({self.pomodoro_count}회) 완료! {self.setting_long_break_min}분간 긴 휴식을 취하세요."
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
            self.start_button.config(image=self.icon_stop, bg="#FF9AA2")
        else:
            self.start_button.config(image=self.icon_play, bg="#FFDAC1")

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

    def on_closing(self):
        if messagebox.askokcancel("종료", "정말 종료하시겠습니까?"):
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
        sw = tk.Toplevel(self.root)
        sw.title("설정")
        sw.geometry("280x420")
        sw.resizable(False, False)
        sw.configure(bg="#FFF8F0")
        sw.transient(self.root)
        sw.grab_set()
        
        # 화면 중앙 배치
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 140
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 160
        sw.geometry(f"+{x}+{y}")

        lbl_font = ("Helvetica", 10)
        bg_color = "#FFF8F0"
        
        def create_row(label_text, default_val, row):
            tk.Label(sw, text=label_text, font=lbl_font, bg=bg_color).grid(row=row, column=0, padx=20, pady=10, sticky="w")
            var = tk.IntVar(value=default_val)
            spin = tk.Spinbox(sw, from_=1, to=180, textvariable=var, width=5, font=lbl_font)
            spin.grid(row=row, column=1, padx=20, pady=10)
            return var

        var_work = create_row("집중 시간 (분)", self.setting_work_min, 0)
        var_short = create_row("짧은 휴식 (분)", self.setting_short_break_min, 1)
        var_long = create_row("긴 휴식 (분)", self.setting_long_break_min, 2)
        var_interval = create_row("긴 휴식 간격 (회)", self.setting_long_break_interval, 3)

        var_top = tk.BooleanVar(value=self.setting_always_on_top)
        chk_top = tk.Checkbutton(sw, text="항상 위에 표시", variable=var_top, font=lbl_font, bg=bg_color, fg="#555555", activebackground=bg_color, activeforeground="#555555", highlightthickness=0, bd=0)
        chk_top.grid(row=4, column=0, columnspan=2, padx=20, pady=10, sticky="w")

        var_auto = tk.BooleanVar(value=self.setting_auto_start)
        chk_auto = tk.Checkbutton(sw, text="타이머 자동 시작", variable=var_auto, font=lbl_font, bg=bg_color, fg="#555555", activebackground=bg_color, activeforeground="#555555", highlightthickness=0, bd=0)
        chk_auto.grid(row=5, column=0, columnspan=2, padx=20, pady=10, sticky="w")

        var_sound = tk.BooleanVar(value=self.setting_sound)
        chk_sound = tk.Checkbutton(sw, text="알림음 켜기", variable=var_sound, font=lbl_font, bg=bg_color, fg="#555555", activebackground=bg_color, activeforeground="#555555", highlightthickness=0, bd=0)
        chk_sound.grid(row=6, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        
        def save_settings():
            self.setting_work_min = int(var_work.get())
            self.setting_short_break_min = int(var_short.get())
            self.setting_long_break_min = int(var_long.get())
            self.setting_long_break_interval = int(var_interval.get())
            
            self.setting_always_on_top = var_top.get()
            self.root.attributes('-topmost', self.setting_always_on_top)

            self.setting_auto_start = var_auto.get()
            self.setting_sound = var_sound.get()

            self.reset_timer()
            sw.destroy()

        save_btn = tk.Button(sw, text="저장", font=("Helvetica", 10, "bold"), bg="#FFDAC1", fg="#555555", bd=0, padx=20, pady=5, command=save_settings)
        save_btn.grid(row=7, column=0, columnspan=2, pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()