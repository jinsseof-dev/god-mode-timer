import PyInstaller.__main__
import sys
import os
import wave
import math
import struct
import shutil

def create_dummy_wav(filename, duration=0.5, freq=440):
    """간단한 비프음 WAV 파일을 생성합니다."""
    if os.path.exists(filename): return
    
    print(f"🔊 리소스 생성: {filename}")
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    try:
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            
            data = []
            for i in range(n_samples):
                t = float(i) / sample_rate
                value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * t))
                data.append(struct.pack('<h', value))
            f.writeframes(b''.join(data))
    except Exception as e:
        print(f"⚠️ WAV 생성 실패: {e}")

def ensure_resources():
    """빌드에 필요한 리소스가 없으면 생성하거나 시스템에서 복사합니다."""
    # 1. 알림음 생성 (없을 경우)
    create_dummy_wav("alarm.wav", duration=1.0, freq=880) # A5
    create_dummy_wav("tick.wav", duration=0.05, freq=2000) # High pitch tick
    
    # 2. 폰트 복사 (Windows 환경인 경우)
    font_file = "arialbd.ttf"
    if not os.path.exists(font_file) and sys.platform == "win32":
        sys_font = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", font_file)
        if os.path.exists(sys_font):
            try:
                print(f"🔤 폰트 복사: {sys_font} -> {font_file}")
                shutil.copy(sys_font, font_file)
            except Exception as e:
                print(f"⚠️ 폰트 복사 실패: {e}")

def build():
    print(" 배포용 실행 파일 빌드를 시작합니다...")
    
    # 리소스 자동 준비
    ensure_resources()
    
    options = [
        'gui.py',                        # 메인 소스 파일
        '--name=GodModTimer',            # 실행 파일 이름 설정
        '--onefile',                     # 단일 실행 파일(.exe)로 생성
        '--noconsole',                   # GUI 프로그램이므로 콘솔 창 숨김
        '--clean',                       # 빌드 캐시 삭제
        '--hidden-import=ctypes.wintypes', # Windows API 관련 모듈 명시적 포함
        '--hidden-import=PIL',             # Pillow 라이브러리 명시적 포함
        '--hidden-import=PIL.ImageTk',     # ImageTk 모듈 명시적 포함
        '--hidden-import=winrt.windows.ui.notifications', # WinRT 알림 모듈
        '--hidden-import=winrt.windows.data.xml.dom',     # WinRT XML 모듈
        '--hidden-import=pystray',         # 시스템 트레이 모듈
    ]
    
    # 리소스 파일이 존재하는 경우에만 포함 (파일이 없어도 빌드가 되도록 처리)
    resources = ['alarm.wav', 'tick.wav', 'arialbd.ttf']
    for res in resources:
        if os.path.exists(res):
            options.append(f'--add-data={res};.')
        else:
            print(f"ℹ️ 알림: '{res}' 파일이 없습니다. 앱 실행 시 시스템 기본값(비프음/폰트)이 사용됩니다.")
    
    PyInstaller.__main__.run(options)
    
    print("\n✅ 빌드 완료! 'dist' 폴더에서 GodModTimer.exe를 확인하세요.")

if __name__ == "__main__":
    build()