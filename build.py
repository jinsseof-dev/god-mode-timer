import PyInstaller.__main__
import sys
import os

def build():
    print("🚀 배포용 실행 파일 빌드를 시작합니다...")
    
    options = [
        'gui.py',                        # 메인 소스 파일
        '--name=GodModTimer',            # 실행 파일 이름 설정
        '--onefile',                     # 단일 실행 파일(.exe)로 생성
        '--noconsole',                   # GUI 프로그램이므로 콘솔 창 숨김
        '--clean',                       # 빌드 캐시 삭제
        '--hidden-import=ctypes.wintypes', # Windows API 관련 모듈 명시적 포함
        '--hidden-import=PIL',             # Pillow 라이브러리 명시적 포함
        '--hidden-import=PIL.ImageTk',     # ImageTk 모듈 명시적 포함
    ]
    
    # 리소스 파일이 존재하는 경우에만 포함 (파일이 없어도 빌드가 되도록 처리)
    resources = ['alarm.wav', 'tick.wav', 'arialbd.ttf']
    for res in resources:
        if os.path.exists(res):
            options.append(f'--add-data={res};.')
        else:
            print(f"⚠️ 경고: '{res}' 파일을 찾을 수 없어 빌드 패키지에서 제외합니다.")
    
    PyInstaller.__main__.run(options)
    
    print("\n✅ 빌드 완료! 'dist' 폴더에서 GodModTimer.exe를 확인하세요.")

if __name__ == "__main__":
    build()