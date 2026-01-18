import tkinter as tk
from datetime import datetime, timedelta
import os
from common import get_user_data_path
import json
from utils import export_csv, parse_logs, get_side_position

def open_stats_window(app):
    """통계 창을 엽니다."""
    sw = tk.Toplevel(app.root)
    sw.title("집중 통계")
    sw.geometry("320x400")
    sw.resizable(False, False)
    sw.configure(bg=app.colors["bg"])
    sw.transient(app.root)
    
    # 화면 중앙 배치 -> 우측 배치 (가림 방지)
    sw.geometry(get_side_position(app.root, 320, 400))

    daily_stats = parse_logs()
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_stats = daily_stats.get(today_str, {'count': 0})
    today_count = today_stats['count']
    
    # 헤더 (오늘의 기록)
    tk.Label(sw, text="오늘의 갓생 지수", font=("Helvetica", 12), bg=app.colors["bg"], fg=app.colors["fg_sub"]).pack(pady=(25, 5))
    tk.Label(sw, text=f"{today_count}갓생", font=("Helvetica", 36, "bold"), bg=app.colors["bg"], fg=app.colors["stats_bar_today"]).pack(pady=(0, 5))

    # 차트 캔버스
    canvas_height = 180
    canvas = tk.Canvas(sw, width=280, height=canvas_height, bg=app.colors["bg"], highlightthickness=0)
    canvas.pack(pady=10)

    # 최근 7일 데이터 준비
    dates = []
    counts = []
    max_count = 0
    
    for i in range(6, -1, -1):
        d = datetime.now() - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        dates.append(d.strftime("%m/%d"))
        stats = daily_stats.get(d_str, {'count': 0})
        c = stats['count']
        counts.append(c)
        if c > max_count: max_count = c
    
    if max_count == 0: max_count = 5 # 그래프 기본 스케일
    
    # 막대 그래프 그리기
    bar_width = 20
    spacing = 15
    start_x = 20
    base_y = canvas_height - 30
    
    for i, count in enumerate(counts):
        x = start_x + i * (bar_width + spacing)
        bar_height = (count / max_count) * (canvas_height - 60)
        
        # 막대 (오늘 날짜는 토마토색, 나머지는 연한 붉은색)
        color = app.colors["stats_bar_today"] if dates[i] == datetime.now().strftime("%m/%d") else app.colors["stats_bar_other"]
        canvas.create_rectangle(x, base_y - bar_height, x + bar_width, base_y, fill=color, outline="")
        
        # 날짜 라벨
        canvas.create_text(x + bar_width/2, base_y + 15, text=dates[i], font=("Helvetica", 8), fill=app.colors["fg_sub"])

    # 주간 통계 계산 (ISO 달력 기준 이번 주)
    current_iso = datetime.now().isocalendar()[:2] # (Year, Week)
    weekly_count = 0
    weekly_duration = 0
    
    for date_str, stats in daily_stats.items():
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt.isocalendar()[:2] == current_iso:
                weekly_count += stats['count']
                weekly_duration += stats['duration']
        except ValueError:
            continue
            
    # 시간 환산 (실제 duration 사용)
    total_minutes = weekly_duration
    hours, minutes = divmod(total_minutes, 60)
    time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

    # 푸터 (주간 시간 및 누적 기록)
    total_count = sum(s['count'] for s in daily_stats.values())
    
    footer_frame = tk.Frame(sw, bg=app.colors["bg"])
    footer_frame.pack(side=tk.BOTTOM, pady=20)
    
    tk.Label(footer_frame, text=f"이번 주 집중: {weekly_count}갓생 ({time_str})", font=("Helvetica", 11, "bold"), bg=app.colors["bg"], fg=app.colors["fg"]).pack()
    tk.Label(footer_frame, text=f"(누적 {total_count}갓생)", font=("Helvetica", 9), bg=app.colors["bg"], fg=app.colors["fg_sub"]).pack(pady=(2, 0))
    
    # CSV 내보내기 버튼
    btn_export = tk.Button(footer_frame, text="CSV 내보내기", font=("Helvetica", 9), 
                           bg=app.colors["btn_bg"], fg=app.colors["btn_fg"], 
                           bd=0, padx=10, pady=4, command=lambda: export_csv(sw))
    btn_export.pack(pady=(15, 0))
    btn_export.bind("<Enter>", lambda e: btn_export.config(bg=app.colors["btn_hover"]))
    btn_export.bind("<Leave>", lambda e: btn_export.config(bg=app.colors["btn_bg"]))