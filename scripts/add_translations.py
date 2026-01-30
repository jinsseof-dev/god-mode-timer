import json
import os

def update_locales():
    # 추가할 번역 데이터 정의
    additions = {
        "ko": {
            "data_settings_group": "데이터 관리",
            "open_data_folder": "데이터 폴더 열기"
        },
        "en": {
            "data_settings_group": "Data Management",
            "open_data_folder": "Open Data Folder"
        },
        "ja": {
            "data_settings_group": "データ管理",
            "open_data_folder": "データフォルダを開く"
        },
        "zh": {
            "data_settings_group": "数据管理",
            "open_data_folder": "打开数据文件夹"
        }
    }

    # 경로 설정 (scripts 폴더 상위 -> src/locales)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    locales_dir = os.path.join(project_root, "src", "locales")

    if not os.path.exists(locales_dir):
        os.makedirs(locales_dir)
        print(f"📁 폴더 생성됨: {locales_dir}")

    # 각 언어 파일 업데이트
    for lang, new_keys in additions.items():
        file_path = os.path.join(locales_dir, f"{lang}.json")
        
        data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Could not read {file_path}: {e}")
        
        # 기존 데이터에 새 키 병합 (덮어쓰기)
        data.update(new_keys)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"✅ Updated {lang}.json")
        except Exception as e:
            print(f"❌ Error writing {file_path}: {e}")

if __name__ == "__main__":
    update_locales()
