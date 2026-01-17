import tkinter as tk
from tkinter import messagebox
from utils import export_csv, get_side_position

def open_settings_window(app):
    """설정 창을 엽니다."""
    sw = tk.Toplevel(app.root)
    sw.title("설정")
    sw.geometry("320x400")
    sw.resizable(False, False)
    sw.configure(bg=app.colors["bg"])
    sw.transient(app.root)
    sw.grab_set()
    
    # 화면 중앙 배치 -> 우측 배치 (가림 방지)
    sw.geometry(get_side_position(app.root, 320, 400))

    lbl_font = ("Helvetica", 10)
    bg_color = app.colors["bg"]
    fg_color = app.colors["fg"]
    
    def create_row(label_text, default_val, row):
        tk.Label(sw, text=label_text, font=lbl_font, bg=bg_color, fg=fg_color).grid(row=row, column=0, padx=20, pady=5, sticky="w")
        var = tk.IntVar(value=default_val)
        spin = tk.Spinbox(sw, from_=1, to=180, textvariable=var, width=5, font=lbl_font)
        spin.grid(row=row, column=1, padx=20, pady=5)
        return var

    var_work = create_row("집중 시간 (분)", app.setting_work_min, 0)
    var_short = create_row("짧은 휴식 (분)", app.setting_short_break_min, 1)
    var_long = create_row("긴 휴식 (분)", app.setting_long_break_min, 2)
    var_interval = create_row("긴 휴식 간격 (회)", app.setting_long_break_interval, 3)

    var_top = tk.BooleanVar(value=app.setting_always_on_top)
    chk_top = tk.Checkbutton(sw, text="항상 위에 표시", variable=var_top, font=lbl_font, bg=bg_color, fg=fg_color, activebackground=bg_color, activeforeground=fg_color, selectcolor=bg_color, highlightthickness=0, bd=0)
    chk_top.grid(row=4, column=0, columnspan=2, padx=20, pady=5, sticky="w")

    var_auto = tk.BooleanVar(value=app.setting_auto_start)
    chk_auto = tk.Checkbutton(sw, text="타이머 자동 시작", variable=var_auto, font=lbl_font, bg=bg_color, fg=fg_color, activebackground=bg_color, activeforeground=fg_color, selectcolor=bg_color, highlightthickness=0, bd=0)
    chk_auto.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="w")

    var_sound = tk.BooleanVar(value=app.setting_sound)
    chk_sound = tk.Checkbutton(sw, text="알림음 켜기", variable=var_sound, font=lbl_font, bg=bg_color, fg=fg_color, activebackground=bg_color, activeforeground=fg_color, selectcolor=bg_color, highlightthickness=0, bd=0)
    chk_sound.grid(row=6, column=0, columnspan=2, padx=20, pady=5, sticky="w")
    
    var_task_input = tk.BooleanVar(value=app.setting_show_task_input)
    chk_task_input = tk.Checkbutton(sw, text="할 일 입력창 표시", variable=var_task_input, font=lbl_font, bg=bg_color, fg=fg_color, activebackground=bg_color, activeforeground=fg_color, selectcolor=bg_color, highlightthickness=0, bd=0)
    chk_task_input.grid(row=7, column=0, columnspan=2, padx=20, pady=5, sticky="w")

    var_strict = tk.BooleanVar(value=app.setting_strict_mode)
    chk_strict = tk.Checkbutton(sw, text="엄격 모드 (중도 포기 불가)", variable=var_strict, font=lbl_font, bg=bg_color, fg=fg_color, activebackground=bg_color, activeforeground=fg_color, selectcolor=bg_color, highlightthickness=0, bd=0)
    chk_strict.grid(row=8, column=0, columnspan=2, padx=20, pady=5, sticky="w")

    tk.Label(sw, text="투명도", font=lbl_font, bg=bg_color, fg=fg_color).grid(row=9, column=0, padx=20, pady=5, sticky="w")
    
    # 투명도 조절 프레임 (슬라이더 + 수치 표시)
    frame_opacity = tk.Frame(sw, bg=bg_color)
    frame_opacity.grid(row=9, column=1, padx=20, pady=5, sticky="w")
    
    var_opacity = tk.DoubleVar(value=app.setting_opacity)
    lbl_opacity_val = tk.Label(frame_opacity, text=f"{int(app.setting_opacity * 100)}%", font=("Helvetica", 9), bg=bg_color, fg=fg_color, width=4)
    lbl_opacity_val.pack(side=tk.RIGHT, padx=(5, 0))
    
    def on_opacity_change(val):
        app.setting_opacity = float(val)
        app.update_opacity()
        lbl_opacity_val.config(text=f"{int(app.setting_opacity * 100)}%")

    scale_opacity = tk.Scale(frame_opacity, from_=0.2, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, 
                             variable=var_opacity, 
                             bg=bg_color, fg=fg_color, 
                             highlightthickness=0, bd=0, 
                             showvalue=0,           # 숫자 숨김 (세련된 디자인)
                             width=10,              # 트랙 두께
                             sliderlength=15,       # 핸들 크기
                             sliderrelief="flat",   # 핸들 테두리 제거
                             troughcolor="#E0E0E0", # 트랙 색상
                             activebackground=app.colors["btn_hover"], # 클릭 시 색상
                             length=100, 
                             command=on_opacity_change)
    scale_opacity.pack(side=tk.LEFT)
    
    def restore_defaults():
        if messagebox.askyesno("기본값 복원", "모든 설정을 기본값으로 되돌리시겠습니까?", parent=sw):
            var_work.set(25)
            var_short.set(5)
            var_long.set(15)
            var_interval.set(4)
            var_top.set(True)
            var_auto.set(False)
            var_sound.set(True)
            var_task_input.set(False)
            var_strict.set(False)
            var_opacity.set(1.0)

    def save_settings():
        app.setting_work_min = int(var_work.get())
        app.setting_short_break_min = int(var_short.get())
        app.setting_long_break_min = int(var_long.get())
        app.setting_long_break_interval = int(var_interval.get())
        
        app.setting_always_on_top = var_top.get()
        app.update_topmost_status()

        app.setting_auto_start = var_auto.get()
        app.setting_sound = var_sound.get()
        app.setting_show_task_input = var_task_input.get()
        app.setting_strict_mode = var_strict.get()
        app.setting_opacity = var_opacity.get()
        
        app.save_settings_to_file()
        app.update_task_input_visibility()
        app.update_opacity()

        app.reset_timer()
        sw.destroy()

    save_btn = tk.Button(sw, text="저장", font=("Helvetica", 10, "bold"), bg="#FFDAC1", fg="#555555", bd=0, padx=20, pady=5, command=save_settings)
    save_btn.grid(row=10, column=0, columnspan=2, pady=(15, 5))

    restore_btn = tk.Button(sw, text="기본값 복원", font=("Helvetica", 9), bg="#E0E0E0", fg="#555555", bd=0, padx=10, pady=5, command=restore_defaults)
    restore_btn.grid(row=11, column=0, columnspan=2, pady=(0, 5))

    export_btn = tk.Button(sw, text="CSV 내보내기", font=("Helvetica", 9), bg="#E0E0E0", fg="#555555", bd=0, padx=10, pady=5, command=lambda: export_csv(sw))
    export_btn.grid(row=12, column=0, columnspan=2, pady=(0, 15))