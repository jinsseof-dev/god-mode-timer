import unittest
from unittest.mock import patch
import sys
import os

# src 폴더를 경로에 추가하여 모듈 import 가능하게 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from timer_engine import TimerEngine

class TestTimerEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TimerEngine()

    def test_initial_state(self):
        """초기 상태 검증"""
        self.assertEqual(self.engine.mode, "work")
        self.assertFalse(self.engine.is_running)
        self.assertEqual(self.engine.work_min, 25)
        self.assertEqual(self.engine.current_time, 25 * 60)

    def test_update_settings(self):
        """설정 업데이트 및 즉시 반영 여부 검증"""
        # 정지 상태이고 시간이 꽉 차있을 때 설정 변경 시 시간도 변경되어야 함
        self.engine.update_settings(work_min=50, short_break_min=10, long_break_min=30, interval=4, auto_start=True)
        self.assertEqual(self.engine.work_min, 50)
        self.assertEqual(self.engine.target_duration, 50 * 60)
        self.assertEqual(self.engine.current_time, 50 * 60)
        self.assertTrue(self.engine.auto_start)

    def test_update_settings_while_running(self):
        """실행 중 설정 변경 시 현재 시간에 영향을 주지 않는지 검증"""
        self.engine.mode = "work"
        self.engine.current_time = 100
        self.engine.start()
        
        # 작업 시간을 60분으로 변경
        self.engine.update_settings(work_min=60, short_break_min=5, long_break_min=15, interval=4, auto_start=False)
        
        # 설정값은 업데이트되어야 함
        self.assertEqual(self.engine.work_min, 60)
        # 하지만 현재 흐르고 있는 시간은 변경되면 안 됨
        self.assertEqual(self.engine.current_time, 100)
        
        # 리셋 후에는 변경된 설정이 적용되어야 함
        self.engine.reset()
        self.assertEqual(self.engine.current_time, 60 * 60)

    def test_start_stop(self):
        """시작/정지 상태 변경 검증"""
        self.engine.start()
        self.assertTrue(self.engine.is_running)
        self.engine.stop()
        self.assertFalse(self.engine.is_running)

    @patch('time.time')
    def test_tick(self, mock_time):
        """시간 흐름(Tick) 로직 검증"""
        # 시작 시간 설정
        start_time = 1000.0
        mock_time.return_value = start_time
        
        self.engine.start()
        self.assertEqual(self.engine.last_tick_time, start_time)
        
        # 1초 경과 시뮬레이션
        mock_time.return_value = start_time + 1.0
        finished = self.engine.tick()
        
        self.assertFalse(finished)
        self.assertAlmostEqual(self.engine.current_time, 25 * 60 - 1.0)
        
        # 타이머 종료 시뮬레이션 (목표 시간 초과)
        mock_time.return_value = start_time + 25 * 60 + 1.0 
        finished = self.engine.tick()
        
        self.assertTrue(finished)
        self.assertEqual(self.engine.current_time, 0)
        self.assertFalse(self.engine.is_running)

    @patch('time.time')
    def test_tick_overshoot(self, mock_time):
        """시간 경과가 남은 시간보다 클 때(Overshoot) 처리 검증"""
        start_time = 1000.0
        mock_time.return_value = start_time
        self.engine.start()
        
        # 10초 남았는데 15초가 경과한 상황 시뮬레이션
        self.engine.current_time = 10 
        mock_time.return_value = start_time + 15.0 
        
        finished = self.engine.tick()
        
        self.assertTrue(finished)
        self.assertEqual(self.engine.current_time, 0) # 음수가 되지 않고 0이어야 함
        self.assertFalse(self.engine.is_running)

    def test_switch_to_break(self):
        """휴식 모드 전환 및 긴 휴식/짧은 휴식 판별 검증"""
        # 짧은 휴식 (interval=4, count=1)
        is_long = self.engine.switch_to_break(today_count=1)
        self.assertFalse(is_long)
        self.assertEqual(self.engine.mode, "break")
        self.assertEqual(self.engine.target_duration, self.engine.short_break_min * 60)
        
        # 긴 휴식 (interval=4, count=4)
        is_long = self.engine.switch_to_break(today_count=4)
        self.assertTrue(is_long)
        self.assertEqual(self.engine.target_duration, self.engine.long_break_min * 60)

    def test_long_break_cycle_sequence(self):
        """연속적인 사이클에서 긴 휴식 로직 검증"""
        self.engine.long_break_interval = 4
        self.engine.short_break_min = 5
        self.engine.long_break_min = 15

        # 1, 2, 3회차는 짧은 휴식
        for i in range(1, 4):
            is_long = self.engine.switch_to_break(today_count=i)
            self.assertFalse(is_long, f"Cycle {i} should be short break")

        # 4회차는 긴 휴식
        is_long = self.engine.switch_to_break(today_count=4)
        self.assertTrue(is_long, "Cycle 4 should be long break")

    def test_switch_to_work(self):
        """집중 모드 전환 검증"""
        self.engine.mode = "break"
        self.engine.switch_to_work()
        self.assertEqual(self.engine.mode, "work")
        self.assertEqual(self.engine.target_duration, self.engine.work_min * 60)

    def test_reset(self):
        """리셋 기능 검증"""
        self.engine.current_time = 100
        self.engine.start()
        self.engine.reset()
        
        self.assertFalse(self.engine.is_running)
        self.assertEqual(self.engine.current_time, self.engine.work_min * 60)

    def test_set_duration(self):
        """수동 시간 설정 검증"""
        self.engine.set_duration(10)
        self.assertEqual(self.engine.target_duration, 10 * 60)
        self.assertEqual(self.engine.current_time, 10 * 60)
        self.assertEqual(self.engine.work_min, 10) # 집중 모드에서는 설정값도 업데이트

    def test_skip_break(self):
        """휴식 건너뛰기 로직 검증"""
        # 휴식 모드 설정
        self.engine.mode = "break"
        self.engine.start()
        
        self.engine.skip_break()
        
        # 집중 모드로 전환되고 타이머는 정지 상태여야 함
        self.assertEqual(self.engine.mode, "work")
        self.assertFalse(self.engine.is_running)
        self.assertEqual(self.engine.current_time, self.engine.work_min * 60)

        # 집중 모드에서 호출 시 아무 변화 없어야 함 (오동작 방지)
        self.engine.current_time = 100
        self.engine.skip_break()
        self.assertEqual(self.engine.current_time, 100)

    def test_repeat_break(self):
        """휴식 반복(연장) 로직 검증"""
        # 집중 모드(휴식 종료 후 대기 상태)에서 휴식 반복 요청
        self.engine.mode = "work"
        self.engine.stop()
        
        # 1회차 완료 후 휴식 반복 -> 짧은 휴식
        self.engine.repeat_break(today_count=1)
        
        self.assertEqual(self.engine.mode, "break")
        self.assertTrue(self.engine.is_running) # 즉시 시작됨
        self.assertEqual(self.engine.target_duration, self.engine.short_break_min * 60)

if __name__ == '__main__':
    unittest.main(verbosity=2)