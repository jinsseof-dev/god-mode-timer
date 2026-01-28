import json
import os
import locale
import sys

class Localization:
    def __init__(self, lang_code=None):
        self.translations = {}
        # 언어 코드가 없으면 시스템 언어 감지
        self.lang_code = lang_code if lang_code else self.get_system_language()
        self.load_language(self.lang_code)

    def get_system_language(self):
        try:
            lang, encoding = locale.getdefaultlocale()
            if lang and lang.startswith('ko'):
                return 'ko'
            if lang and lang.startswith('ja'):
                return 'ja'
        except (ValueError, TypeError):
            pass
        return 'en'

    def load_language(self, lang_code):
        self.lang_code = lang_code
        filename = f"{lang_code}.json"
        
        try:
            # Get absolute path to resource, works for dev and for PyInstaller
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.dirname(os.path.abspath(__file__))

            path = os.path.join(base_path, 'locales', filename)
            
            # 개발 환경 등에서 locales 폴더가 없을 경우 상위 경로도 확인 (Fallback)
            if not os.path.exists(path):
                path = os.path.join(base_path, filename)
            
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            else:
                # Fallback to English if the language file is not found
                if lang_code != 'en':
                    self.load_language('en')
        except Exception as e:
            print(f"Error loading language {lang_code}: {e}")
            self.translations = {}

    def get(self, key, **kwargs):
        """키에 해당하는 번역 텍스트를 반환합니다. 없으면 키 자체를 반환."""
        text = self.translations.get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text