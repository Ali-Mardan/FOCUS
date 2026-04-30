import threading
import time
import win32gui
import win32process
import psutil
from PyQt5.QtCore import QObject, pyqtSignal


class WindowMonitor(QObject):
    drift_detected = pyqtSignal(str, str)  # (active_window_title, current_step)
    back_on_track = pyqtSignal()

    def __init__(self, interval=3):
        super().__init__()
        self._interval = interval
        self._steps = []
        self._current_step_index = 0
        self._running = False
        self._thread = None
        self._snoozed_until = 0
        self._last_drift_time = 0

    def set_steps(self, steps: list[dict]):
        self._steps = steps
        self._current_step_index = 0

    def set_current_step(self, index: int):
        self._current_step_index = index

    def snooze(self, seconds=300):
        self._snoozed_until = time.time() + seconds

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _get_active_window_info(self) -> tuple[str, str]:
        """Returns (window_title, exe_name) of the foreground window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd).lower()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                exe = proc.name().lower()
            except Exception:
                exe = ""
            return title, exe
        except Exception:
            return "", ""

    def _is_on_task(self, title: str, exe: str) -> bool:
        # Always allow our own app window
        if exe == "python.exe" or "focus —" in title or title == "focus":
            return True
        if not self._steps or self._current_step_index >= len(self._steps):
            return True
        allowed = self._steps[self._current_step_index].get("allowed_apps", [])
        combined = title + " " + exe
        return any(keyword.lower() in combined for keyword in allowed)

    def _run(self):
        drift_count = 0
        while self._running:
            time.sleep(self._interval)
            if time.time() < self._snoozed_until:
                continue
            title, exe = self._get_active_window_info()
            if not title:
                continue
            if self._is_on_task(title, exe):
                drift_count = 0
                self.back_on_track.emit()
            else:
                drift_count += 1
                # Only nudge after 2 consecutive drift checks (6s) to avoid false positives
                if drift_count >= 2:
                    now = time.time()
                    if now - self._last_drift_time > 30:  # don't spam nudges
                        self._last_drift_time = now
                        current_step = ""
                        if self._steps and self._current_step_index < len(self._steps):
                            current_step = self._steps[self._current_step_index]["step"]
                        self.drift_detected.emit(title, current_step)
                    drift_count = 0
