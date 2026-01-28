import tkinter as tk
from utils import get_side_position, open_url

def show_ad_window(app):
    """집중 완료 축하 및 광고(후원) 팝업을 띄웁니다."""
    # 이미 팝업이 떠 있다면 중복 실행 방지
    if hasattr(app, 'ad_window') and app.ad_window and app.ad_window.winfo_exists():
        app.ad_window.lift()
        return

    ad = tk.Toplevel(app.root)
    app.ad_window = ad
    
    ad.title(app.loc.get("ad_window_title"))
    w = int(300 * app.scale_factor)
    h = int(200 * app.scale_factor)
    ad.geometry(f"{w}x{h}")
    ad.resizable(False, False)
    ad.configure(bg=app.colors["bg"])
    ad.transient(app.root)
    
    # 메인 윈도우 옆에 배치
    ad.geometry(get_side_position(app.root, w, h))

    # 1. 축하 메시지
    tk.Label(ad, text=app.loc.get("ad_congrats_msg"), font=("Helvetica", 14, "bold"), 
             bg=app.colors["bg"], fg=app.colors["fg"]).pack(pady=(20, 5))
    
    # 시간 환산
    hours, minutes = divmod(app.today_duration, 60)
    if hours > 0:
        time_str = app.loc.get("time_fmt_hm", hours=hours, minutes=minutes)
    else:
        time_str = app.loc.get("time_fmt_m", minutes=minutes)
    
    tk.Label(ad, text=app.loc.get("ad_today_stats_fmt", count=app.today_count, time=time_str), font=("Helvetica", 11, "bold"), 
             bg=app.colors["bg"], fg=app.colors["stats_bar_today"]).pack(pady=(0, 5))
    
    tk.Label(ad, text=app.loc.get("ad_rest_msg"), font=("Helvetica", 10), 
             bg=app.colors["bg"], fg=app.colors["fg_sub"]).pack(pady=(0, 20))

    # 2. 광고/후원 영역 (버튼 형태)
    # 실제 광고 이미지나 문구로 교체 가능
    ad_text = app.loc.get("ad_coffee_btn")
    ad_url = "https://github.com/jinsseof-dev/god-mod-timer"
    
    btn_ad = tk.Button(ad, text=ad_text, font=("Helvetica", 10, "bold"), 
                       bg="#FFD700", fg="#555555", bd=0, padx=15, pady=8, cursor="hand2",
                       command=lambda: [open_url(ad_url), ad.destroy()])
    btn_ad.pack(pady=5, fill=tk.X, padx=30)

    # 3. 닫기 버튼
    btn_close = tk.Button(ad, text=app.loc.get("close"), font=("Helvetica", 9), bg="#E0E0E0", fg="#555555", bd=0, padx=10, pady=4, command=ad.destroy)
    btn_close.pack(side=tk.BOTTOM, pady=15)