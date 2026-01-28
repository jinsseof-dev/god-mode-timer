import tkinter as tk
from utils import export_csv, get_side_position, show_toast

def open_settings_window(app):
    """설정 창을 엽니다."""
    sf = app.scale_factor
    sw = tk.Toplevel(app.root)
    sw.title(app.loc.get("settings_window_title"))
    w = int(640 * sf)
    h = int(420 * sf)
    sw.geometry(f"{w}x{h}")
    sw.resizable(True, True)
    sw.minsize(400, 300)
    sw.configure(bg=app.colors["bg"])
    sw.transient(app.root)
    sw.grab_set()
    
    # 화면 중앙 배치 -> 우측 배치 (가림 방지)
    if app.settings_window_x is not None and app.settings_window_y is not None:
        sw.geometry(f"+{app.settings_window_x}+{app.settings_window_y}")
    else:
        sw.geometry(get_side_position(app.root, w, h))

    lbl_font = ("Helvetica", int(9 * sf))
    group_font = ("Helvetica", int(9 * sf), "bold")
    bg_color = app.colors["bg"]
    fg_color = app.colors["fg"]
    
    # 초기값 저장 (변경 사항 확인 및 취소 시 복구용)
    initial_settings = {
        "work_min": app.setting_work_min,
        "short_break_min": app.setting_short_break_min,
        "long_break_min": app.setting_long_break_min,
        "long_break_interval": app.setting_long_break_interval,
        "auto_start": app.setting_auto_start,
        "sound": app.setting_sound,
        "strict_mode": app.setting_strict_mode,
        "always_on_top": app.setting_always_on_top,
        "show_task_input": app.setting_show_task_input,
        "opacity": app.setting_opacity,
        "ui_scale": app.setting_ui_scale,
        "theme": app.setting_theme,
        "language": app.setting_language
    }

    # 하단 버튼 영역 (레이아웃 순서 보장을 위해 먼저 배치)
    btn_frame = tk.Frame(sw, bg=bg_color)

    # 버전 정보 표시 (테마 업데이트 함수보다 먼저 정의해야 함)
    version_label = tk.Label(btn_frame, text=app.loc.get("version_fmt", version=app.app_version), font=("Helvetica", int(8*sf)), bg=bg_color, fg=app.colors["fg_sub"])

    btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=int(20*sf), pady=int(20*sf))

    # 메인 컨테이너 (여백 확보)
    main_frame = tk.Frame(sw, bg=bg_color)
    main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=int(15*sf), pady=int(15*sf))

    # 좌우 분할 프레임 생성
    left_col = tk.Frame(main_frame, bg=bg_color)
    left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, int(10*sf)))
    
    right_col = tk.Frame(main_frame, bg=bg_color)
    right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(int(10*sf), 0))

    # 1. 타이머 설정 그룹 (왼쪽 상단)
    grp_timer = tk.LabelFrame(left_col, text=app.loc.get("timer_settings_group"), font=group_font, bg=bg_color, fg=fg_color, bd=1, relief="groove")
    grp_timer.pack(fill=tk.X, pady=(0, int(15*sf)), ipady=int(5*sf))

    def create_row(parent, label_text, default_val, row):
        tk.Label(parent, text=label_text, font=lbl_font, bg=bg_color, fg=fg_color).grid(row=row, column=0, padx=int(15*sf), pady=int(5*sf), sticky="w")
        var = tk.IntVar(value=default_val)
        spin = tk.Spinbox(parent, from_=1, to=180, textvariable=var, width=5, font=lbl_font, justify="center", bg=app.colors["btn_bg"], fg=fg_color)
        spin.grid(row=row, column=1, padx=int(15*sf), pady=int(5*sf), sticky="e")
        parent.grid_columnconfigure(1, weight=1)
        return var

    var_work = create_row(grp_timer, app.loc.get("work_time_min"), app.setting_work_min, 0)
    var_short = create_row(grp_timer, app.loc.get("short_break_min"), app.setting_short_break_min, 1)
    var_long = create_row(grp_timer, app.loc.get("long_break_min"), app.setting_long_break_min, 2)
    var_interval = create_row(grp_timer, app.loc.get("long_break_interval_count"), app.setting_long_break_interval, 3)

    # 2. 동작 설정 그룹 (왼쪽 하단)
    grp_behavior = tk.LabelFrame(left_col, text=app.loc.get("behavior_settings_group"), font=group_font, bg=bg_color, fg=fg_color, bd=1, relief="groove")
    grp_behavior.pack(fill=tk.X, pady=(0, 0), ipady=int(5*sf))

    def create_chk(parent, text, var):
        chk = tk.Checkbutton(parent, text=text, variable=var, font=lbl_font, bg=bg_color, fg=fg_color, 
                             activebackground=bg_color, activeforeground=fg_color, selectcolor=bg_color, 
                             highlightthickness=0, bd=0)
        chk.pack(anchor="w", padx=int(15*sf), pady=int(2*sf))
        return chk

    var_auto = tk.BooleanVar(value=app.setting_auto_start)
    create_chk(grp_behavior, app.loc.get("auto_start_timer"), var_auto)

    var_sound = tk.BooleanVar(value=app.setting_sound)
    create_chk(grp_behavior, app.loc.get("enable_sound"), var_sound)

    var_strict = tk.BooleanVar(value=app.setting_strict_mode)
    create_chk(grp_behavior, app.loc.get("strict_mode_desc"), var_strict)

    # 3. 화면 설정 그룹 (오른쪽 전체)
    grp_display = tk.LabelFrame(right_col, text=app.loc.get("display_settings_group"), font=group_font, bg=bg_color, fg=fg_color, bd=1, relief="groove")
    grp_display.pack(fill=tk.BOTH, expand=True, pady=(0, 0), ipady=int(5*sf))

    # 언어 선택 (Language)
    tk.Label(grp_display, text=app.loc.get("language_label"), font=lbl_font, bg=bg_color, fg=fg_color).pack(anchor="w", padx=int(15*sf), pady=(int(5*sf), 0))
    
    lang_frame = tk.Frame(grp_display, bg=bg_color)
    lang_frame.pack(fill=tk.X, padx=int(15*sf), pady=(0, int(5*sf)))
    
    var_lang = tk.StringVar(value=app.setting_language)
    
    btn_ko = tk.Button(lang_frame, text=app.loc.get("lang_ko"), font=lbl_font, bd=0, padx=int(10*sf), pady=int(6*sf))
    btn_ko.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, int(2*sf)))
    
    btn_en = tk.Button(lang_frame, text=app.loc.get("lang_en"), font=lbl_font, bd=0, padx=int(10*sf), pady=int(6*sf))
    btn_en.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(int(3*sf), int(3*sf)))

    btn_ja = tk.Button(lang_frame, text=app.loc.get("lang_ja"), font=lbl_font, bd=0, padx=int(10*sf), pady=int(6*sf))
    btn_ja.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(int(2*sf), 0))

    def update_lang_radio_style():
        val = var_lang.get()
        # 모든 버튼을 기본 스타일로 초기화
        btn_ko.configure(bg=app.colors["btn_bg"], fg=app.colors["fg_sub"])
        btn_en.configure(bg=app.colors["btn_bg"], fg=app.colors["fg_sub"])
        btn_ja.configure(bg=app.colors["btn_bg"], fg=app.colors["fg_sub"])
        
        # 선택된 버튼만 활성 스타일로 변경
        if val == "ko":
            btn_ko.configure(bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"])
        elif val == "en":
            btn_en.configure(bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"])
        elif val == "ja":
            btn_ja.configure(bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"])
            
    update_lang_radio_style()
    
    def set_lang(val):
        var_lang.set(val)
        update_lang_radio_style()
        
    btn_ko.configure(command=lambda: set_lang("ko"))
    btn_en.configure(command=lambda: set_lang("en"))
    btn_ja.configure(command=lambda: set_lang("ja"))

    # 테마 선택
    tk.Label(grp_display, text=app.loc.get("theme_label"), font=lbl_font, bg=bg_color, fg=fg_color).pack(anchor="w", padx=int(15*sf), pady=(int(5*sf), 0))
    
    theme_frame = tk.Frame(grp_display, bg=bg_color)
    theme_frame.pack(fill=tk.X, padx=int(15*sf), pady=(0, int(5*sf)))
    
    var_theme = tk.StringVar(value=app.setting_theme)
    
    # 테마 선택 버튼 (커스텀 라디오 버튼)
    btn_light = tk.Button(theme_frame, text=app.loc.get("theme_light"), font=lbl_font, bd=0, padx=int(10*sf), pady=int(6*sf))
    btn_light.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, int(5*sf)))
    
    btn_dark = tk.Button(theme_frame, text=app.loc.get("theme_dark"), font=lbl_font, bd=0, padx=int(10*sf), pady=int(6*sf))
    btn_dark.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(int(5*sf), 0))

    def update_radio_style():
        val = var_theme.get()
        if val == "Light":
            btn_light.configure(bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"])
            btn_dark.configure(bg=app.colors["btn_bg"], fg=app.colors["fg_sub"])
        else:
            btn_light.configure(bg=app.colors["btn_bg"], fg=app.colors["fg_sub"])
            btn_dark.configure(bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"])

    update_radio_style()

    def update_theme_preview():
        selected_theme = var_theme.get()
        
        def refresh_ui():
            new_colors = app.colors
            
            # Update Settings Window Backgrounds
            sw.configure(bg=new_colors["bg"])
            main_frame.configure(bg=new_colors["bg"])
            btn_frame.configure(bg=new_colors["bg"])
            
            def update_recursive(w):
                try:
                    if isinstance(w, (tk.LabelFrame, tk.Frame)):
                        w.configure(bg=new_colors["bg"])
                        if isinstance(w, tk.LabelFrame):
                            w.configure(fg=new_colors["fg"])
                    elif isinstance(w, tk.Label):
                        if w is version_label:
                            w.configure(bg=new_colors["bg"], fg=new_colors["fg_sub"])
                        else:
                            w.configure(bg=new_colors["bg"], fg=new_colors["fg"])
                    elif isinstance(w, tk.Checkbutton):
                        w.configure(bg=new_colors["bg"], fg=new_colors["fg"],
                                    activebackground=new_colors["bg"], activeforeground=new_colors["fg"],
                                    selectcolor=new_colors["bg"])
                    elif isinstance(w, tk.Radiobutton):
                        w.configure(bg=new_colors["bg"], fg=new_colors["fg"],
                                    activebackground=new_colors["bg"], activeforeground=new_colors["fg"],
                                    selectcolor=new_colors["bg"])
                    elif isinstance(w, tk.Spinbox):
                        w.configure(bg=new_colors["btn_bg"], fg=new_colors["fg"])
                    elif isinstance(w, tk.Scale):
                        w.configure(fg=new_colors["fg"], troughcolor="#C0C0C0")
                except:
                    pass
                for child in w.winfo_children():
                    update_recursive(child)
            
            update_recursive(main_frame)
            update_recursive(btn_frame)
            
            save_btn.configure(bg=new_colors["start_btn_bg"], fg=new_colors["btn_fg"])
            restore_btn.configure(bg=new_colors["btn_bg"], fg=new_colors["btn_fg"])
            export_btn.configure(bg=new_colors["btn_bg"], fg=new_colors["btn_fg"])
            update_radio_style()

        app.transition_theme(selected_theme, refresh_ui)

    def set_theme(val):
        var_theme.set(val)
        update_theme_preview()

    btn_light.configure(command=lambda: set_theme("Light"))
    btn_dark.configure(command=lambda: set_theme("Dark"))

    var_top = tk.BooleanVar(value=app.setting_always_on_top)
    create_chk(grp_display, app.loc.get("always_on_top"), var_top)

    var_task_input = tk.BooleanVar(value=app.setting_show_task_input)
    create_chk(grp_display, app.loc.get("show_task_input"), var_task_input)
    
    # 투명도 조절 프레임 (슬라이더 + 수치 표시)
    frame_opacity = tk.Frame(grp_display, bg=bg_color)
    frame_opacity.pack(fill=tk.X, padx=int(15*sf), pady=int(5*sf))
    
    tk.Label(frame_opacity, text=app.loc.get("opacity_label"), font=lbl_font, bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
    
    var_opacity = tk.DoubleVar(value=app.setting_opacity)
    lbl_opacity_val = tk.Label(frame_opacity, text=f"{int(app.setting_opacity * 100)}%", font=("Helvetica", int(8*sf)), bg=bg_color, fg=fg_color, width=4)
    lbl_opacity_val.pack(side=tk.RIGHT, padx=(int(5*sf), 0))
    
    def on_opacity_change(val):
        app.setting_opacity = float(val)
        app.update_opacity()
        lbl_opacity_val.config(text=f"{int(app.setting_opacity * 100)}%")

    scale_opacity = tk.Scale(frame_opacity, from_=0.2, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, 
                             variable=var_opacity, 
                             bg="#FF0000", fg=fg_color, 
                             highlightthickness=0, bd=0, 
                             showvalue=0,           # 숫자 숨김 (세련된 디자인)
                             width=int(10*sf),              # 트랙 두께
                             sliderlength=int(15*sf),       # 핸들 크기
                             sliderrelief="flat",   # 핸들 테두리 제거
                             troughcolor="#C0C0C0", # 트랙 색상
                             activebackground="#CC0000", # 클릭 시 색상
                             length=int(100*sf), 
                             command=on_opacity_change)
    scale_opacity.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=int(10*sf))

    # UI 크기 조절 슬라이더
    frame_ui_scale = tk.Frame(grp_display, bg=bg_color)
    frame_ui_scale.pack(fill=tk.X, padx=int(15*sf), pady=int(5*sf))
    
    tk.Label(frame_ui_scale, text=app.loc.get("ui_scale_label"), font=lbl_font, bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
    
    var_ui_scale = tk.IntVar(value=app.setting_ui_scale)
    lbl_ui_scale_val = tk.Label(frame_ui_scale, text=f"{app.setting_ui_scale}%", font=("Helvetica", int(8*sf)), bg=bg_color, fg=fg_color, width=4)
    lbl_ui_scale_val.pack(side=tk.RIGHT, padx=(int(5*sf), 0))
    
    def on_ui_scale_change(val):
        lbl_ui_scale_val.config(text=f"{int(float(val))}%")
        app.setting_ui_scale = int(float(val))
        app.update_scale_factor()
        
        # 통계 창이 열려있다면 내부 UI만 업데이트
        if hasattr(app, 'stats_window') and app.stats_window and app.stats_window.winfo_exists():
            if hasattr(app.stats_window, 'refresh_internal_ui_scale'):
                app.stats_window.refresh_internal_ui_scale()

        # 설정 창 내부 UI 요소(폰트) 크기 업데이트 (창 크기는 유지)
        new_sf = app.scale_factor
        new_lbl_font = ("Helvetica", int(9 * new_sf))
        new_group_font = ("Helvetica", int(9 * new_sf), "bold")
        new_small_font = ("Helvetica", int(8 * new_sf))
        
        def update_fonts(w):
            try:
                if isinstance(w, (tk.Label, tk.Button, tk.Checkbutton, tk.Radiobutton, tk.Spinbox)):
                    if w is version_label or w is lbl_opacity_val or w is lbl_ui_scale_val:
                        w.configure(font=new_small_font)
                    elif isinstance(w, tk.Button) and w['text'] == app.loc.get("save_btn"):
                         w.configure(font=("Helvetica", int(9 * new_sf), "bold"))
                    else:
                        w.configure(font=new_lbl_font)
                elif isinstance(w, tk.LabelFrame):
                    w.configure(font=new_group_font)
            except: pass
            for child in w.winfo_children():
                update_fonts(child)
        update_fonts(sw)

    scale_ui = tk.Scale(frame_ui_scale, from_=50, to=200, resolution=10, orient=tk.HORIZONTAL, 
                             variable=var_ui_scale, 
                             bg="#FF0000", fg=fg_color, 
                             highlightthickness=0, bd=0, showvalue=0,
                             width=int(10*sf), sliderlength=int(15*sf), sliderrelief="flat",
                             troughcolor="#C0C0C0", activebackground="#CC0000",
                             length=int(100*sf), command=on_ui_scale_change)
    scale_ui.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=int(10*sf))
    
    def restore_defaults():
        popup = tk.Toplevel(sw)
        popup.title(app.loc.get("restore_defaults_title"))
        w_pop = int(360 * app.scale_factor)
        h_pop = int(160 * app.scale_factor)
        popup.geometry(f"{w_pop}x{h_pop}")
        popup.resizable(False, False)
        popup.configure(bg=app.colors["bg"])
        popup.transient(sw)
        popup.grab_set()
        popup.focus_set()
        
        # 화면 중앙 배치
        x = sw.winfo_x() + (sw.winfo_width() // 2) - (w_pop // 2)
        y = sw.winfo_y() + (sw.winfo_height() // 2) - (h_pop // 2)
        popup.geometry(f"+{x}+{y}")

        container = tk.Frame(popup, bg=app.colors["bg"])
        container.pack(expand=True)

        tk.Label(container, text=app.loc.get("restore_defaults_msg"), font=("Helvetica", int(10*sf)), bg=app.colors["bg"], fg=app.colors["fg"]).pack(pady=(0, int(20*sf)))

        btn_frame = tk.Frame(container, bg=app.colors["bg"])
        btn_frame.pack()

        def do_restore():
            popup.destroy()
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
            var_ui_scale.set(100)
            var_theme.set("Light")
            var_lang.set("ko")
            
            # 투명도 즉시 적용 (미리보기)
            on_ui_scale_change(100)
            on_opacity_change(1.0)
            update_theme_preview()
            update_lang_radio_style()
            
            show_toast(app.loc.get("reset_settings_title"), app.loc.get("reset_settings_msg"))

        btn_yes = tk.Button(btn_frame, text=app.loc.get("restore_btn"), font=("Helvetica", int(9*sf), "bold"), bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"], bd=0, padx=15, pady=5, command=do_restore)
        btn_yes.pack(side=tk.LEFT, padx=5)
        btn_yes.bind("<Enter>", lambda e: btn_yes.config(bg=app.colors["start_btn_hover"]))
        btn_yes.bind("<Leave>", lambda e: btn_yes.config(bg=app.colors["start_btn_bg"]))

        tk.Button(btn_frame, text=app.loc.get("cancel"), font=("Helvetica", int(9*sf)), bg="#E0E0E0", fg="#555555", bd=0, padx=15, pady=5, command=popup.destroy).pack(side=tk.LEFT, padx=5)
        
        popup.bind('<Return>', lambda e: do_restore())

    def has_changes():
        return (var_work.get() != initial_settings["work_min"] or
                var_short.get() != initial_settings["short_break_min"] or
                var_long.get() != initial_settings["long_break_min"] or
                var_interval.get() != initial_settings["long_break_interval"] or
                var_auto.get() != initial_settings["auto_start"] or
                var_sound.get() != initial_settings["sound"] or
                var_strict.get() != initial_settings["strict_mode"] or
                var_top.get() != initial_settings["always_on_top"] or
                var_task_input.get() != initial_settings["show_task_input"] or
                abs(var_opacity.get() - initial_settings["opacity"]) > 0.001 or
                var_ui_scale.get() != initial_settings["ui_scale"] or
                var_theme.get() != initial_settings["theme"] or
                var_lang.get() != initial_settings["language"])

    def close_without_saving():
        # 저장하지 않고 닫을 때, 투명도 미리보기 복구
        if abs(app.setting_opacity - initial_settings["opacity"]) > 0.001:
            app.setting_opacity = initial_settings["opacity"]
            app.update_opacity()
            
        # 테마 미리보기 복구
        if app.setting_theme != initial_settings["theme"]:
            app.setting_theme = initial_settings["theme"]
            app.update_theme_colors()
            app.apply_theme()
            
        # UI 스케일 미리보기 복구
        if app.setting_ui_scale != initial_settings["ui_scale"]:
            app.setting_ui_scale = initial_settings["ui_scale"]
            app.apply_ui_scale()

        app.settings_window_x = sw.winfo_x()
        app.settings_window_y = sw.winfo_y()
        sw.destroy()

    def show_save_popup():
        popup = tk.Toplevel(sw)
        popup.title(app.loc.get("save_settings_title"))
        w_pop = int(360 * app.scale_factor)
        h_pop = int(160 * app.scale_factor)
        popup.geometry(f"{w_pop}x{h_pop}")
        popup.resizable(False, False)
        popup.configure(bg=app.colors["bg"])
        popup.transient(sw)
        popup.grab_set()
        popup.focus_set()
        
        # 화면 중앙 배치
        x = sw.winfo_x() + (sw.winfo_width() // 2) - (w_pop // 2)
        y = sw.winfo_y() + (sw.winfo_height() // 2) - (h_pop // 2)
        popup.geometry(f"+{x}+{y}")

        container = tk.Frame(popup, bg=app.colors["bg"])
        container.pack(expand=True)

        tk.Label(container, text=app.loc.get("save_changes_msg"), font=("Helvetica", int(10*sf)), bg=app.colors["bg"], fg=app.colors["fg"]).pack(pady=(0, int(20*sf)))

        btn_frame = tk.Frame(container, bg=app.colors["bg"])
        btn_frame.pack()

        def do_save():
            popup.destroy()
            save_settings()

        def do_dont_save():
            popup.destroy()
            close_without_saving()

        # 버튼 생성 (저장, 저장 안 함, 취소)
        btn_save = tk.Button(btn_frame, text=app.loc.get("save_btn"), font=("Helvetica", int(9*sf), "bold"), bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"], bd=0, padx=int(15*sf), pady=int(5*sf), command=do_save)
        btn_save.pack(side=tk.LEFT, padx=int(5*sf))
        btn_save.bind("<Enter>", lambda e: btn_save.config(bg=app.colors["start_btn_hover"]))
        btn_save.bind("<Leave>", lambda e: btn_save.config(bg=app.colors["start_btn_bg"]))

        btn_no = tk.Button(btn_frame, text=app.loc.get("dont_save_btn"), font=("Helvetica", int(9*sf)), bg=app.colors["btn_bg"], fg=app.colors["btn_fg"], bd=0, padx=int(15*sf), pady=int(5*sf), command=do_dont_save)
        btn_no.pack(side=tk.LEFT, padx=int(5*sf))
        btn_no.bind("<Enter>", lambda e: btn_no.config(bg=app.colors["btn_hover"]))
        btn_no.bind("<Leave>", lambda e: btn_no.config(bg=app.colors["btn_bg"]))

        tk.Button(btn_frame, text=app.loc.get("cancel"), font=("Helvetica", int(9*sf)), bg="#E0E0E0", fg="#555555", bd=0, padx=int(15*sf), pady=int(5*sf), command=popup.destroy).pack(side=tk.LEFT, padx=int(5*sf))
        
        popup.bind('<Return>', lambda e: do_save())

    def on_close():
        if has_changes():
            show_save_popup()
        else:
            close_without_saving()
            
    sw.protocol("WM_DELETE_WINDOW", on_close)

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
        app.setting_ui_scale = var_ui_scale.get()
        app.setting_theme = var_theme.get()
        
        # 언어 변경 처리 (로직 간소화)
        new_lang = var_lang.get()
        lang_changed = app.setting_language != new_lang
        if lang_changed:
            app.setting_language = new_lang
            app.loc.load_language(new_lang)
        
        app.settings_window_x = sw.winfo_x()
        app.settings_window_y = sw.winfo_y()

        app.apply_ui_scale()
        app.save_settings_to_file()
        app.update_task_input_visibility()
        app.update_opacity()
        app.update_theme_colors()
        app.apply_theme()

        app.reset_timer()

        if lang_changed:
            app.refresh_language()

        show_toast(app.loc.get("save_settings_toast_title"), app.loc.get("save_settings_toast_msg"))
        sw.destroy()

    # 저장 버튼 (우측 끝)
    save_btn = tk.Button(btn_frame, text=app.loc.get("save_btn"), font=("Helvetica", int(9*sf), "bold"), bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"], bd=0, padx=int(15*sf), pady=int(6*sf), command=save_settings)
    save_btn.pack(side=tk.RIGHT, padx=(int(5*sf), 0))
    save_btn.bind("<Enter>", lambda e: save_btn.config(bg=app.colors["start_btn_hover"]))
    save_btn.bind("<Leave>", lambda e: save_btn.config(bg=app.colors["start_btn_bg"]))

    # CSV 내보내기 버튼
    export_btn = tk.Button(btn_frame, text=app.loc.get("csv_export"), font=("Helvetica", int(9*sf)), bg=app.colors["btn_bg"], fg=app.colors["btn_fg"], bd=0, padx=int(10*sf), pady=int(6*sf), command=lambda: export_csv(sw, app.loc))
    export_btn.pack(side=tk.RIGHT, padx=(int(5*sf), 0))
    export_btn.bind("<Enter>", lambda e: export_btn.config(bg="#FFE0B2"))
    export_btn.bind("<Leave>", lambda e: export_btn.config(bg=app.colors["btn_bg"]))

    # 기본값 복원 버튼
    restore_btn = tk.Button(btn_frame, text=app.loc.get("restore_defaults_btn"), font=("Helvetica", int(9*sf)), bg=app.colors["btn_bg"], fg=app.colors["btn_fg"], bd=0, padx=int(10*sf), pady=int(6*sf), command=restore_defaults)
    restore_btn.pack(side=tk.RIGHT, padx=(0, 0))
    restore_btn.bind("<Enter>", lambda e: restore_btn.config(bg="#FFE0B2"))
    restore_btn.bind("<Leave>", lambda e: restore_btn.config(bg=app.colors["btn_bg"]))

    # 버전 레이블 배치
    version_label.pack(side=tk.LEFT, padx=(int(5*sf), 0))