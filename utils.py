import sys
import subprocess
from datetime import datetime

def play_sound():
    """운영체제에 맞는 알림음을 재생합니다."""
    try:
        if sys.platform == "win32":
            import winsound
            winsound.Beep(1000, 1000)  # 1000Hz, 1.5초
        else:
            print('\a')  # Mac/Linux 기본 비프음
    except Exception:
        pass

def log_pomodoro():
    """완료된 뽀모도로를 로그 파일에 기록합니다."""
    try:
        with open("pomodoro_log.txt", "a", encoding="utf-8") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{now}] 🍅 뽀모도로 집중 완료\n")
        print("💾 기록이 'pomodoro_log.txt'에 저장되었습니다.")
    except Exception as e:
        print(f"\n로그 저장 실패: {e}")

def show_toast(title, message):
    """Windows 10/11 알림 센터에 토스트 메시지를 띄웁니다."""
    if sys.platform != "win32":
        return

    # PowerShell 스크립트 (System.Windows.Forms.NotifyIcon 사용)
    # Windows.UI.Notifications는 시작 메뉴 바로가기가 없으면 토스트가 뜨지 않고 알림 센터에만 남을 수 있음
    # 따라서 NotifyIcon(BalloonTip) 방식을 사용하여 즉시 팝업되도록 변경
    ps_script = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.Visible = $True
    $notify.BalloonTipTitle = "{title}"
    $notify.BalloonTipText = "{message}"
    $notify.ShowBalloonTip(5000)
    Start-Sleep -s 5
    $notify.Dispose()
    """
    
    try:
        # CREATE_NO_WINDOW = 0x08000000
        # Popen을 사용하여 비동기로 실행 (GUI 프리징 방지)
        subprocess.Popen(["powershell", "-Command", ps_script], creationflags=0x08000000)
    except Exception:
        pass