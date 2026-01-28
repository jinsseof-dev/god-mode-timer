import json
import os

def update_locales():
    # 추가할 번역 데이터 정의
    additions = {
        "ko": {
            "clear_data_btn": "데이터 초기화",
            "clear_data_title": "데이터 초기화",
            "confirm_clear_data_msg": "정말로 모든 기록을 삭제하시겠습니까?\n삭제된 데이터는 복구할 수 없습니다.",
            "delete_all": "모두 삭제",
            "clear_data_success_title": "데이터 삭제 완료",
            "clear_data_success_msg": "모든 로그가 삭제되었습니다.",
            "clear_data_fail_msg": "데이터 삭제에 실패했습니다.",
            "import_csv_btn": "데이터 가져오기",
            "import_csv_title": "데이터 가져오기 (CSV)",
            "import_success_msg": "데이터 복원이 완료되었습니다.\n(성공: {success}건, 중복/건너뜀: {skipped}건)",
            "import_fail_fmt": "데이터 복원에 실패했습니다:\n{error}"
        },
        "en": {
            "clear_data_btn": "Reset Data",
            "clear_data_title": "Reset Data",
            "confirm_clear_data_msg": "Are you sure you want to delete all logs?\nThis cannot be undone.",
            "delete_all": "Delete All",
            "clear_data_success_title": "Data Cleared",
            "clear_data_success_msg": "All logs have been deleted.",
            "clear_data_fail_msg": "Failed to clear data.",
            "import_csv_btn": "Import Data",
            "import_csv_title": "Import Data (CSV)",
            "import_success_msg": "Data restore completed.\n(Success: {success}, Skipped: {skipped})",
            "import_fail_fmt": "Failed to restore data:\n{error}"
        },
        "ja": {
            "clear_data_btn": "データ初期化",
            "clear_data_title": "データ初期化",
            "confirm_clear_data_msg": "本当にすべての記録を削除しますか？\n削除されたデータは復元できません。",
            "delete_all": "すべて削除",
            "clear_data_success_title": "データ削除完了",
            "clear_data_success_msg": "すべてのログが削除されました。",
            "clear_data_fail_msg": "データの削除に失敗しました。",
            "import_csv_btn": "データ読み込み",
            "import_csv_title": "データ読み込み (CSV)",
            "import_success_msg": "データの復元が完了しました。\n(成功: {success}件, 重複/スキップ: {skipped}件)",
            "import_fail_fmt": "データの復元に失敗しました:\n{error}"
        },
        "zh": {
            "clear_data_btn": "重置数据",
            "clear_data_title": "重置数据",
            "confirm_clear_data_msg": "确定要删除所有记录吗？\n此操作无法撤销。",
            "delete_all": "全部删除",
            "clear_data_success_title": "数据已清除",
            "clear_data_success_msg": "所有日志已被删除。",
            "clear_data_fail_msg": "数据清除失败。",
            "import_csv_btn": "导入数据",
            "import_csv_title": "导入数据 (CSV)",
            "import_success_msg": "数据恢复完成。\n(成功: {success}, 跳过: {skipped})",
            "import_fail_fmt": "数据恢复失败:\n{error}"
        }
    }

    # 경로 설정 (scripts 폴더 상위 -> src/locales)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    locales_dir = os.path.join(project_root, "src", "locales")

    if not os.path.exists(locales_dir):
        print(f"❌ Error: Locales directory not found at {locales_dir}")
        return

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
