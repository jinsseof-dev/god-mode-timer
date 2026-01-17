import sys
import os
from datetime import datetime
import time
from common import get_user_data_path, resource_path
import json

def play_sound():
    """운영체제에 맞는 알림음을 재생합니다."""
    try:
        if sys.platform == "win32":
            import winsound
            sound_path = resource_path("alarm.wav")
            if os.path.exists(sound_path):
                # SND_FILENAME: 파일 이름, SND_ASYNC: 비동기 재생
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(1000, 1500)  # 1000Hz, 1.5초
        else:
            print('\a')  # Mac/Linux 기본 비프음
    except Exception:
        pass

_last_tick_time = 0

def play_tick_sound():
    """마우스 조작 시 짧은 클릭음(조약돌 소리 유사)을 재생합니다."""
    global _last_tick_time
    if time.time() - _last_tick_time < 0.05:
        return
    _last_tick_time = time.time()

    try:
        if sys.platform == "win32":
            import winsound
            sound_path = resource_path("tick.wav")
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(2000, 10)  # 2000Hz, 0.01초
    except Exception:
        pass

def log_godmode(task_name=None, duration=25, status="success"):
    """완료된 갓생(집중)을 로그 파일에 기록합니다."""
    try:
        log_path = get_user_data_path("godmode_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # JSON 형식으로 로그 데이터 구성
            log_entry = {
                "timestamp": now,
                "event": "godmode_complete",
                "duration": duration,
                "task": task_name,
                "status": status
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"💾 기록이 '{log_path}'에 저장되었습니다.")
    except Exception as e:
        print(f"\n로그 저장 실패: {e}")

def show_toast(title, message):
    """Windows 10/11 알림 센터에 토스트 메시지를 띄웁니다. (WinRT 사용)"""
    if sys.platform != "win32":
        return

    try:
        from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
        from winrt.windows.data.xml.dom import XmlDocument
    except ImportError:
        print("⚠️ WinRT 라이브러리가 없습니다. 'pip install -r requirements.txt'를 실행해주세요.")
        return

    try:
        # XML 템플릿 정의
        toast_xml = f"<toast><visual><binding template='ToastGeneric'><text>{title}</text><text>{message}</text></binding></visual></toast>"
        
        # XML 로드 및 알림 생성
        xml_doc = XmlDocument()
        xml_doc.load_xml(toast_xml)
        notification = ToastNotification(xml_doc)
        
        # 알림 표시
        # MSIX 패키지 환경에서는 인자 없이 호출해야 앱 ID를 자동으로 인식하여 작동합니다.
        # 개발 환경(python gui.py)에서는 시작 메뉴 바로가기가 없으므로 '요소 없음' 에러가 발생할 수 있습니다.
        notifier = ToastNotificationManager.create_toast_notifier()
        notifier.show(notification)
    except OSError as e:
        if e.winerror == -2147023728: # Element not found (0x80070490)
            print("ℹ️ 개발 모드 알림: MSIX 패키지가 아니어서 WinRT 알림이 표시되지 않았습니다. (설치 후 정상 작동)")
        else:
            print(f"⚠️ 알림 전송 실패 (OSError): {e}")
    except Exception as e:
        print(f"⚠️ 알림 전송 실패: {e}")