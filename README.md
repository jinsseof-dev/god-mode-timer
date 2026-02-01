# 🍅 God-Mode Timer

생산성 향상을 위한 심플한 파이썬 뽀모도로 타이머 프로젝트입니다.
25분 집중, 5분 휴식 사이클을 기본으로 합니다.

God-Mode Timer is a productivity tool designed to help you focus and manage your time effectively using the Pomodoro technique.

---

## 🚀 v2.0.0 Roadmap (Flutter Migration)

**God-Mode Timer v2.0.0**은 **Flutter**로 재개발하여 크로스 플랫폼(Windows, macOS, Android, iOS)을 지원할 계획입니다.

### 📅 Phase 1: 설계 및 코어 이식
- [ ] **Project Structure**: Clean Architecture / MVVM 패턴 도입
- [ ] **State Management**: Riverpod 적용
- [ ] **Core Logic**: Python `TimerEngine`을 Dart로 포팅
- [ ] **Data**: Drift (SQLite) 및 shared_preferences 적용

### 🖥️ Phase 2: Windows 데스크톱 MVP (우선순위)
- [ ] **Window Control**: Frameless, Always on Top, Snap, Mini Mode 구현
- [ ] **UI**: CustomPainter 기반 고품질 렌더링
- [ ] **Features**: 시스템 트레이, 작업 표시줄 진행률, 사운드

### 📊 Phase 3: 통계 및 설정 고도화
- [ ] **Charts**: `fl_chart` 기반 일간/주간 통계 시각화
- [ ] **Localization**: `.arb` 파일을 이용한 다국어 지원
- [ ] **Migration**: v1.x 데이터(DB/JSON) 가져오기 기능

### 📱 Phase 4: 모바일 확장 (Android & iOS)
- [ ] **Responsive Design**: 모바일/데스크톱 반응형 UI
- [ ] **Background Timer**: Foreground Service(Android) 및 Live Activities(iOS)

### 🍎 Phase 5: macOS 및 배포
- [ ] **macOS**: 메뉴바 앱(Menu bar app) 지원
- [ ] **CI/CD**: GitHub Actions 자동 빌드 파이프라인
- [ ] **Distribution**: MSIX (Windows), Play Store, App Store 배포

### 🛠️ Tech Stack (v2.0.0)

| Category | Package | Description |
| :--- | :--- | :--- |
| **State Management** | `flutter_riverpod` | App state & timer logic |
| **Database** | `drift` | Log storage & stats |
| **Settings** | `shared_preferences` | User preferences |
| **Window** | `window_manager` | Desktop window control |
| **Tray** | `system_tray` | System tray icon |
| **Taskbar** | `windows_taskbar` | Taskbar progress |
| **Charts** | `fl_chart` | Statistics charts |
| **Sound** | `audioplayers` | Notifications & White noise |
| **Background** | `flutter_background_service` | Android background timer |

---

## 📊 v1.x 개발 진척률 (Progress)

**현재 상태: 지속 가능성 및 v2.0 준비 (v1.23.0.0)**
`[==========] 100%`

## 📝 v1.x 개발 일지 (History)

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
- [x] High DPI 지원 (선명한 벡터 그래픽 렌더링)
- [x] 장기 휴식 로직 (4회 집중 후 15분 휴식 제안)

### 6단계: 사용성 개선 (Usability)
- [x] 버튼 통합 (시작/정지) 및 일시정지 제거
- [x] 설정 메뉴 확장 (자동 시작, 알림음 제어)
- [x] 시인성 개선 (진한 색상, 검정 테두리)

### 7단계: 마무리 및 최적화 (Final Polish)
- [x] 프로젝트 명칭 변경 (Focus Timer -> God-Mode Timer)
- [x] 조작 피드백 사운드 추가 (틱 소리)
- [x] 렌더링 성능 최적화 (Bilinear 적용)
- [x] 시각적 완성도 향상 (색상 조정, 윤곽선 정리)

### 8단계: 스토어 정책 준수 및 최적화 (Future)
- [x] `runFullTrust` 권한 제거 가능성 검토 (Win32 앱 특성상 유지, API 의존성 최소화 완료)

### 9단계: 기능 확장 (Planned)
- [x] **통계 대시보드**: 로그 데이터를 분석하여 일간/주간 집중 성과 시각화
- [x] **할 일(Task) 집중**: 타이머와 연동된 간단한 할 일 입력 및 체크 기능
- [ ] ~~**시스템 트레이(System Tray)**~~: (v1.20에서 제거됨)
- [x] **미니 모드(Mini Mode)**: 화면 공간을 절약하는 초소형 타이머 모드

### 10단계: 사용성 강화 (v1.16)
- [x] **집중 사이클 트래커**: 긴 휴식까지 남은 횟수를 시각적으로 표시
- [x] **휴식 건너뛰기**: 휴식 중 즉시 집중 모드로 전환하는 버튼 추가
- [x] **마우스 휠 지원**: 휠 스크롤로 타이머 시간 간편 조절
- [x] **투명도 조절**: 윈도우 투명도 설정 기능 추가
- [x] **CSV 내보내기**: 설정 및 통계 창에서 로그 데이터 내보내기 지원
- [x] **단축키**: 스페이스바(시작/정지) 지원

### 11단계: 지속 가능성 (v1.18)
- [x] **집중 완료 팝업**: 집중 완료 시 축하 메시지와 함께 후원/광고 버튼 노출

### 12단계: 안정성 및 편의성 (v1.19)
- [x] **휴식 반복**: 휴식 종료 후 집중 모드로 넘어가기 전 휴식을 연장(반복)하는 기능 추가
- [x] **종료 방지**: 집중 모드 실행 중 실수로 앱을 종료하지 않도록 보호 기능 강화
- [x] **UI 개선**: High DPI 환경 대응 및 창 크기 최적화

### 13단계: UI/UX 고도화 (v1.20)
- [x] **테마 지원**: 라이트/다크 모드 설정 및 실시간 미리보기 지원
- [x] **설정 UI 개선**: 가로형 2단 레이아웃 적용, UI 크기 조절(50~200%) 슬라이더 추가
- [x] **사용자 경험 강화**: 팝업 중앙 정렬, 고해상도 아이콘(256px), 할 일 입력창 고정
- [x] **빌드 최적화**: .env 버전 연동, MSIX 인코딩 수정, 트레이 기능 제거

### 14단계: 기능 확장 및 글로벌화 (v1.22)
- [x] **다국어 지원 (Localization)**: 한국어/영어/일본어/중국어 UI 지원 (i18n)
- [x] **데이터 관리**: CSV 내보내기 및 데이터 초기화, 데이터 저장 위치 변경(내 문서 폴더)
- [x] **통계 고도화**: 시간대별 분석, 로그 수정/삭제, 인터랙션 개선
- [x] **사용성 개선**: 콘솔 창 숨김, 종료 팝업 제거, 폴더 구조 최적화

### 15단계: 지속 가능성 및 v2.0 준비 (v1.23)
- [x] **후원 연동**: 메인 화면 및 팝업에 'Buy Me a Coffee' 배너 추가 (이미지 캐싱 적용)
- [x] **정책 제어**: 환경변수(`BANNER_SPONSORED`, `AD_POPUP_POLICY`)로 배너 표시 여부 및 빈도 제어
- [x] **안정성 강화**: 이미지 다운로드 예외 처리 및 단위 테스트 추가

## 📂 프로젝트 구조 (Project Structure)

```text
god-mod-timer/
├── src/                  # 애플리케이션 소스 코드
│   ├── locales/          # 다국어 리소스 (ko.json, en.json, ja.json)
│   ├── gui.py            # 메인 GUI 진입점
│   ├── main.py           # CLI 버전 진입점
│   └── ...               # 기타 모듈 (utils, common, windows 등)
├── scripts/              # 개발 및 관리용 스크립트
│   ├── clean.ps1         # 빌드 부산물 정리
│   └── create_assets.py  # 아이콘 리소스 생성
├── store_package/        # MSIX 패키징 리소스 (아이콘, 매니페스트 등)
├── build.py              # PyInstaller 빌드 스크립트
└── build_msix.ps1        # 전체 빌드 및 패키징 자동화 스크립트
```

## � 설치 및 실행 방법 (Installation & Usage)

### 요구 사항
- Python 3.x

### 실행
```bash
python src/main.py
# GUI 버전 실행
python src/gui.py
```

## 📦 배포 및 빌드 (Deployment)

실제 서비스 배포를 위해 빌드 스크립트를 제공합니다. 아래 과정을 통해 최적화된 실행 파일(.exe)을 생성할 수 있습니다.

### 사전 준비 (.env 설정)
스토어 배포를 위해 프로젝트 루트에 `.env` 파일을 생성하고 게시자 ID를 입력해야 합니다.
```ini
PUBLISHER_ID=CN=YOUR-PUBLISHER-ID
```

```bash
# 1. 의존성 설치
python -m pip install -r requirements.txt

# 2. 빌드 스크립트 실행
python build.py
```

-생성된 파일은 `dist/` 폴더에서 확인할 수 있습니다.
+빌드가 완료되면 프로젝트 루트 폴더에 `GodModTimer.msix` 파일이 생성됩니다.
*   **v1.23**: Added banner ads and sponsored popup.
*   **v1.22**: Multi-language support & Enhanced statistics.
