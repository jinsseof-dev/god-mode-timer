import tkinter as tk
import tkinter.font as tkfont
import math
from datetime import datetime, timedelta
from utils import export_csv, get_recent_logs, get_side_position, parse_logs, delete_log, update_log, get_task_stats
import traceback

def open_stats_window(app):
    """통계 창을 엽니다."""
    try:
        sw = tk.Toplevel(app.root)
        sw.title(app.loc.get("stats_window_title"))
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

        # 그래프 헤더 (제목 + 보기 모드 전환 버튼)
        graph_header = tk.Frame(left_frame, bg=app.colors["bg"])
        graph_header.pack(fill=tk.X, pady=(0, int(10*app.scale_factor)))

        label_title = tk.Label(graph_header, text=app.loc.get("monthly_stats_title"), font=("Helvetica", int(11*app.scale_factor), "bold"), bg=app.colors["bg"], fg=app.colors["fg"])
        label_title.pack(side=tk.LEFT)

        # 그래프 모드 변수 (daily / weekly)
        graph_mode = tk.StringVar(value="daily")
        selected_date_filter = None

        mode_frame = tk.Frame(graph_header, bg=app.colors["bg"])
        mode_frame.pack(side=tk.RIGHT)

        def change_graph_mode():
            nonlocal selected_date_filter
            selected_date_filter = None
            prepare_graph_data()
            draw_graph()

        rb_daily = tk.Radiobutton(mode_frame, text=app.loc.get("stats_daily", default="Daily"), variable=graph_mode, value="daily", 
                                  indicatoron=0, bg=app.colors["btn_bg"], selectcolor=app.colors["start_btn_bg"],
                                  font=("Helvetica", int(8*app.scale_factor)), command=change_graph_mode, bd=0, padx=5)
        rb_daily.pack(side=tk.LEFT, padx=2)
        
        rb_tasks = tk.Radiobutton(mode_frame, text=app.loc.get("stats_tasks", default="Tasks"), variable=graph_mode, value="tasks", 
                                   indicatoron=0, bg=app.colors["btn_bg"], selectcolor=app.colors["start_btn_bg"],
                                   font=("Helvetica", int(8*app.scale_factor)), command=change_graph_mode, bd=0, padx=5)
        rb_tasks.pack(side=tk.LEFT, padx=2)
        
        rb_hourly = tk.Radiobutton(mode_frame, text=app.loc.get("stats_hourly", default="Hourly"), variable=graph_mode, value="hourly", 
                                   indicatoron=0, bg=app.colors["btn_bg"], selectcolor=app.colors["start_btn_bg"],
                                   font=("Helvetica", int(8*app.scale_factor)), command=change_graph_mode, bd=0, padx=5)
        rb_hourly.pack(side=tk.LEFT, padx=2)

        # 캔버스
        canvas = tk.Canvas(left_frame, bg=app.colors["bg"], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # 툴팁 폰트 (한 번만 생성)
        tooltip_font = tkfont.Font(family="Helvetica", size=int(8 * app.scale_factor), weight="bold")

        # 그래프 데이터 변수
        dates = []
        counts = []
        max_count = 0
        task_stats = []
        today_str = datetime.now().strftime("%m/%d")

        def prepare_graph_data():
            nonlocal dates, counts, max_count, task_stats
            dates = []
            counts = []
            max_count = 0
            task_stats = []
            
            if graph_mode.get() == "daily":
                # 일간 (최근 30일)
                for i in range(29, -1, -1):
                    d = datetime.now() - timedelta(days=i)
                    d_str = d.strftime("%Y-%m-%d")
                    dates.append(d.strftime("%m/%d"))
                    stats = daily_stats.get(d_str, {'count': 0})
                    c = stats['count']
                    counts.append(c)
                    if c > max_count: max_count = c
            elif graph_mode.get() == "tasks":
                # 작업별 분포 (DB 집계 사용)
                task_stats = get_task_stats(current_view_days, selected_date_filter)
            elif graph_mode.get() == "hourly":
                # 시간대별 분포 (0시 ~ 23시)
                hours = [0] * 24
                for log in logs:
                    # 로그의 시작 시간 기준
                    h = log['start'].hour
                    hours[h] += 1
                
                dates = [str(h) for h in range(24)]
                counts = hours
                max_count = max(counts) if counts else 0

            if max_count == 0: max_count = 5

        prepare_graph_data()

        # 막대 그래프 그리기
        def draw_graph(event=None):
            sf = app.scale_factor
            canvas.delete("all")
            canvas.configure(bg=app.colors["bg"])
            
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w <= 1: w = int(300 * sf)
            if h <= 1: h = int(200 * sf)
            
            if graph_mode.get() == "tasks":
                # 파이 차트 그리기
                if not task_stats:
                    canvas.create_text(w/2, h/2, text=app.loc.get("no_data", default="No Data"), fill=app.colors["fg_sub"], font=("Helvetica", int(10*sf)))
                    return
                
                # 선택된 날짜 표시
                if selected_date_filter:
                    canvas.create_text(int(10*sf), int(10*sf), text=f"Date: {selected_date_filter}", anchor="nw", font=("Helvetica", int(9*sf), "bold"), fill=app.colors["fg"])

                # 레이아웃: 파이 차트는 왼쪽, 범례는 오른쪽
                cx = w * 0.35
                cy = h / 2
                radius = min(w * 0.6, h) / 2 * 0.8
                
                colors = ['#FF5252', '#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#00BCD4', '#FF9800', '#795548', '#607D8B', '#9E9E9E']
                start_angle = 90
                
                # 파이 조각 그리기
                for i, (task, duration, pct) in enumerate(task_stats):
                    extent = (pct / 100) * 360
                    color = colors[i % len(colors)]
                    
                    if pct >= 99.99:
                        # 100%일 경우 create_arc가 일부 환경에서 렌더링되지 않는 문제 해결을 위해 create_oval 사용
                        slice_id = canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, fill=color, outline=app.colors["bg"], width=max(1, int(1*sf)))
                    else:
                        # 조각
                        slice_id = canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=start_angle, extent=-extent, fill=color, outline=app.colors["bg"], width=max(1, int(1*sf)))
                    
                    # 툴팁
                    tooltip_text = f"{task}: {int(duration)}m ({pct:.1f}%)"

                    def on_enter_pie(e, txt=tooltip_text):
                        canvas.delete("tooltip")
                        sf = app.scale_factor
                        
                        # 1. 텍스트 크기 측정
                        text_width = tooltip_font.measure(txt)
                        text_height = int(12 * sf)
                        
                        # 2. 패딩 및 박스 크기 계산
                        padding_x = int(8 * sf)
                        padding_y = int(5 * sf)
                        box_width = text_width + 2 * padding_x
                        box_height = text_height + 2 * padding_y
                        
                        # 3. 박스 위치 계산 (마우스 커서 기준)
                        box_x1 = e.x + 15
                        box_y1 = e.y + 10
                        
                        # 캔버스 경계를 벗어나지 않도록 위치 조정
                        canvas_w = canvas.winfo_width()
                        if box_x1 + box_width > canvas_w:
                            box_x1 = e.x - box_width - 15
                        
                        box_x2 = box_x1 + box_width
                        box_y2 = box_y1 + box_height

                        # 4. 툴팁 배경 및 텍스트 그리기
                        canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill=app.colors["timer_center"], outline=app.colors["fg_sub"], tag="tooltip")
                        canvas.create_text(box_x1 + padding_x, box_y1 + padding_y, text=txt, anchor="nw", font=tooltip_font, fill=app.colors["fg"], tag="tooltip")

                    canvas.tag_bind(slice_id, "<Enter>", on_enter_pie)
                    canvas.tag_bind(slice_id, "<Motion>", on_enter_pie)
                    canvas.tag_bind(slice_id, "<Leave>", lambda e: canvas.delete("tooltip"))
                    
                    start_angle -= extent

                # 범례 (Legend) 그리기 (상위 8개)
                legend_x = w * 0.65
                legend_y = int(20 * sf)
                legend_spacing = int(18 * sf)
                
                for i, (task, duration, pct) in enumerate(task_stats[:8]):
                    if legend_y + legend_spacing > h: break
                    color = colors[i % len(colors)]
                    
                    # 색상 박스
                    canvas.create_rectangle(legend_x, legend_y, legend_x + int(10*sf), legend_y + int(10*sf), fill=color, outline="")
                    
                    # 텍스트 (너무 길면 자름)
                    display_text = task
                    if len(display_text) > 10: display_text = display_text[:9] + ".."
                    canvas.create_text(legend_x + int(15*sf), legend_y + int(5*sf), text=f"{display_text} ({int(pct)}%)", anchor="w", font=("Helvetica", int(8*sf)), fill=app.colors["fg"])
                    legend_y += legend_spacing
                return

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
                outline = app.colors["fg"] if (graph_mode.get() == "daily" and dates[i] == today_str) else ""
                
                rect_id = canvas.create_rectangle(x, base_y - bar_height, x + bar_width, base_y, fill=color, outline=outline)
                
                # 날짜 라벨 (1일, 5일, 10일... 간격으로 표시)
                show_label = False
                if graph_mode.get() == "hourly":
                    if i % 6 == 0: show_label = True # 0, 6, 12, 18시 표시
                elif i == 0 or (i + 1) % 5 == 0:
                    show_label = True
                
                if show_label:
                    canvas.create_text(x + bar_width/2, base_y + int(15 * sf), text=dates[i], font=("Helvetica", int(7 * sf)), fill=app.colors["fg_sub"])
                
                # 툴팁
                if graph_mode.get() == "daily":
                    tooltip_text = app.loc.get("tooltip_fmt", date=dates[i], count=count)
                else: # hourly
                    tooltip_text = f"{dates[i]}시: {count}회"

                def on_enter(e, txt=tooltip_text, bx=x, by=base_y - bar_height):
                    canvas.delete("tooltip")
                    sf = app.scale_factor
                    
                    # 1. 텍스트 크기 측정
                    text_width = tooltip_font.measure(txt)
                    text_height = int(12 * sf)
                    
                    # 2. 패딩 및 박스 크기 계산
                    padding_x = int(8 * sf)
                    padding_y = int(5 * sf)
                    box_width = text_width + 2 * padding_x
                    box_height = text_height + 2 * padding_y
                    
                    # 3. 박스 위치 계산 (막대 중앙 상단)
                    box_x1 = bx + bar_width/2 - box_width/2
                    box_y1 = by - box_height - int(5 * sf) # 막대 위로 5px
                    
                    # 캔버스 경계를 벗어나지 않도록 위치 조정
                    canvas_w = canvas.winfo_width()
                    if box_x1 < 0:
                        box_x1 = 0
                    if box_x1 + box_width > canvas_w:
                        box_x1 = canvas_w - box_width
                    
                    box_x2 = box_x1 + box_width
                    box_y2 = box_y1 + box_height

                    # 4. 툴팁 배경 및 텍스트 그리기
                    canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill=app.colors["timer_center"], outline=app.colors["fg_sub"], tag="tooltip")
                    canvas.create_text(box_x1 + padding_x, box_y1 + padding_y, text=txt, anchor="nw", font=tooltip_font, fill=app.colors["fg"], tag="tooltip")

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
                
        def get_time_str(duration):
            hours, minutes = divmod(duration, 60)
            if hours > 0:
                return app.loc.get("time_fmt_hm", hours=hours, minutes=minutes)
            else:
                return app.loc.get("time_fmt_m", minutes=minutes)

        time_str = get_time_str(total_30_duration)

        stats_frame = tk.Frame(left_frame, bg=app.colors["bg"])
        stats_frame.pack(pady=20)
        
        label_summary = tk.Label(stats_frame, text=app.loc.get("recent_30_days_fmt", count=total_30_count, time=time_str), font=("Helvetica", int(10 * app.scale_factor), "bold"), bg=app.colors["bg"], fg=app.colors["fg"])
        label_summary.pack()

        # === 우측: 로그 리스트 ===
        right_frame = tk.Frame(main_frame, bg=app.colors["bg"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        label_log_title = tk.Label(right_frame, text=app.loc.get("recent_logs_title"), font=("Helvetica", int(11 * app.scale_factor), "bold"), bg=app.colors["bg"], fg=app.colors["fg"])
        label_log_title.pack(pady=(0, int(10 * app.scale_factor)))

        # CSV 내보내기 버튼
        btn_export = tk.Button(right_frame, text=app.loc.get("csv_export"), font=("Helvetica", int(8 * app.scale_factor)), 
                            bg=app.colors["btn_bg"], fg=app.colors["btn_fg"], 
                            bd=0, padx=10, pady=4, command=lambda: export_csv(sw, app.loc))
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
        btn_more = tk.Button(right_frame, text=app.loc.get("load_more_logs"), font=("Helvetica", int(8 * app.scale_factor)), 
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
            most_recent_date = logs[0]['start'].strftime("%Y-%m-%d")
            expanded_dates.add(most_recent_date)

        def toggle_date(date_key):
            # 접기/펼치기만 수행
            if date_key in expanded_dates:
                expanded_dates.remove(date_key)
            else:
                expanded_dates.add(date_key)
            draw_logs()

        def show_date_stats(date_key):
            nonlocal selected_date_filter
            
            # 해당 날짜로 그래프 필터링 및 모드 전환
            selected_date_filter = date_key
            graph_mode.set("tasks")
            prepare_graph_data()
            draw_graph()
            
            # 날짜 클릭 시 해당 날짜의 로그 목록도 펼쳐줌
            if date_key not in expanded_dates:
                expanded_dates.add(date_key)
                draw_logs()
            
        def delete_log_item(timestamp_str):
            if tk.messagebox.askyesno(app.loc.get("confirm_delete_title", default="Delete"), 
                                      app.loc.get("confirm_delete_msg", default="Are you sure you want to delete this log?"), 
                                      parent=sw):
                if delete_log(timestamp_str):
                    # 데이터 리로드
                    nonlocal daily_stats, logs
                    daily_stats = parse_logs(current_view_days)
                    logs, _ = get_recent_logs(current_view_days)
                    
                    # 그래프 및 리스트 갱신
                    prepare_graph_data()
                    draw_graph()
                    draw_logs()
                    
                    # 요약 정보 갱신 (간단히 재계산)
                    refresh_language()
        
        def edit_log_item(log):
            # 편집 팝업
            edit_win = tk.Toplevel(sw)
            edit_win.title(app.loc.get("edit_log_title", default="Edit Log"))
            
            w = int(300 * app.scale_factor)
            h = int(150 * app.scale_factor)
            edit_win.geometry(f"{w}x{h}")
            
            # 통계 창 중앙에 배치
            x = sw.winfo_x() + (sw.winfo_width() // 2) - (w // 2)
            y = sw.winfo_y() + (sw.winfo_height() // 2) - (h // 2)
            edit_win.geometry(f"+{x}+{y}")
            
            edit_win.configure(bg=app.colors["bg"])
            edit_win.transient(sw)
            edit_win.grab_set()
            
            tk.Label(edit_win, text=app.loc.get("edit_task_label", default="Task Name"), 
                     font=("Helvetica", int(10*app.scale_factor)), bg=app.colors["bg"], fg=app.colors["fg"]).pack(pady=(int(15*app.scale_factor), int(5*app.scale_factor)))
            
            var_task = tk.StringVar(value=log['task'])
            entry = tk.Entry(edit_win, textvariable=var_task, font=("Helvetica", int(10*app.scale_factor)), bg=app.colors["btn_bg"], fg=app.colors["fg"])
            entry.pack(fill=tk.X, padx=int(20*app.scale_factor))
            entry.focus_set()
            
            def save_edit(event=None):
                new_task = var_task.get().strip()
                if update_log(log['timestamp_str'], new_task):
                    # 데이터 리로드 및 UI 갱신
                    nonlocal daily_stats, logs
                    daily_stats = parse_logs(current_view_days)
                    logs, _ = get_recent_logs(current_view_days)
                    
                    prepare_graph_data()
                    draw_graph()
                    draw_logs()
                    refresh_language() # 요약 정보 갱신
                    edit_win.destroy()
            
            btn_frame = tk.Frame(edit_win, bg=app.colors["bg"])
            btn_frame.pack(pady=int(15*app.scale_factor))
            
            tk.Button(btn_frame, text=app.loc.get("save_btn", default="Save"), command=save_edit,
                      bg=app.colors["start_btn_bg"], fg=app.colors["btn_fg"], bd=0, padx=10, pady=5).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text=app.loc.get("cancel", default="Cancel"), command=edit_win.destroy,
                      bg=app.colors["btn_bg"], fg=app.colors["fg"], bd=0, padx=10, pady=5).pack(side=tk.LEFT, padx=5)
            
            edit_win.bind("<Return>", save_edit)
            edit_win.bind("<Escape>", lambda e: edit_win.destroy())

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
                    log_canvas.create_text(canvas_width/2, int(30 * sf), text=app.loc.get("no_logs_message"), fill=app.colors["fg_sub"], font=("Helvetica", int(8 * sf)))
                    return

                current_date_key = None
                weekdays = app.loc.get("weekdays")

                for log in logs:
                    date_disp = log['start'].strftime("%m/%d")
                    date_key = log['start'].strftime("%Y-%m-%d")
                    
                    # 날짜 헤더 표시 (날짜가 바뀔 때마다)
                    if date_key != current_date_key:
                        if current_date_key is not None:
                            y_offset += int(10 * sf) # 날짜 그룹 간 간격
                        
                        current_date_key = date_key
                        weekday = weekdays[log['start'].weekday()]
                        
                        day_stats = daily_stats.get(date_key, {'count': 0, 'duration': 0})
                        day_count = day_stats['count']
                        day_duration = day_stats['duration']
                        
                        time_str = get_time_str(day_duration)
                        
                        is_expanded = date_key in expanded_dates
                        icon = "▼" if is_expanded else "▶"
                        # 아이콘과 텍스트 분리 (화살표만 클릭 가능하게 하기 위함)
                        text_part = app.loc.get("date_header_fmt", icon="", date=date_disp, weekday=weekday, count=day_count, time=time_str).strip()
                        
                        # 헤더 배경
                        header_height = int(26 * sf)
                        bg_id = log_canvas.create_rectangle(int(2 * sf), y_offset, canvas_width-int(5 * sf), y_offset + header_height, 
                                                    fill=app.colors["btn_bg"], outline="")
                        
                        # 아이콘 (화살표)
                        icon_x = int(8 * sf)
                        icon_y = y_offset + header_height/2
                        icon_id = log_canvas.create_text(icon_x, icon_y, text=icon, anchor="w", font=("Helvetica", int(9 * sf), "bold"), fill=app.colors["fg"])
                        
                        # 텍스트 (날짜 정보)
                        text_x = int(24 * sf)
                        text_id = log_canvas.create_text(text_x, icon_y, text=text_part, anchor="w", font=("Helvetica", int(9 * sf), "bold"), fill=app.colors["fg"])
                        
                        # 클릭 영역 (아이콘 주변)
                        click_area_w = int(24 * sf)
                        click_area_id = log_canvas.create_rectangle(int(2 * sf), y_offset, int(2 * sf) + click_area_w, y_offset + header_height, fill="", outline="")
                        
                        # 이벤트 바인딩 (아이콘 및 클릭 영역 -> 접기/펼치기)
                        for item_id in [icon_id, click_area_id]:
                            log_canvas.tag_bind(item_id, "<Button-1>", lambda e, d=date_key: toggle_date(d))
                            log_canvas.tag_bind(item_id, "<Enter>", lambda e: log_canvas.config(cursor="hand2"))
                            log_canvas.tag_bind(item_id, "<Leave>", lambda e: log_canvas.config(cursor=""))
                        
                        # 이벤트 바인딩 (날짜 텍스트 -> 파이 차트 보기)
                        log_canvas.tag_bind(text_id, "<Button-1>", lambda e, d=date_key: show_date_stats(d))
                        log_canvas.tag_bind(text_id, "<Enter>", lambda e: log_canvas.config(cursor="hand2"))
                        log_canvas.tag_bind(text_id, "<Leave>", lambda e: log_canvas.config(cursor=""))
                        
                        y_offset += header_height + int(4 * sf) # 헤더 높이 + 간격

                    if date_key not in expanded_dates:
                        continue

                    time_range = f"{log['start'].strftime('%H:%M')} ~ {log['end'].strftime('%H:%M')} ({log['duration']}분)"
                    task = log['task']
                    if task == "-":
                        task = ""
                    task = task.replace('\n', ' ').strip()
                    
                    time_width = time_font.measure(time_range)
                    
                    # 텍스트 너비에 맞춰 말줄임표(...) 처리
                    available_width = max(0, canvas_width - (time_width + int(50 * sf)))
                    if task_font.measure(task) > available_width - int(20 * sf): # 삭제 버튼 공간 확보
                        while task_font.measure(task + "...") > available_width and len(task) > 0:
                            task = task[:-1]
                        task += "..."
                    
                    # 박스 그리기
                    rect_id = log_canvas.create_rectangle(int(10 * sf), y_offset, canvas_width-int(10 * sf), y_offset + item_height, 
                                                fill=app.colors["btn_bg"], outline=app.colors["btn_hover"])
                    
                    # 시간
                    time_id = log_canvas.create_text(int(20 * sf), y_offset + int(12 * sf), text=time_range, 
                                        anchor="w", font=time_font, fill=app.colors["fg_sub"])
                    
                    # 작업명
                    task_id = log_canvas.create_text(int(20 * sf) + time_width + int(10 * sf), y_offset + int(12 * sf), text=task, 
                                        anchor="w", font=task_font, fill=app.colors["fg"])
                    
                    # 삭제 버튼 (x)
                    del_x = canvas_width - int(20 * sf)
                    del_y = y_offset + int(12 * sf)
                    del_id = log_canvas.create_text(del_x, del_y, text="×", font=("Helvetica", int(12 * sf), "bold"), fill=app.colors["fg_sub"], activefill="red")
                    
                    log_canvas.tag_bind(del_id, "<Button-1>", lambda e, ts=log.get('timestamp_str'): delete_log_item(ts))
                    log_canvas.tag_bind(del_id, "<Enter>", lambda e: log_canvas.config(cursor="hand2"))
                    log_canvas.tag_bind(del_id, "<Leave>", lambda e: log_canvas.config(cursor=""))
                    
                    # 항목 클릭 시 수정 (배경, 시간, 작업명)
                    for item in [rect_id, time_id, task_id]:
                        log_canvas.tag_bind(item, "<Button-1>", lambda e, l=log: edit_log_item(l))
                        log_canvas.tag_bind(item, "<Enter>", lambda e: log_canvas.config(cursor="hand2"))
                        log_canvas.tag_bind(item, "<Leave>", lambda e: log_canvas.config(cursor=""))
                    
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

        def refresh_language():
            sw.title(app.loc.get("stats_window_title"))
            label_title.config(text=app.loc.get("monthly_stats_title"))
            label_log_title.config(text=app.loc.get("recent_logs_title"))
            btn_export.config(text=app.loc.get("csv_export"))
            if btn_more.winfo_exists():
                btn_more.config(text=app.loc.get("load_more_logs"))
            
            t_str = get_time_str(total_30_duration)
            label_summary.config(text=app.loc.get("recent_30_days_fmt", count=total_30_count, time=t_str))
            prepare_graph_data()
            draw_graph()
            draw_logs()
        sw.refresh_language = refresh_language
        
        def refresh_internal_ui_scale():
            sf = app.scale_factor
            
            # 툴팁 폰트 업데이트
            tooltip_font.configure(size=int(8*sf), weight="bold")
            
            # Update fonts of labels and buttons
            label_title.configure(font=("Helvetica", int(11*sf), "bold"))
            label_summary.configure(font=("Helvetica", int(10*sf), "bold"))
            label_log_title.configure(font=("Helvetica", int(11*sf), "bold"))
            btn_export.configure(font=("Helvetica", int(8*sf)))
            if btn_more.winfo_exists():
                btn_more.configure(font=("Helvetica", int(8*sf)))
            rb_daily.configure(font=("Helvetica", int(8*sf)))
            rb_tasks.configure(font=("Helvetica", int(8*sf)))
            rb_hourly.configure(font=("Helvetica", int(8*sf)))

            # Update paddings
            graph_header.pack_configure(pady=(0, int(10*sf)))
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
        tk.messagebox.showerror(app.loc.get("error"), app.loc.get("stats_error_msg", error=e))