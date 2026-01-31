import sys
import os
import shutil

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_user_data_path(filename):
    """사용자 데이터 파일 경로를 반환합니다. (Documents 폴더 우선 사용)"""
    app_name = "GodModeTimer"
    
    # 1. 영구 보존 가능한 경로 설정 (Documents)
    # MSIX 앱 삭제 시에도 Documents 폴더의 데이터는 유지됩니다.
    if sys.platform == "win32":
        base_path = os.path.join(os.path.expanduser("~"), "Documents")
    else:
        base_path = os.path.expanduser("~/.local/share")
    
    data_dir = os.path.join(base_path, app_name)
    
    # 폴더가 없으면 생성
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
        except OSError:
            pass
    
    target_path = os.path.join(data_dir, filename)
    
    # 2. 이미 새 위치(Documents)에 파일이 있으면 바로 반환
    if os.path.exists(target_path):
        return target_path
        
    # 3. 마이그레이션: 기존 데이터가 있는지 확인 (Windows MSIX/AppData)
    if sys.platform == "win32":
        old_path = None
        
        # 3-1. MSIX 컨테이너 스토리지 확인
        try:
            from winrt.windows.storage import ApplicationData
            local_folder = ApplicationData.current.local_folder.path
            msix_file = os.path.join(local_folder, filename)
            if os.path.exists(msix_file):
                old_path = msix_file
        except Exception:
            pass
            
        # 3-2. 일반 LocalAppData 확인 (fallback)
        if not old_path:
            local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            legacy_file = os.path.join(local_app_data, app_name, filename)
            if os.path.exists(legacy_file):
                old_path = legacy_file
                
        # 3-3. 데이터 발견 시 새 위치로 복사
        if old_path and os.path.exists(old_path):
            try:
                shutil.copy2(old_path, target_path)
                print(f"📦 데이터 마이그레이션 완료: {old_path} -> {target_path}")
            except Exception as e:
                print(f"⚠️ 데이터 마이그레이션 실패: {e}")

    return target_path
