import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk
import json

# src 폴더를 모듈 검색 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from gui import GodModeApp
from ad_window import show_ad_window

class TestV123Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Tkinter 루트 윈도우 생성 (테스트용, 화면에 표시 안 함)
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        # 각 테스트마다 앱 인스턴스 초기화
        # 외부 의존성(소리, 파일 등) Mocking
        with patch('gui.WindowsTaskbar'), \
             patch('gui.play_sound'), \
             patch('gui.get_user_data_path', return_value='dummy_path'), \
             patch('os.path.exists', return_value=False), \
             patch.dict(os.environ, {"BANNER_SPONSORED": "true"}): # 배너 테스트를 위해 활성화
            
            self.app = GodModeApp(self.root)
            
            # 테스트를 위해 draw_timer를 Mock으로 대체 (호출 여부 확인용)
            self.app.draw_timer = MagicMock()

    def tearDown(self):
        # 생성된 팝업 등이 있다면 닫기
        if hasattr(self.app, 'ad_window') and self.app.ad_window:
            self.app.ad_window.destroy()
        for widget in self.root.winfo_children():
            widget.destroy()

    def test_ad_banner_exists(self):
        """v1.23: 메인 화면 상단에 배너 광고가 생성되었는지 테스트"""
        # 1. ad_frame 존재 여부 확인
        self.assertTrue(hasattr(self.app, 'ad_frame'), "ad_frame이 생성되지 않았습니다.")
        self.assertIsInstance(self.app.ad_frame, tk.Frame)
        
        # 2. ad_label 존재 확인
        self.assertTrue(hasattr(self.app, 'ad_label'), "ad_label이 생성되지 않았습니다.")
        
        # 이미지 배너가 로드되지 않았을 경우(테스트 환경) 텍스트 배너 확인
        if not (hasattr(self.app, 'bmc_banner_image') and self.app.bmc_banner_image):
            banner_text = self.app.ad_label.cget("text")
            self.assertIn("Coffee", banner_text, "배너 텍스트에 'Coffee' 문구가 포함되어야 합니다.")
        
        # 3. 배너가 화면 상단(TOP)에 배치되었는지 확인 (pack info)
        pack_info = self.app.ad_frame.pack_info()
        self.assertEqual(pack_info['side'], 'top', "배너가 상단에 배치되지 않았습니다.")

    def test_settings_update_redraws_timer(self):
        """v1.23: 설정 로드 시 타이머 화면이 즉시 갱신되는지 테스트"""
        # 가상의 설정 데이터
        dummy_settings = {"work_min": 50, "auto_start": True}
        
        # json.load와 open을 Mocking하여 가짜 설정 파일 읽기 시뮬레이션
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(dummy_settings))), \
             patch('json.load', return_value=dummy_settings), \
             patch('gui.get_user_data_path', return_value='settings.json'), \
             patch('os.path.exists', return_value=True):
            
            # 설정 로드 실행
            self.app.load_settings()
            
            # 1. 엔진 설정이 업데이트되었는지 확인
            self.assertEqual(self.app.engine.work_min, 50, "엔진의 집중 시간이 업데이트되지 않았습니다.")
            self.assertTrue(self.app.engine.auto_start, "엔진의 자동 시작 설정이 업데이트되지 않았습니다.")
            
            # 2. draw_timer가 호출되었는지 확인 (버그 수정 검증)
            self.app.draw_timer.assert_called()

    def test_show_ad_window(self):
        """v1.23: 광고 팝업창이 정상적으로 뜨는지 테스트"""
        # 초기 상태: 팝업 없음
        self.app.ad_window = None
        
        # 팝업 호출
        show_ad_window(self.app)
        
        # 1. 팝업 윈도우 객체 생성 확인
        self.assertIsNotNone(self.app.ad_window, "ad_window 객체가 생성되지 않았습니다.")
        self.assertTrue(self.app.ad_window.winfo_exists(), "광고 팝업창이 실제로 생성되지 않았습니다.")
        self.assertIsInstance(self.app.ad_window, tk.Toplevel)
        
        # 2. 타이틀 확인
        self.assertEqual(self.app.ad_window.title(), self.app.loc.get("ad_window_title"))

    def test_mini_mode_toggle(self):
        """미니 모드 전환 및 복귀 테스트"""
        # 윈도우 조작 메서드 Mocking (실제 GUI 동작 방지)
        self.app.root.overrideredirect = MagicMock()
        self.app.root.geometry = MagicMock(return_value="300x400+100+100")
        self.app.root.minsize = MagicMock()
        self.app.root.withdraw = MagicMock()
        self.app.root.deiconify = MagicMock()
        
        # 1. 미니 모드 진입
        with patch('gui.show_toast'): # 토스트 알림 무시
            self.app.toggle_mini_mode()
        
        self.assertTrue(self.app.is_mini_mode, "미니 모드로 전환되지 않았습니다.")
        self.app.root.overrideredirect.assert_called_with(True)
        
        # 2. 미니 모드 해제 (복귀)
        self.app.toggle_mini_mode()
        
        self.assertFalse(self.app.is_mini_mode, "일반 모드로 복귀되지 않았습니다.")
        self.app.root.overrideredirect.assert_called_with(False)

    def test_strict_mode_behavior(self):
        """엄격 모드(Strict Mode) 동작 테스트"""
        # 엄격 모드 활성화
        self.app.setting_strict_mode = True
        
        # 1. 집중 모드 실행 중 정지 시도 -> 실패해야 함
        self.app.engine.mode = "work"
        self.app.engine.is_running = True
        
        with patch('gui.show_toast') as mock_toast:
            self.app.toggle_timer() # 정지 시도
            
            # 정지되지 않고 계속 실행 중이어야 함
            self.assertTrue(self.app.engine.is_running, "엄격 모드에서 타이머가 정지되었습니다.")
            mock_toast.assert_called() # 경고 토스트 호출 확인

        # 2. 휴식 모드 실행 중 정지 시도 -> 성공해야 함 (엄격 모드는 집중 모드에만 적용)
        self.app.engine.mode = "break"
        self.app.engine.is_running = True
        
        with patch('gui.show_toast'): # 시작/정지 토스트 무시
            self.app.toggle_timer() # 정지 시도
            
            # 정지되어야 함 (reset_timer 호출됨 -> is_running False)
            self.assertFalse(self.app.engine.is_running, "휴식 모드에서는 엄격 모드가 적용되지 않아야 합니다.")

    def test_ad_banner_hidden_by_default(self):
        """BANNER_SPONSORED 환경변수가 없거나 false일 때 배너가 숨겨지는지 테스트"""
        # 환경변수가 'false'일 때 (기본값 동작 시뮬레이션)
        with patch.dict(os.environ, {"BANNER_SPONSORED": "false"}):
            with patch('gui.WindowsTaskbar'), \
                 patch('gui.play_sound'), \
                 patch('gui.get_user_data_path', return_value='dummy_path'), \
                 patch('os.path.exists', return_value=False):
                
                app = GodModeApp(self.root)
                self.assertIsNone(app.ad_frame, "BANNER_SPONSORED가 false일 때 배너가 생성되면 안 됩니다.")

    def test_load_env_exception_handling(self):
        """load_env 실행 중 파일 읽기 오류 발생 시 예외 처리 테스트"""
        # open 함수가 호출될 때 파일명에 따라 동작을 다르게 설정
        original_open = open
        def side_effect(file, *args, **kwargs):
            # .env 파일에 대해서만 IOError 발생
            if str(file).endswith('.env'):
                raise IOError("Read permission denied")
            return original_open(file, *args, **kwargs)

        # .env 파일은 존재한다고 가정(True)하지만, open 시 IOError 발생
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=side_effect), \
             patch('gui.WindowsTaskbar'), \
             patch('gui.play_sound'), \
             patch('gui.get_user_data_path', return_value='dummy_path'):
            
            # 환경변수에 BANNER_SPONSORED가 없는 상태
            with patch.dict(os.environ, {}, clear=True):
                app = GodModeApp(self.root)
                
                # 예외가 처리되어 앱이 정상 실행되고, 배너는 기본값(False)에 따라 생성되지 않아야 함
                self.assertIsNone(app.ad_frame)

    def test_popup_frequency(self):
        """집중 완료 팝업이 2회마다 뜨는지 테스트"""
        self.app.engine.mode = "work"
        self.app.setting_sound = False
        self.app.setting_auto_start = False
        
        with patch('gui.show_ad_window') as mock_show_ad, \
             patch('gui.log_godmode'), \
             patch('gui.show_toast'), \
             patch.object(self.app, 'refresh_today_count'), \
             patch.object(self.app, 'draw_timer'), \
             patch.object(self.app, 'update_topmost_status'), \
             patch.object(self.app, 'update_control_buttons_visibility'), \
             patch.object(self.app, 'enable_settings_button'), \
             patch.object(self.app, 'enable_task_entry'), \
             patch.object(self.app, 'update_start_button_color'), \
             patch.object(self.app.root, 'deiconify'), \
             patch.object(self.app.engine, 'switch_to_break', return_value=False):

            # 1회차 (홀수) -> 안 뜸
            self.app.today_count = 1
            self.app.finish_cycle()
            mock_show_ad.assert_not_called()
            
            # 2회차 (짝수) -> 뜸
            self.app.today_count = 2
            self.app.finish_cycle()
            mock_show_ad.assert_called_once()

    def test_ad_banner_policy(self):
        """AD_POPUP_POLICY에 따른 팝업 내부 배너 표시 여부 테스트"""
        # 헬퍼 함수: 팝업 내 배너 존재 여부 확인
        def has_banner(window):
            for child in window.winfo_children():
                if isinstance(child, tk.Frame):
                    for subchild in child.winfo_children():
                        # "SPONSORED" 라벨이 제거되었으므로 버튼 존재 여부로 확인
                        if isinstance(subchild, tk.Button):
                            return True
            return False

            # 1. Policy: always
            with patch.dict(os.environ, {"AD_POPUP_POLICY": "always"}):
                show_ad_window(self.app)
                self.assertTrue(has_banner(self.app.ad_window))
                self.app.ad_window.destroy()

            # 2. Policy: never
            with patch.dict(os.environ, {"AD_POPUP_POLICY": "never"}):
                show_ad_window(self.app)
                self.assertFalse(has_banner(self.app.ad_window))
                self.app.ad_window.destroy()

            # 3. Policy: random (True case)
            with patch.dict(os.environ, {"AD_POPUP_POLICY": "random"}), \
                 patch('random.random', return_value=0.4): # 0.5 미만 -> True
                show_ad_window(self.app)
                self.assertTrue(has_banner(self.app.ad_window))
                self.app.ad_window.destroy()

            # 4. Policy: random (False case)
            with patch.dict(os.environ, {"AD_POPUP_POLICY": "random"}), \
                 patch('random.random', return_value=0.6): # 0.5 이상 -> False
                show_ad_window(self.app)
                self.assertFalse(has_banner(self.app.ad_window))
                self.app.ad_window.destroy()

if __name__ == '__main__':
    unittest.main()