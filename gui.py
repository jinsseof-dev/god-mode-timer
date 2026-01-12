import tkinter as tk
from tkinter import messagebox
from utils import play_sound, log_pomodoro, show_toast
import time
import math
import sys
import ctypes
import re

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
        self.root.title("Focus Timer")
        self.root.geometry("360x400")
        self.root.resizable(True, True)
        self.root.minsize(300, 350)
        self.root.configure(bg="#FFF8F0")
        self.root.attributes('-topmost', True)

        # 윈도우 작업 표시줄 진행률 초기화
        self.taskbar = WindowsTaskbar(root)

        # 윈도우 닫기 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 윈도우 자석 효과 (Snap to Edge)
        self.root.bind("<Configure>", self.snap_to_edge)

        # 상태 변수
        self.is_running = False
        self.work_time = 25 * 60
        self.break_time = 5 * 60
        self.current_time = self.work_time
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

        self.reset_button = tk.Button(self.btn_frame, text="↻", font=("Helvetica", 16), width=4, bd=0, bg="#E2F0CB", fg="#555555", pady=3, command=self.reset_timer)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        self.reset_button.bind("<Enter>", lambda e: self.reset_button.config(bg="#D0E8B0"))
        self.reset_button.bind("<Leave>", lambda e: self.reset_button.config(bg="#E2F0CB"))

    def draw_timer(self):
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1: w = 320
        if h <= 1: h = 320
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 * 0.88
        arc_radius = radius * 0.7
        
        # 0. 배경 원
        self.canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, fill="#FFFFFF", outline="#E0E0E0")
        
        # 1. 남은 시간 영역 그리기 (60분 스케일)
        display_time = min(self.current_time, 3600)
        angle = (display_time / 3600) * 360
        color = "#FFB7B2" if self.mode == "work" else "#B5EAD7"
        
        if display_time >= 3600:
            self.canvas.create_oval(cx-arc_radius, cy-arc_radius, cx+arc_radius, cy+arc_radius, fill=color, outline=color)
        elif display_time > 0:
            # 12시(90도)에서 시작, 시계방향(음수 extent)으로 그려짐
            self.canvas.create_arc(cx-arc_radius, cy-arc_radius, cx+arc_radius, cy+arc_radius, start=90, extent=-angle, fill=color, outline=color)

        # 2. 눈금 그리기 (0~60분)
        for i in range(60):
            angle_deg = 90 - (i * 6)
            angle_rad = math.radians(angle_deg)
            
            if i % 5 == 0:
                tick_len = 10
                width = 2
                
                # 5분 단위 숫자 표시
                text_radius = radius - 20
                tx = cx + text_radius * math.cos(angle_rad)
                ty = cy - text_radius * math.sin(angle_rad)
                font_size = max(8, int(radius * 0.07))
                self.canvas.create_text(tx, ty, text=str(i if i != 0 else 60), font=("Helvetica", font_size, "bold"), fill="#AAAAAA")
            else:
                tick_len = 5
                width = 1
                
            x_out = cx + radius * math.cos(angle_rad)
            y_out = cy - radius * math.sin(angle_rad)
            x_in = cx + (radius - tick_len) * math.cos(angle_rad)
            y_in = cy - (radius - tick_len) * math.sin(angle_rad)
            
            self.canvas.create_line(x_in, y_in, x_out, y_out, fill="#E0E0E0", width=width)
            
        # 3. 외곽선
        self.canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="#E0E0E0", width=2)

        # 4. 중앙 디지털 시간 표시
        # 테두리를 제거하고 깔끔한 흰색 원으로 변경
        center_radius = radius * 0.175
        self.canvas.create_oval(cx-center_radius, cy-center_radius, cx+center_radius, cy+center_radius, fill="#F0F0F0", outline="", width=0)
        mins, secs = divmod(int(self.current_time), 60)
        time_str = "{:02d}:{:02d}".format(mins, secs)
        font_size_time = max(10, int(radius * 0.09))
        self.canvas.create_text(cx, cy, text=time_str, font=("Helvetica", font_size_time, "bold"), fill="#555555")

        # 윈도우 타이틀 업데이트
        if self.is_running:
            new_title = f"{time_str} - Focus Timer"
            if self.root.title() != new_title:
                self.root.title(new_title)
            
            # 작업 표시줄 진행률 업데이트
            total_time = self.work_time if self.mode == "work" else self.break_time
            self.taskbar.set_progress(self.current_time, total_time)
        elif self.root.title() != "Focus Timer":
            self.root.title("Focus Timer")
            self.taskbar.reset()

    def toggle_timer(self):
        if self.is_running:
            self.is_running = False
            self.update_start_button_color()
            show_toast("일시 정지", "타이머가 일시 정지되었습니다.")
        else:
            self.is_running = True
            self.update_start_button_color()
            
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
        play_sound()
        
        if self.mode == "work":
            log_pomodoro()
            self.mode = "break"
            self.current_time = self.break_time
            show_toast("집중 완료", "집중 시간이 끝났습니다! 휴식 시간이 바로 시작됩니다.")
            
            # 휴식 시간 자동 시작
            self.is_running = True
            self.update_start_button_color()
            self.last_time = time.time()
            self.draw_timer()
            self.root.after(50, self.count_down)
        else:
            self.is_running = False
            self.update_start_button_color()
            self.mode = "work"
            self.current_time = self.work_time
            show_toast("휴식 완료", "휴식 시간이 끝났습니다! 다시 집중해볼까요?")
            self.draw_timer()
            messagebox.showinfo("알림", "휴식 시간이 끝났습니다! 다시 집중해볼까요?")

    def reset_timer(self):
        self.is_running = False
        self.update_start_button_color()
        self.mode = "work"
        self.current_time = self.work_time
        self.draw_timer()

    def update_start_button_color(self):
        if self.is_running:
            self.start_button.config(text="⏸", bg="#FF9AA2", fg="white")
        else:
            self.start_button.config(text="▶", bg="#FFDAC1", fg="#555555")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()