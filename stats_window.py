import tkinter as tk
from datetime import datetime, timedelta
import os
from common import get_user_data_path

def parse_logs():
    """로그 파일을 읽어 날짜별 집중 횟수를 계산합니다."""
    log_path = get_user_data_path("godmode_log.txt")
    if not os.path.exists(log_path):
        return {}
    
    daily_counts = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                # 로그 형식: [2024-01-01 12:00:00] ⚡ 갓생 집중 완료
                if "]" in line:
                    date_str = line.split("]")[0].strip("[")
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        date_key = dt.strftime("%Y-%m-%d")
                        daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
                    except ValueError:
                        continue
    except Exception:
        pass
    return daily_counts

def open_stats_window(app):
    """통계 창을 엽니다."""
    sw = tk.Toplevel(app.root)
    sw.title("집중 통계")
    sw.geometry("320x400")
    sw.resizable(False, False)
    sw.configure(bg=app.colors["bg"])
    sw.transient(app.root)
    
    # 화면 중앙 배치
    x = app.root.winfo_x() + (app.root.winfo_width() // 2) - 160
    y = app.root.winfo_y() + (app.root.winfo_height() // 2) - 200
    sw.geometry(f"+{x}+{y}")

    daily_counts = parse_logs()
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_count = daily_counts.get(today_str, 0)
    
    # 헤더 (오늘의 기록)
    tk.Label(sw, text="오늘의 갓생 지수", font=("Helvetica", 12), bg=app.colors["bg"], fg=app.colors["fg_sub"]).pack(pady=(25, 5))
    tk.Label(sw, text=f"{today_count}갓생", font=("Helvetica", 36, "bold"), bg=app.colors["bg"], fg=app.colors["stats_bar_today"]).pack(pady=(0, 20))

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
        c = daily_counts.get(d_str, 0)
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
    
    for date_str, count in daily_counts.items():
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt.isocalendar()[:2] == current_iso:
                weekly_count += count
        except ValueError:
            continue
            
    # 시간 환산 (1회 = 25분 가정)
    total_minutes = weekly_count * 25
    hours, minutes = divmod(total_minutes, 60)
    time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

    # 푸터 (주간 시간 및 누적 기록)
    total_count = sum(daily_counts.values())
    
    footer_frame = tk.Frame(sw, bg=app.colors["bg"])
    footer_frame.pack(side=tk.BOTTOM, pady=20)
    
    tk.Label(footer_frame, text=f"이번 주 집중: {weekly_count}갓생 ({time_str})", font=("Helvetica", 11, "bold"), bg=app.colors["bg"], fg=app.colors["fg"]).pack()
    tk.Label(footer_frame, text=f"(누적 {total_count}갓생)", font=("Helvetica", 9), bg=app.colors["bg"], fg=app.colors["fg_sub"]).pack(pady=(2, 0))