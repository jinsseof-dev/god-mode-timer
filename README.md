# 🍅 Python Pomodoro Timer

생산성 향상을 위한 심플한 파이썬 뽀모도로 타이머 프로젝트입니다.
25분 집중, 5분 휴식 사이클을 기본으로 합니다.

## 📊 개발 진척률 (Progress)

**현재 상태: UI/UX 개선 및 반응형 적용 (v1.3)**
`[==========] 100%`

## 📝 개발 할 일 (To-Do List)

### 1단계: 핵심 기능 (MVP)
- [x] 프로젝트 구조 및 Git 저장소 설정
- [x] 기본 타이머 로직 구현 (CLI 기반)
- [x] 사용자 입력으로 타이머 시간 설정 기능
- [x] 휴식 시간 알림 메시지 출력

### 2단계: 기능 확장
- [x] 알림음(Sound) 추가 (집중/휴식 종료 시)
- [x] 로그 기능 (오늘 몇 번의 뽀모도로를 완료했는지 파일로 저장)
- [x] 일시정지 및 초기화 기능

### 3단계: GUI 및 배포
- [x] GUI 구현 (Tkinter 사용)
- [x] 설정 메뉴 (시간 조절 기능 추가)
- [x] 실행 파일(.exe/.app)로 패키징

### 4단계: UX 및 시각화 개선
- [x] 타이머 시각화 (원형 그래프 구현)
- [x] 부드러운 애니메이션 효과 적용
- [x] 종료 확인 팝업 및 알림 시 창 맨 앞으로 가져오기
- [x] 윈도우 타이틀 바 복구 및 표준 제어 사용
- [x] 항상 위(Always on Top) 기본 적용
- [x] 화면 가장자리 자석(Snap) 효과 추가

### 5단계: UI 고도화 (Refinement)
- [x] 반응형 윈도우 구현 (창 크기에 따라 타이머/폰트 자동 조절)
- [x] 미니멀리즘 디자인 적용 (여백 최소화, 버튼 스타일 개선)
- [x] 상태별 토스트 알림 추가 (일시정지 등)

## 🚀 설치 및 실행 방법 (Installation & Usage)

### 요구 사항
- Python 3.x

### 실행
```bash
python src/main.py
# GUI 버전 실행
python gui.py
```

## 📦 패키징 (Packaging)

PyInstaller를 사용하여 실행 파일(.exe)을 생성할 수 있습니다.

```bash
pip install pyinstaller

# 콘솔 창 없이 실행되는 단일 파일 생성
pyinstaller --noconsole --onefile --name="PomodoroTimer" gui.py
```

생성된 파일은 `dist/` 폴더에서 확인할 수 있습니다.
