import time
import sys
from utils import play_sound, log_godmode

def run_timer(minutes, message):
    seconds = minutes * 60
    print(f"\n{message} 시작 ({minutes}분)")
    print("  (Ctrl+C를 누르면 일시정지/초기화 메뉴가 나타납니다)")

    while seconds >= 0:
        try:
            mins, secs = divmod(seconds, 60)
            timer_format = '{:02d}:{:02d}'.format(mins, secs)
            sys.stdout.write(f"\r{timer_format}")
            sys.stdout.flush()
            time.sleep(1)
            seconds -= 1
        except KeyboardInterrupt:
            print("\n\n⏸  타이머가 일시정지되었습니다.")
            choice = input("  [R]esume(재개), [S]top/Reset(초기화), [Q]uit(종료): ").strip().lower()
            if choice == 's':
                print("\n⏹  타이머를 초기화합니다.")
                return False
            elif choice == 'q':
                print("\n👋 프로그램을 종료합니다.")
                sys.exit()
            print(f"▶  {message} 재개")
    
    print("\n")
    return True

def main():
    print("🍅 God-Mode Timer")

    while True:
        print("\n집중 시간을 입력하세요. (휴식 시간은 5분으로 고정됩니다)")

        try:
            work_input = input("집중 시간(분) [Enter for 25]: ").strip()
            work_minutes = int(work_input) if work_input else 25
            break_minutes = 5
        except ValueError:
            print("유효하지 않은 입력입니다. 기본값으로 시작합니다.")
            work_minutes = 25
            break_minutes = 5

        if not run_timer(work_minutes, "🍅 집중 시간"):
            continue
        
        play_sound()
        log_godmode(duration=work_minutes, status="success")
        print("🔔 딩동! 집중 시간이 끝났습니다. 휴식을 취하세요.")
        
        if not run_timer(break_minutes, "☕ 휴식 시간"):
            continue
        
        play_sound()
        print("✨ 갓생 사이클이 완료되었습니다!")
        
        if input("\n새로운 갓생 사이클을 시작하시겠습니까? (Enter: 예, n: 아니오): ").strip().lower() == 'n':
            break

if __name__ == "__main__":
    main()