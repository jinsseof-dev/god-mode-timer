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
    
    ad.title("집중 완료!")
    ad.geometry("300x200")
    ad.resizable(False, False)
    ad.configure(bg=app.colors["bg"])
    ad.transient(app.root)
    
    # 메인 윈도우 옆에 배치
    ad.geometry(get_side_position(app.root, 300, 200))

    # 1. 축하 메시지
    tk.Label(ad, text="🎉 집중 완료!", font=("Helvetica", 14, "bold"), 
             bg=app.colors["bg"], fg=app.colors["fg"]).pack(pady=(20, 5))
    
    # 시간 환산
    hours, minutes = divmod(app.today_duration, 60)
    time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"
    
    tk.Label(ad, text=f"오늘의 갓생 지수: {app.today_count}회 ({time_str})", font=("Helvetica", 11, "bold"), 
             bg=app.colors["bg"], fg=app.colors["stats_bar_today"]).pack(pady=(0, 5))
    
    tk.Label(ad, text="잠시 휴식을 취하며 머리를 식히세요.", font=("Helvetica", 10), 
             bg=app.colors["bg"], fg=app.colors["fg_sub"]).pack(pady=(0, 20))

    # 2. 광고/후원 영역 (버튼 형태)
    # 실제 광고 이미지나 문구로 교체 가능
    ad_text = "☕ 개발자에게 커피 한 잔 사주기"
    ad_url = "https://github.com/jinsseof-dev/god-mod-timer"
    
    btn_ad = tk.Button(ad, text=ad_text, font=("Helvetica", 10, "bold"), 
                       bg="#FFD700", fg="#555555", bd=0, padx=15, pady=8, cursor="hand2",
                       command=lambda: [open_url(ad_url), ad.destroy()])
    btn_ad.pack(pady=5, fill=tk.X, padx=30)

    # 3. 닫기 버튼
    btn_close = tk.Button(ad, text="닫기", font=("Helvetica", 9), bg="#E0E0E0", fg="#555555", bd=0, padx=10, pady=4, command=ad.destroy)
    btn_close.pack(side=tk.BOTTOM, pady=15)