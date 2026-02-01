import tkinter as tk
from utils import get_side_position, open_url, load_remote_image
import os
import random

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
             bg=app.colors["bg"], fg=app.colors["fg_sub"]).pack(pady=(0, 10))

    # 2. 광고/후원 영역
    
    # AD_POPUP_POLICY 확인
    ad_policy = os.environ.get("AD_POPUP_POLICY", "random").lower()
    show_banner = False
    
    if ad_policy == "always":
        show_banner = True
    elif ad_policy == "never":
        show_banner = False
    else:
        show_banner = random.random() < 0.5

    if show_banner:
        # 배너 프레임 (배경색과 동일하게 설정하여 파란색 영역 제거)
        ad_frame = tk.Frame(ad, bg=app.colors["bg"], bd=0)
        ad_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ad_url = "https://www.buymeacoffee.com/jinsseofdev"
        
        # 이미지 로드 시도 (캐싱 적용)
        tk_image = load_remote_image(
            "bmc_button_yellow.png",
            "https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png",
            (217, 60)
        )
        ad.bmc_image = tk_image # GC 방지

        if tk_image:
            tk.Button(ad_frame, image=tk_image, bd=0, cursor="hand2", bg=app.colors["bg"], activebackground=app.colors["bg"],
                      command=lambda: [open_url(ad_url), ad.destroy()]).pack(pady=(5, 5))
        else:
            # 이미지 로드 실패 시 텍스트 버튼 표시 (기존 로직)
            tk.Button(ad_frame, text=app.loc.get("ad_coffee_btn"), font=("Helvetica", 10, "bold"), 
                      bg="#FFD700", fg="#555555", bd=0, padx=10, pady=5, cursor="hand2",
                      command=lambda: [open_url(ad_url), ad.destroy()]).pack(pady=(0, 5), padx=5, fill=tk.X)

    # 3. 닫기 버튼
    btn_close = tk.Button(ad, text=app.loc.get("close"), font=("Helvetica", 9), bg="#E0E0E0", fg="#555555", bd=0, padx=10, pady=4, command=ad.destroy)
    btn_close.pack(side=tk.BOTTOM, pady=15)