import time

class TimerEngine:
    def __init__(self):
        self.mode = "work"  # "work" or "break"
        self.break_type = None  # "short" or "long"
        self.is_running = False
        self.current_time = 25 * 60
        self.target_duration = 25 * 60
        self.last_tick_time = 0
        
        # Settings
        self.work_min = 25
        self.short_break_min = 5
        self.long_break_min = 15
        self.long_break_interval = 4
        self.auto_start = False

    def update_settings(self, work_min, short_break_min, long_break_min, interval, auto_start):
        """설정 값을 업데이트하고, 대기 상태라면 현재 시간에도 반영합니다."""
        self.work_min = work_min
        self.short_break_min = short_break_min
        self.long_break_min = long_break_min
        self.long_break_interval = interval
        self.auto_start = auto_start
        
        # 설정 변경 즉시 반영 (정지 상태이고 꽉 찬 상태일 때)
        if not self.is_running and abs(self.current_time - self.target_duration) < 1.0:
            if self.mode == "work":
                self.target_duration = self.work_min * 60
            elif self.mode == "break":
                # 현재 휴식 타입에 맞춰 시간 업데이트
                self.target_duration = (self.long_break_min if self.break_type == "long" else self.short_break_min) * 60
            self.current_time = self.target_duration

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.last_tick_time = time.time()

    def stop(self):
        self.is_running = False

    def toggle(self):
        if self.is_running:
            self.stop()
        else:
            self.start()

    def reset(self):
        self.stop()
        if self.mode == "work":
            self.target_duration = self.work_min * 60
        elif self.mode == "break":
            if self.break_type == "long":
                self.target_duration = self.long_break_min * 60
            else:
                self.target_duration = self.short_break_min * 60
        self.current_time = self.target_duration

    def tick(self):
        """시간을 업데이트합니다. 타이머가 종료되면 True를 반환합니다."""
        if not self.is_running:
            return False
            
        now = time.time()
        elapsed = now - self.last_tick_time
        self.last_tick_time = now
        
        self.current_time -= elapsed
        if self.current_time <= 0:
            self.current_time = 0
            self.is_running = False
            return True
        return False

    def set_duration(self, minutes):
        """현재 모드의 시간을 수동으로 설정합니다 (마우스 휠/클릭 등)."""
        self.target_duration = minutes * 60
        self.current_time = self.target_duration
        
        # 집중 모드일 경우 설정 값도 업데이트 (영구 저장용은 GUI에서 처리)
        if self.mode == "work":
            self.work_min = minutes

    def switch_to_break(self, today_count):
        """휴식 모드로 전환하고 휴식 시간(긴/짧은)을 결정합니다."""
        self.mode = "break"
        
        # 긴 휴식 여부 결정
        if today_count > 0 and today_count % self.long_break_interval == 0:
            self.target_duration = self.long_break_min * 60
            self.break_type = "long"
            is_long = True
        else:
            self.target_duration = self.short_break_min * 60
            self.break_type = "short"
            is_long = False
            
        self.current_time = self.target_duration
        return is_long

    def switch_to_work(self):
        """집중 모드로 전환합니다."""
        self.mode = "work"
        self.break_type = None
        self.target_duration = self.work_min * 60
        self.current_time = self.target_duration

    def skip_break(self):
        """휴식을 건너뛰고 집중 모드로 전환합니다."""
        if self.mode == "break":
            self.switch_to_work()
            self.stop()

    def repeat_break(self, today_count):
        """휴식을 반복합니다."""
        if self.mode == "work":
            self.switch_to_break(today_count)
            self.start()
