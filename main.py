
### 3. 기본 Python 코드 (`src/main.py`)

가장 기본적인 CLI(명령줄 인터페이스) 버전의 타이머 코드입니다. `src` 폴더 안에 `main.py`로 저장하세요.

```python
import time
import sys

def countdown(minutes, label="집중 시간"):
    """
    주어진 분(minutes)만큼 카운트다운을 수행합니다.
    """
    seconds = minutes * 60
    
    print(f"\n--- {label} 시작 ({minutes}분) ---")
    
    try:
        while seconds > 0:
            mins, secs = divmod(seconds, 60)
            timer_format = '{:02d}:{:02d}'.format(mins, secs)
            
            # 터미널에서 덮어쓰기 방식으로 시간 출력
            sys.stdout.write(f"\r⏳ {label}: {timer_format}")
            sys.stdout.flush()
            
            time.sleep(1)
            seconds -= 1
            
        print(f"\n✅ {label} 종료! 잠시 쉬세요.\n")
        
    except KeyboardInterrupt:
        print("\n\n⛔ 타이머가 사용자에 의해 중단되었습니다.")
        sys.exit()

def start_pomodoro():
    """
    뽀모도로 사이클을 시작합니다.
    """
    work_min = 25
    break_min = 5
    
    print("🍅 뽀모도로 타이머를 시작합니다.")
    print("Ctrl+C를 누르면 종료됩니다.")
    
    cycle_count = 0
    
    while True:
        cycle_count += 1
        print(f"\n[Cycle #{cycle_count}]")
        
        # 1. 집중 시간 (25분)
        countdown(work_min, "집중")
        
        # 2. 휴식 시간 (5분)
        countdown(break_min, "휴식")
        
        user_input = input("계속 하시겠습니까? (Enter: 계속 / q: 종료): ")
        if user_input.lower() == 'q':
            print("타이머를 종료합니다. 오늘도 수고하셨습니다!")
            break

if __name__ == "__main__":
    start_pomodoro()
