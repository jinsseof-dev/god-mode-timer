import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_user_data_path(filename):
    """사용자 데이터 폴더(AppData) 내의 파일 경로를 반환합니다."""
    app_name = "GodModeTimer"
    if sys.platform == "win32":
        base_path = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base_path = os.path.expanduser("~/.local/share")
    
    data_dir = os.path.join(base_path, app_name)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    return os.path.join(data_dir, filename)
