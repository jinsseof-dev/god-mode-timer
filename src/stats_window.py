import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta
from utils import export_csv, get_recent_logs, get_side_position, parse_logs
import traceback

def open_stats_window(app):
    """통계 창을 엽니다."""
    try:
        sw = tk.Toplevel(app.root)
        sw.title("갓생 지수 통계")
        w = app.stats_window_w if getattr(app, 'stats_window_w', None) else int(740 * app.scale_factor)
        h = app.stats_window_h if getattr(app, 'stats_window_h', None) else int(360 * app.scale_factor)
        sw.geometry(f"{w}x{h}")
        sw.resizable(True, True)
        sw.minsize(500, 250)
        sw.configure(bg=app.colors["bg"])
        sw.transient(app.root)
        app.stats_window = sw
        
        # 화면 중앙 배치 -> 우측 배치 (가림 방지)
        try:
            if app.stats_window_x is not None and app.stats_window_y is not None:
                sw.geometry(f"+{app.stats_window_x}+{app.stats_window_y}")
            else:
                sw.geometry(get_side_position(app.root, w, h))
        except Exception:
            sw.geometry(get_side_position(app.root, w, h))

        # 데이터 로드
        current_view_days = 30
        daily_stats = parse_logs(current_view_days)
        logs, has_more = get_recent_logs(current_view_days)

        # 메인 컨테이너 (좌우 분할)
        main_frame = tk.Frame(sw, bg=app.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 10))

        # === 좌측: 그래프 및 통계 ===
        left_frame = tk.Frame(main_frame, bg=app.colors["bg"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        label_title = tk.Label(left_frame, text="한달간 갓생 지수", font=("Helvetica", int(11*app.scale_factor), "bold"), bg=app.colors["bg"], fg=app.colors["fg"])
        label_title.pack(pady=(0, int(15*app.scale_factor)))

        # 캔버스
        canvas = tk.Canvas(left_frame, bg=app.colors["bg"], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # 최근 30일 데이터 준비
        dates = []
        counts = []
        max_count = 0
        today_str = datetime.now().strftime("%m/%d")
        
        for i in range(29, -1, -1):
            d = datetime.now() - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            dates.append(d.strftime("%m/%d"))
            stats = daily_stats.get(d_str, {'count': 0})
            c = stats['count']
            counts.append(c)
            if c > max_count: max_count = c
        
        if max_count == 0: max_count = 5

        # 막대 그래프 그리기
        def draw_graph(event=None):
            sf = app.scale_factor
            canvas.delete("all")
            canvas.configure(bg=app.colors["bg"])
            
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w <= 1: w = int(300 * sf)
            if h <= 1: h = int(200 * sf)
            
            canvas_height = h
            
            bar_width = int(7 * sf)
            spacing = int(2 * sf)
            start_x = int(15 * sf)
            base_y = canvas_height - int(30 * sf)
            
            for i, count in enumerate(counts):
                x = start_x + i * (bar_width + spacing)
                bar_height = (count / max_count) * (canvas_height - int(60 * sf))
                
                # 색상 로직
                if count >= 5:
                    color = app.colors["stats_bar_today"]
                else:
                    color = app.colors["stats_bar_other"]
                    
                # 오늘 날짜 강조
                outline = app.colors["fg"] if dates[i] == today_str else ""
                
                rect_id = canvas.create_rectangle(x, base_y - bar_height, x + bar_width, base_y, fill=color, outline=outline)
                
                # 날짜 라벨 (1일, 5일, 10일... 간격으로 표시)
                if i == 0 or (i + 1) % 5 == 0:
                    canvas.create_text(x + bar_width/2, base_y + int(15 * sf), text=dates[i], font=("Helvetica", int(7 * sf)), fill=app.colors["fg_sub"])
                
                # 툴팁
                tooltip_text = f"{dates[i]}: {count}갓생"
                def on_enter(e, txt=tooltip_text, bx=x, by=base_y - bar_height):
                    canvas.delete("tooltip")
                    canvas.create_text(bx + bar_width/2, by - int(10 * sf), text=txt, font=("Helvetica", int(8 * sf), "bold"), fill=app.colors["fg"], tag="tooltip")
                    
                def on_leave(e):
                    canvas.delete("tooltip")

                canvas.tag_bind(rect_id, "<Enter>", on_enter)
                canvas.tag_bind(rect_id, "<Leave>", on_leave)

        draw_graph()
        canvas.bind("<Configure>", draw_graph)

        # 최근 30일 통계 요약
        total_30_count = sum(counts)
        total_30_duration = 0
        
        for i in range(29, -1, -1):
            d = datetime.now() - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            if d_str in daily_stats:
                total_30_duration += daily_stats[d_str]['duration']
                
        hours, minutes = divmod(total_30_duration, 60)
        time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

        stats_frame = tk.Frame(left_frame, bg=app.colors["bg"])
        stats_frame.pack(pady=20)
        
        label_summary = tk.Label(stats_frame, text=f"최근 30일: {total_30_count}갓생 ({time_str})", font=("Helvetica", int(10 * app.scale_factor), "bold"), bg=app.colors["bg"], fg=app.colors["fg"])
        label_summary.pack()

        # === 우측: 로그 리스트 ===
        right_frame = tk.Frame(main_frame, bg=app.colors["bg"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        label_log_title = tk.Label(right_frame, text="최근 기록", font=("Helvetica", int(11 * app.scale_factor), "bold"), bg=app.colors["bg"], fg=app.colors["fg"])
        label_log_title.pack(pady=(0, int(10 * app.scale_factor)))

        # CSV 내보내기 버튼
        btn_export = tk.Button(right_frame, text="CSV 내보내기", font=("Helvetica", int(8 * app.scale_factor)), 
                            bg=app.colors["btn_bg"], fg=app.colors["btn_fg"], 
                            bd=0, padx=10, pady=4, command=lambda: export_csv(sw))
        btn_export.pack(side=tk.BOTTOM, pady=(5, 0), fill=tk.X)
        btn_export.bind("<Enter>", lambda e: btn_export.config(bg=app.colors["btn_hover"]))
        btn_export.bind("<Leave>", lambda e: btn_export.config(bg=app.colors["btn_bg"]))

        # 데이터 더 보기 함수
        def load_more_data():
            nonlocal current_view_days, daily_stats, logs
            current_view_days += 30
            
            # 데이터 추가 로드
            daily_stats = parse_logs(current_view_days)
            logs, has_more_new = get_recent_logs(current_view_days)
            
            if not has_more_new:
                btn_more.pack_forget()

            # 로그 리스트 갱신
            draw_logs()

        # 더 보기 버튼
        btn_more = tk.Button(right_frame, text="이전 기록 더 보기 (+30일)", font=("Helvetica", int(8 * app.scale_factor)), 
                            bg=app.colors["btn_bg"], fg=app.colors["btn_fg"], 
                            bd=0, padx=10, pady=4, command=load_more_data)
        if has_more:
            btn_more.pack(side=tk.BOTTOM, pady=(5, 0), fill=tk.X)
        btn_more.bind("<Enter>", lambda e: btn_more.config(bg=app.colors["btn_hover"]))
        btn_more.bind("<Leave>", lambda e: btn_more.config(bg=app.colors["btn_bg"]))

        list_container = tk.Frame(right_frame, bg=app.colors["bg"])
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 로그 캔버스 (박스 형태 시각화)
        log_canvas = tk.Canvas(list_container, bg=app.colors["bg"], highlightthickness=0, yscrollcommand=scrollbar.set)
        log_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=log_canvas.yview)
        
        task_font = tkfont.Font(family="Helvetica", size=int(9 * app.scale_factor))
        time_font = tkfont.Font(family="Helvetica", size=int(8 * app.scale_factor))
        
        # 펼쳐진 날짜 저장 (가장 최근 날짜만 기본적으로 펼침)
        expanded_dates = set()
        if logs:
            most_recent_date = logs[0]['start'].strftime("%m/%d")
            expanded_dates.add(most_recent_date)

        def toggle_date(date_key):
            if date_key in expanded_dates:
                expanded_dates.remove(date_key)
            else:
                expanded_dates.add(date_key)
            draw_logs()

        def draw_logs(event=None):
            sf = app.scale_factor
            # 폰트 업데이트
            task_font.configure(size=int(9 * sf))
            time_font.configure(size=int(8 * sf))
            
            try:
                log_canvas.config(cursor="")
                log_canvas.delete("all")
                canvas_width = log_canvas.winfo_width()
                if canvas_width <= 1: return

                y_offset = int(10 * sf)
                item_height = int(24 * sf)
                padding = int(4 * sf)
                
                if not logs:
                    log_canvas.create_text(canvas_width/2, int(30 * sf), text="아직 기록된 집중 시간이 없습니다.", fill=app.colors["fg_sub"], font=("Helvetica", int(8 * sf)))
                    return

                current_date_str = None
                weekdays = ["월", "화", "수", "목", "금", "토", "일"]

                for log in logs:
                    date_str = log['start'].strftime("%m/%d")
                    
                    # 날짜 헤더 표시 (날짜가 바뀔 때마다)
                    if date_str != current_date_str:
                        if current_date_str is not None:
                            y_offset += int(10 * sf) # 날짜 그룹 간 간격
                        
                        current_date_str = date_str
                        weekday = weekdays[log['start'].weekday()]
                        
                        date_key = log['start'].strftime("%Y-%m-%d")
                        day_stats = daily_stats.get(date_key, {'count': 0, 'duration': 0})
                        day_count = day_stats['count']
                        day_duration = day_stats['duration']
                        
                        hours, minutes = divmod(day_duration, 60)
                        time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"
                        
                        is_expanded = date_str in expanded_dates
                        icon = "▼" if is_expanded else "▶"
                        header_text = f"{icon} {date_str} ({weekday})   {day_count}갓생 ({time_str})"
                        
                        # 헤더 배경 및 텍스트
                        header_height = int(26 * sf)
                        bg_id = log_canvas.create_rectangle(int(2 * sf), y_offset, canvas_width-int(5 * sf), y_offset + header_height, 
                                                    fill=app.colors["btn_bg"], outline="")
                        header_id = log_canvas.create_text(int(8 * sf), y_offset + header_height/2, text=header_text, anchor="w", font=("Helvetica", int(9 * sf), "bold"), fill=app.colors["fg"])
                        
                        for item_id in [bg_id, header_id]:
                            log_canvas.tag_bind(item_id, "<Button-1>", lambda e, d=date_str: toggle_date(d))
                            log_canvas.tag_bind(item_id, "<Enter>", lambda e: log_canvas.config(cursor="hand2"))
                            log_canvas.tag_bind(item_id, "<Leave>", lambda e: log_canvas.config(cursor=""))
                        
                        y_offset += header_height + int(4 * sf) # 헤더 높이 + 간격

                    if date_str not in expanded_dates:
                        continue

                    time_range = f"{log['start'].strftime('%H:%M')} ~ {log['end'].strftime('%H:%M')} ({log['duration']}분)"
                    task = log['task']
                    if task == "-":
                        task = ""
                    task = task.replace('\n', ' ').strip()
                    
                    time_width = time_font.measure(time_range)
                    
                    # 텍스트 너비에 맞춰 말줄임표(...) 처리
                    available_width = max(0, canvas_width - (time_width + int(50 * sf)))
                    if task_font.measure(task) > available_width:
                        while task_font.measure(task + "...") > available_width and len(task) > 0:
                            task = task[:-1]
                        task += "..."
                    
                    # 박스 그리기
                    log_canvas.create_rectangle(int(10 * sf), y_offset, canvas_width-int(10 * sf), y_offset + item_height, 
                                                fill=app.colors["btn_bg"], outline=app.colors["btn_hover"])
                    
                    # 시간
                    log_canvas.create_text(int(20 * sf), y_offset + int(12 * sf), text=time_range, 
                                        anchor="w", font=time_font, fill=app.colors["fg_sub"])
                    
                    # 작업명
                    log_canvas.create_text(int(20 * sf) + time_width + int(10 * sf), y_offset + int(12 * sf), text=task, 
                                        anchor="w", font=task_font, fill=app.colors["fg"])
                    
                    y_offset += item_height + padding
                    
                log_canvas.configure(scrollregion=(0, 0, canvas_width, y_offset + int(10 * sf)))
            except Exception:
                traceback.print_exc()

        log_canvas.bind("<Configure>", draw_logs)
        
        # 마우스 휠 스크롤
        def on_mousewheel(event):
            log_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        sw.bind("<MouseWheel>", on_mousewheel)
        
        def on_close():
            app.stats_window_x = sw.winfo_x()
            app.stats_window_y = sw.winfo_y()
            app.stats_window_w = sw.winfo_width()
            app.stats_window_h = sw.winfo_height()
            sw.destroy()
            app.stats_window = None
            
        sw.protocol("WM_DELETE_WINDOW", on_close)
        
        def refresh_theme():
            new_colors = app.colors
            sw.configure(bg=new_colors["bg"])
            main_frame.configure(bg=new_colors["bg"])
            left_frame.configure(bg=new_colors["bg"])
            right_frame.configure(bg=new_colors["bg"])
            stats_frame.configure(bg=new_colors["bg"])
            list_container.configure(bg=new_colors["bg"])
            log_canvas.configure(bg=new_colors["bg"])
            
            def update_recursive(w):
                try:
                    if isinstance(w, (tk.LabelFrame, tk.Frame)):
                        w.configure(bg=new_colors["bg"])
                        if isinstance(w, tk.LabelFrame):
                            w.configure(fg=new_colors["fg"])
                    elif isinstance(w, (tk.Label, tk.Button)):
                        w.configure(bg=new_colors["bg"], fg=new_colors["fg"])
                except: pass
                for child in w.winfo_children():
                    update_recursive(child)
            update_recursive(sw)
            draw_graph()
            draw_logs()
            
        sw.refresh_theme = refresh_theme
        
        def refresh_internal_ui_scale():
            sf = app.scale_factor
            
            # Update fonts of labels and buttons
            label_title.configure(font=("Helvetica", int(11*sf), "bold"))
            label_summary.configure(font=("Helvetica", int(10*sf), "bold"))
            label_log_title.configure(font=("Helvetica", int(11*sf), "bold"))
            btn_export.configure(font=("Helvetica", int(8*sf)))
            if btn_more.winfo_exists():
                btn_more.configure(font=("Helvetica", int(8*sf)))

            # Update paddings
            label_title.pack_configure(pady=(0, int(15*sf)))
            label_log_title.pack_configure(pady=(0, int(10*sf)))

            # Redraw canvases
            draw_graph()
            draw_logs()
        sw.refresh_internal_ui_scale = refresh_internal_ui_scale

        def refresh_ui_scale():
            sf = app.scale_factor
            w = int(740 * sf)
            h = int(360 * sf)
            sw.geometry(f"{w}x{h}")
            
            # 폰트 및 패딩 업데이트 (재귀적)
            new_lbl_font = ("Helvetica", int(10 * sf))
            new_bold_font = ("Helvetica", int(11 * sf), "bold")
            
            def update_fonts(w):
                try:
                    if isinstance(w, (tk.Label, tk.Button)):
                        if "bold" in str(w.cget("font")):
                            w.configure(font=new_bold_font)
                        else:
                            w.configure(font=("Helvetica", int(9 * sf)))
                except: pass
                for child in w.winfo_children():
                    update_fonts(child)
            update_fonts(sw)
            draw_graph()
            draw_logs()
            
        sw.refresh_ui_scale = refresh_ui_scale
        
    except Exception as e:
        traceback.print_exc()
        tk.messagebox.showerror("오류", f"통계 창을 여는 중 오류가 발생했습니다:\n{e}")