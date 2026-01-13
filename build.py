import PyInstaller.__main__
import sys

def build():
    print("🚀 배포용 실행 파일 빌드를 시작합니다...")
    
    options = [
        'gui.py',                        # 메인 소스 파일
        '--name=FocusTimer',             # 실행 파일 이름 설정
        '--onefile',                     # 단일 실행 파일(.exe)로 생성
        '--noconsole',                   # GUI 프로그램이므로 콘솔 창 숨김
        '--clean',                       # 빌드 캐시 삭제
        '--hidden-import=ctypes.wintypes', # Windows API 관련 모듈 명시적 포함
        '--hidden-import=PIL',             # Pillow 라이브러리 명시적 포함
        '--hidden-import=PIL.ImageTk',     # ImageTk 모듈 명시적 포함
        '--add-data=arialbd.ttf;.',        # 폰트 파일 패키징
    ]
    
    PyInstaller.__main__.run(options)
    
    print("\n✅ 빌드 완료! 'dist' 폴더에서 FocusTimer.exe를 확인하세요.")

if __name__ == "__main__":
    build()