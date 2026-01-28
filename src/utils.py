import sys
import os
from datetime import datetime, timedelta
import time
from common import get_user_data_path
import json
import threading
import csv
from tkinter import filedialog, messagebox
import webbrowser

def play_sound():
    """운영체제에 맞는 알림음을 재생합니다 (시스템 비프음 사용)."""
    try:
        if sys.platform == "win32":
            import winsound
            # UI 프리징 방지를 위해 별도 스레드에서 재생
            def _beep():
                # '딩-동' 느낌의 비프음 패턴
                winsound.Beep(880, 400)  # A5
                time.sleep(0.05)
                winsound.Beep(698, 600)  # F5
            
            threading.Thread(target=_beep, daemon=True).start()
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
            # 아주 짧은 고음 비프음 (블로킹이어도 5ms라 체감 없음)
            winsound.Beep(1200, 5)
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

def export_csv(parent):
    """로그 데이터를 CSV 파일로 내보냅니다."""
    log_path = get_user_data_path("godmode_log.txt")
    if not os.path.exists(log_path):
        messagebox.showinfo("알림", "기록된 로그가 없습니다.", parent=parent)
        return

    file_path = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title="CSV로 내보내기",
        initialfile=f"godmode_logs_{datetime.now().strftime('%Y%m%d')}.csv"
    )

    if not file_path:
        return

    try:
        with open(log_path, "r", encoding="utf-8") as f_in, \
             open(file_path, "w", encoding="utf-8-sig", newline="") as f_out:
            
            writer = csv.writer(f_out)
            writer.writerow(["Timestamp", "Duration (min)", "Task", "Status"])
            
            for line in f_in:
                line = line.strip()
                if not line: continue
                
                try:
                    data = json.loads(line)
                    writer.writerow([
                        data.get("timestamp", ""),
                        data.get("duration", 25),
                        data.get("task") or "",
                        data.get("status", "success")
                    ])
                except json.JSONDecodeError:
                    # 기존 텍스트 형식 파싱 (하위 호환성)
                    if "]" in line:
                        parts = line.split("]")
                        timestamp = parts[0].strip("[")
                        task = ""
                        if "-" in parts[1]:
                            task = parts[1].split("-", 1)[1].strip()
                        writer.writerow([timestamp, 25, task, "success"])
                    
        messagebox.showinfo("완료", "CSV 내보내기가 완료되었습니다.", parent=parent)
    except Exception as e:
        messagebox.showerror("오류", f"내보내기 실패: {e}", parent=parent)

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
            pass
        else:
            print(f"⚠️ 알림 전송 실패 (OSError): {e}")
    except Exception as e:
        print(f"⚠️ 알림 전송 실패: {e}")

def parse_logs(days=30):
    """로그 파일을 읽어 최근 N일간의 날짜별 집중 횟수와 시간을 계산합니다."""
    log_path = get_user_data_path("godmode_log.txt")
    if not os.path.exists(log_path):
        return {}
    
    # 기준 날짜 설정 (오늘로부터 days일 전)
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_date = cutoff_date.replace(hour=0, minute=0, second=0, microsecond=0)

    daily_stats = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                timestamp_str = None
                duration = 25
                status = "success"
                task_name = None
                
                # 1. JSON 파싱 시도
                try:
                    entry = json.loads(line)
                    timestamp_str = entry.get("timestamp")
                    duration = entry.get("duration", 25)
                    status = entry.get("status", "success")
                    task_name = entry.get("task")
                except json.JSONDecodeError:
                    # 2. 기존 텍스트 형식 파싱 (하위 호환성)
                    if "]" in line:
                        parts = line.split("]")
                        timestamp_str = parts[0].strip("[")
                        if len(parts) > 1 and "-" in parts[1]:
                            task_name = parts[1].split("-", 1)[1].strip()
                
                if timestamp_str:
                    try:
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if dt < cutoff_date:
                            continue

                        date_key = dt.strftime("%Y-%m-%d")
                        
                        if date_key not in daily_stats:
                            daily_stats[date_key] = {'count': 0, 'duration': 0, 'tasks': []}
                        
                        if status == "success":
                            daily_stats[date_key]['count'] += 1
                            daily_stats[date_key]['duration'] += int(duration)
                            if task_name:
                                daily_stats[date_key]['tasks'].append(task_name)
                    except ValueError:
                        continue
    except Exception:
        pass
    return daily_stats

def get_recent_logs(days=30):
    """최근 N일간의 로그 기록을 파싱하여 반환합니다 (최신순)."""
    log_path = get_user_data_path("godmode_log.txt")
    logs = []
    has_more = False
    if not os.path.exists(log_path):
        return logs, has_more
    
    cutoff_date = datetime.now() - timedelta(days=days)

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # 파일 전체를 읽어서 역순으로 처리
            lines = f.readlines()
            for line in reversed(lines):
                line = line.strip()
                if not line: continue
                
                timestamp_str = None
                duration = 25
                task_name = "-"
                
                try:
                    entry = json.loads(line)
                    timestamp_str = entry.get("timestamp")
                    duration = int(entry.get("duration", 25))
                    task_name = entry.get("task") or "-"
                except json.JSONDecodeError:
                    if "]" in line:
                        parts = line.split("]")
                        timestamp_str = parts[0].strip("[")
                        if len(parts) > 1 and "-" in parts[1]:
                            task_name = parts[1].split("-", 1)[1].strip()
                
                if timestamp_str:
                    try:
                        end_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        # 기준 날짜보다 오래된 기록이 나오면 중단 (역순 탐색이므로 이후는 모두 과거 데이터)
                        if end_dt < cutoff_date:
                            has_more = True
                            break

                        start_dt = end_dt - timedelta(minutes=duration)
                        logs.append({
                            "start": start_dt,
                            "end": end_dt,
                            "duration": duration,
                            "task": task_name
                        })
                    except ValueError:
                        continue
    except Exception:
        pass
    return logs, has_more

def get_side_position(root, width, height, offset=10):
    """메인 윈도우 우측(공간 부족 시 좌측)에 팝업 위치를 반환합니다."""
    main_x = root.winfo_x()
    main_y = root.winfo_y()
    main_w = root.winfo_width()
    
    # 기본적으로 우측에 배치
    x = main_x + main_w + offset
    y = main_y
    
    # 화면 너비를 벗어나면 좌측에 배치
    screen_width = root.winfo_screenwidth()
    if x + width > screen_width:
        x = main_x - width - offset
        
    return f"+{x}+{y}"


def open_url(url):
    """기본 웹 브라우저에서 URL을 엽니다."""
    webbrowser.open(url)