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
import sqlite3

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

_db_initialized = False

def get_db_connection():
    """SQLite 데이터베이스 연결을 반환하고, 필요 시 테이블 생성 및 마이그레이션을 수행합니다."""
    global _db_initialized
    db_path = get_user_data_path("godmode_log.db")
    
    # 최초 실행 시 테이블 생성 및 데이터 이관
    if not _db_initialized:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        # 테이블 생성
        c.execute('''CREATE TABLE IF NOT EXISTS logs
                     (timestamp TEXT PRIMARY KEY, event TEXT, duration INTEGER, task TEXT, status TEXT)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp)''')
        conn.commit()
        
        # 기존 텍스트 로그 파일이 있다면 DB로 마이그레이션
        txt_path = get_user_data_path("godmode_log.txt")
        if os.path.exists(txt_path):
            print("🔄 기존 로그를 SQLite 데이터베이스로 이관 중...")
            migrated_count = 0
            skipped_count = 0
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        try:
                            # JSON 파싱
                            entry = json.loads(line)
                            ts = entry.get("timestamp")
                            dur = entry.get("duration", 25)
                            task = entry.get("task")
                            status = entry.get("status", "success")
                            
                            if ts:
                                c.execute("INSERT OR IGNORE INTO logs (timestamp, event, duration, task, status) VALUES (?, ?, ?, ?, ?)", 
                                          (ts, "godmode_complete", dur, task, status))
                                if c.rowcount > 0:
                                    migrated_count += 1
                                else:
                                    skipped_count += 1
                        except (json.JSONDecodeError, sqlite3.Error):
                            continue
                conn.commit()
                # 이관 완료 후 원본 파일 이름 변경 (백업)
                backup_path = txt_path + ".migrated"
                if os.path.exists(backup_path):
                    backup_path = txt_path + f".migrated_{int(time.time())}"
                
                os.rename(txt_path, backup_path)
                print(f"✅ 데이터 이관 완료. (성공: {migrated_count}, 중복/건너뜀: {skipped_count})")
            except Exception as e:
                print(f"⚠️ 데이터 이관 실패: {e}")
        
        conn.close()
        _db_initialized = True

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def log_godmode(task_name=None, duration=25, status="success"):
    """완료된 갓생(집중)을 DB에 기록합니다."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO logs (timestamp, event, duration, task, status) VALUES (?, ?, ?, ?, ?)",
                  (now, "godmode_complete", duration, task_name, status))
        conn.commit()
        conn.close()
        print(f"💾 기록이 DB에 저장되었습니다.")
    except Exception as e:
        print(f"\n로그 저장 실패: {e}")

def export_csv(parent, loc=None):
    """DB 데이터를 CSV 파일로 내보냅니다."""
    file_path = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title=loc.get("export_csv_title") if loc else "CSV로 내보내기",
        initialfile=f"godmode_logs_{datetime.now().strftime('%Y%m%d')}.csv"
    )

    if not file_path:
        return

    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT timestamp, duration, task, status FROM logs ORDER BY timestamp DESC")
        rows = c.fetchall()
        conn.close()

        if not rows:
            title = loc.get("notice") if loc else "알림"
            msg = loc.get("no_log_msg") if loc else "기록된 로그가 없습니다."
            messagebox.showinfo(title, msg, parent=parent)
            return

        with open(file_path, "w", encoding="utf-8-sig", newline="") as f_out:
            writer = csv.writer(f_out)
            writer.writerow(["Timestamp", "Duration (min)", "Task", "Status"])
            
            for row in rows:
                writer.writerow([row['timestamp'], row['duration'], row['task'] or "", row['status']])

        title = loc.get("done") if loc else "완료"
        msg = loc.get("export_success_msg") if loc else "CSV 내보내기가 완료되었습니다."
        messagebox.showinfo(title, msg, parent=parent)
    except Exception as e:
        title = loc.get("error") if loc else "오류"
        msg = loc.get("export_fail_fmt", error=e) if loc else f"내보내기 실패: {e}"
        messagebox.showerror(title, msg, parent=parent)

def import_csv(parent, loc=None):
    """CSV 파일에서 로그 데이터를 읽어 DB에 복원합니다."""
    file_path = filedialog.askopenfilename(
        parent=parent,
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title=loc.get("import_csv_title") if loc else "CSV 데이터 가져오기"
    )

    if not file_path:
        return

    success_count = 0
    skipped_count = 0

    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    ts = row.get("Timestamp")
                    dur = row.get("Duration (min)")
                    task = row.get("Task")
                    status = row.get("Status", "success")
                    
                    if ts and dur:
                        # 날짜 형식 유효성 검사 (YYYY-MM-DD HH:MM:SS)
                        datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                        
                        c.execute("INSERT OR IGNORE INTO logs (timestamp, event, duration, task, status) VALUES (?, ?, ?, ?, ?)", 
                                  (ts, "godmode_complete", int(dur), task, status))
                        
                        if c.rowcount > 0:
                            success_count += 1
                        else:
                            skipped_count += 1
                except (ValueError, sqlite3.Error):
                    continue
        
        conn.commit()
        conn.close()

        title = loc.get("done") if loc else "완료"
        msg_fmt = loc.get("import_success_msg") if loc else "데이터 복원 완료 (성공: {success}, 중복: {skipped})"
        msg = msg_fmt.format(success=success_count, skipped=skipped_count)
        messagebox.showinfo(title, msg, parent=parent)
        
    except Exception as e:
        title = loc.get("error") if loc else "오류"
        msg_fmt = loc.get("import_fail_fmt", error=str(e)) if loc else f"복원 실패: {e}"
        messagebox.showerror(title, msg_fmt, parent=parent)

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

def delete_log(target_timestamp):
    """특정 타임스탬프의 로그를 DB에서 삭제합니다."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM logs WHERE timestamp = ?", (target_timestamp,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def update_log(target_timestamp, new_task_name):
    """특정 타임스탬프의 로그(작업명)를 DB에서 수정합니다."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE logs SET task = ? WHERE timestamp = ?", (new_task_name, target_timestamp))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def clear_all_logs():
    """DB의 모든 로그 데이터를 삭제합니다."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM logs")
        conn.commit()
        c.execute("VACUUM")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def parse_logs(days=30):
    """DB를 읽어 최근 N일간의 날짜별 집중 횟수와 시간을 계산합니다."""
    # 기준 날짜 설정 (오늘로부터 days일 전)
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

    daily_stats = {}
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 날짜별 그룹화 쿼리 (SQLite substr 사용)
        # timestamp 형식: YYYY-MM-DD HH:MM:SS
        # substr(timestamp, 1, 10) -> YYYY-MM-DD
        query = """
            SELECT 
                substr(timestamp, 1, 10) as date_key,
                COUNT(*) as count,
                SUM(duration) as total_duration
            FROM logs 
            WHERE timestamp >= ? AND status = 'success'
            GROUP BY date_key
        """
        c.execute(query, (cutoff_str,))
        rows = c.fetchall()
        conn.close()

        for row in rows:
            date_key = row['date_key']
            daily_stats[date_key] = {
                'count': row['count'],
                'duration': row['total_duration'] if row['total_duration'] else 0,
                'tasks': [] # 호환성을 위해 빈 리스트 유지
            }
    except Exception:
        pass
    return daily_stats

def get_task_stats(days=30, date_filter=None):
    """DB에서 작업별 통계를 집계하여 반환합니다."""
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    task_stats = []
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        if date_filter:
            # 특정 날짜 필터링 (date_filter: YYYY-MM-DD)
            query = """
                SELECT task, SUM(duration) as total_duration
                FROM logs 
                WHERE timestamp >= ? AND status = 'success' AND substr(timestamp, 1, 10) = ?
                GROUP BY task
                ORDER BY total_duration DESC
            """
            c.execute(query, (cutoff_str, date_filter))
        else:
            # 전체 기간
            query = """
                SELECT task, SUM(duration) as total_duration
                FROM logs 
                WHERE timestamp >= ? AND status = 'success'
                GROUP BY task
                ORDER BY total_duration DESC
            """
            c.execute(query, (cutoff_str,))
            
        rows = c.fetchall()
        conn.close()
        
        total_sum = sum(row['total_duration'] for row in rows)
        
        for row in rows:
            task = row['task'] or "-"
            duration = row['total_duration']
            pct = (duration / total_sum * 100) if total_sum > 0 else 0
            task_stats.append((task, duration, pct))
            
    except Exception:
        pass
    return task_stats

def get_recent_logs(days=30):
    """최근 N일간의 로그 기록을 DB에서 조회하여 반환합니다 (최신순)."""
    logs = []
    has_more = False
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 범위 내 로그 조회
        c.execute("SELECT * FROM logs WHERE timestamp >= ? ORDER BY timestamp DESC", (cutoff_str,))
        rows = c.fetchall()
        
        # 2. 더 오래된 로그가 있는지 확인 (has_more)
        c.execute("SELECT 1 FROM logs WHERE timestamp < ? LIMIT 1", (cutoff_str,))
        has_more = c.fetchone() is not None
        
        conn.close()

        for row in rows:
            try:
                end_dt = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
                duration = int(row['duration'])
                start_dt = end_dt - timedelta(minutes=duration)
                
                logs.append({
                    "start": start_dt,
                    "end": end_dt,
                    "duration": duration,
                    "task": row['task'] or "-",
                    "timestamp_str": row['timestamp']
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