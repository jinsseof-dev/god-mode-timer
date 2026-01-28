import PyInstaller.__main__
import sys
import os
import shutil
import re

def ensure_resources():
    """빌드에 필요한 리소스가 없으면 생성하거나 시스템에서 복사합니다."""
    # 1. 폰트 복사 (Windows 환경인 경우)
    font_file = "arialbd.ttf"
    if not os.path.exists(font_file) and sys.platform == "win32":
        sys_font = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", font_file)
        if os.path.exists(sys_font):
            try:
                print(f"🔤 폰트 복사: {sys_font} -> {font_file}")
                shutil.copy(sys_font, font_file)
            except Exception as e:
                print(f"⚠️ 폰트 복사 실패: {e}")

def get_version():
    """앱 버전을 추출합니다 (.env 우선)."""
    # 1. .env 파일 확인
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("VERSION="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except:
            pass

    # 2. src/gui.py 확인 (Fallback)
    try:
        with open(os.path.join("src", "gui.py"), "r", encoding="utf-8") as f:
            content = f.read()
            # self.app_version = os.environ.get("VERSION", "v1.20") 패턴 처리
            match = re.search(r'self\.app_version\s*=\s*os\.environ\.get\("VERSION",\s*["\']v?([\d\.]+)["\']\)', content)
            if match:
                return match.group(1)
            # 기존 패턴 처리
            match = re.search(r'self\.app_version\s*=\s*["\']v?([\d\.]+)["\']', content)
            if match:
                return match.group(1)
    except Exception:
        pass
    return "1.0.0"

def generate_manifest(version, exe_name):
    """템플릿과 .env 파일을 사용하여 AppxManifest.xml을 생성합니다."""
    template_path = os.path.join("store_package", "AppxManifest.template.xml")
    output_path = os.path.join("store_package", "AppxManifest.xml")
    env_path = ".env"
    
    if not os.path.exists(template_path):
        print("⚠️ 템플릿 파일(AppxManifest.template.xml)이 없습니다.")
        return

    # .env 로드
    env = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env[key] = value
    else:
        print(f"⚠️ 경고: '{env_path}' 파일이 없습니다. 매니페스트 생성 시 환경 변수가 적용되지 않습니다.")
    
    # 템플릿 읽기 및 치환
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 환경변수 치환
    for key, value in env.items():
        content = content.replace(f"${{{key}}}", value)
        
    # 버전 정보 치환 (MSIX는 Major.Minor.Build.Revision 4자리 형식 필요)
    msix_version = version
    if len(version.split('.')) == 2:
        msix_version = f"{version}.0.0"
    elif len(version.split('.')) == 3:
        msix_version = f"{version}.0"
    content = content.replace("${VERSION}", msix_version)
    
    # 실행 파일 이름 업데이트 (매니페스트 내 참조 수정)
    content = content.replace("GodModTimer.exe", exe_name)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Manifest 생성 완료: {output_path}")

def create_app_manifest():
    """High DPI 설정을 포함한 실행 파일용 매니페스트를 생성합니다."""
    manifest_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/PM</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
</assembly>"""
    with open("app.manifest", "w", encoding="utf-8") as f:
        f.write(manifest_content)

def build():
    print(" 배포용 실행 파일 빌드를 시작합니다...")
    
    # 버전 추출
    version = get_version()
    exe_name = f"GodModTimer_v{version}.exe"
    print(f"ℹ️ 앱 버전: {version} (빌드 파일명: {exe_name})")

    # 리소스 자동 준비
    ensure_resources()
    
    # 매니페스트 생성
    generate_manifest(version, exe_name)
    
    # 실행 파일용 매니페스트 생성 (High DPI)
    create_app_manifest()
    
    options = [
        os.path.join('src', 'gui.py'),   # 메인 소스 파일 (src 폴더로 변경)
        f'--name={os.path.splitext(exe_name)[0]}', # 실행 파일 이름 설정 (확장자 제외)
        '--onefile',                     # 단일 실행 파일(.exe)로 생성
        '--noconsole',                   # GUI 프로그램이므로 콘솔 창 숨김
        '--clean',                       # 빌드 캐시 삭제
        '--hidden-import=ctypes.wintypes', # Windows API 관련 모듈 명시적 포함
        '--hidden-import=PIL',             # Pillow 라이브러리 명시적 포함
        '--hidden-import=PIL.ImageTk',     # ImageTk 모듈 명시적 포함
        '--hidden-import=winrt.windows.ui.notifications', # WinRT 알림 모듈
        '--hidden-import=winrt.windows.data.xml.dom',     # WinRT XML 모듈
        '--hidden-import=winrt.windows.storage', # WinRT 스토리지 모듈
        '--manifest=app.manifest',         # High DPI 매니페스트 포함
        '--paths=src',                     # 소스 경로 추가 (모듈 임포트 해결)
    ]
    
    # 리소스 파일이 존재하는 경우에만 포함 (파일이 없어도 빌드가 되도록 처리)
    resources = ['arialbd.ttf']
    for res in resources:
        if os.path.exists(res):
            options.append(f'--add-data={res};.')
        else:
            print(f"ℹ️ 알림: '{res}' 파일이 없습니다. 앱 실행 시 시스템 기본값(비프음/폰트)이 사용됩니다.")
    
    PyInstaller.__main__.run(options)
    
    print(f"\n✅ 빌드 완료! 'dist' 폴더에서 {exe_name}를 확인하세요.")

if __name__ == "__main__":
    build()