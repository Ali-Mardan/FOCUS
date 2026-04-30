import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from overlay import OverlayWindow
from nudge import NudgeDialog
from monitor import WindowMonitor


class PlanWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, goal: str):
        super().__init__()
        self._goal = goal

    def run(self):
        try:
            from planner import generate_plan
            steps = generate_plan(self._goal)
            self.finished.emit(steps)
        except Exception as e:
            self.error.emit(str(e))


class SetupScreen(QWidget):
    session_started = pyqtSignal(str, list)

    def __init__(self):
        super().__init__()
        self._thread = None
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("FOCUS — Start a Session")
        self.setFixedWidth(480)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                background-color: #16213e;
                color: #fff;
                border: 1px solid #0f3460;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
            }
            QPushButton {
                background-color: #00d4aa;
                color: #1a1a2e;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #00f0c0; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Logo / title
        title = QLabel("FOCUS")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #00d4aa; letter-spacing: 6px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        tagline = QLabel("Your AI productivity co-pilot")
        tagline.setStyleSheet("color: #666; font-size: 12px;")
        tagline.setAlignment(Qt.AlignCenter)
        layout.addWidget(tagline)

        # Spacer
        layout.addSpacing(12)

        # Goal input
        goal_label = QLabel("What do you want to accomplish?")
        goal_label.setStyleSheet("font-size: 13px; color: #aaa;")
        layout.addWidget(goal_label)

        self._goal_input = QLineEdit()
        self._goal_input.setPlaceholderText("e.g. Write my resume, Study for my exam, Build the login page...")
        self._goal_input.returnPressed.connect(self._start)
        layout.addWidget(self._goal_input)

        # Start button
        self._start_btn = QPushButton("Start Focus Session")
        self._start_btn.clicked.connect(self._start)
        layout.addWidget(self._start_btn)

        # Status
        self._status = QLabel("")
        self._status.setStyleSheet("color: #666; font-size: 11px;")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)

        # How it works section
        layout.addSpacing(8)
        how_frame = QFrame()
        how_frame.setStyleSheet("background-color: #16213e; border-radius: 8px; padding: 12px;")
        how_layout = QVBoxLayout(how_frame)
        how_layout.setContentsMargins(12, 12, 12, 12)
        how_layout.setSpacing(8)

        how_title = QLabel("How it works")
        how_title.setStyleSheet("color: #00d4aa; font-weight: bold; font-size: 12px;")
        how_layout.addWidget(how_title)

        steps_text = [
            "1. Tell FOCUS what you want to accomplish",
            "2. AI breaks it into actionable steps",
            "3. A floating overlay keeps you on track",
            "4. FOCUS nudges you back if you drift",
        ]
        for s in steps_text:
            lbl = QLabel(s)
            lbl.setStyleSheet("color: #888; font-size: 11px;")
            how_layout.addWidget(lbl)

        layout.addWidget(how_frame)
        layout.addStretch()

        self.adjustSize()

    def _start(self):
        goal = self._goal_input.text().strip()
        if not goal:
            self._status.setText("Please enter a goal first.")
            return

        self._start_btn.setEnabled(False)
        self._goal_input.setEnabled(False)
        self._status.setText("AI is building your plan...")

        self._worker = PlanWorker(goal)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_plan_ready)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._on_error)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_plan_ready(self, steps: list):
        goal = self._goal_input.text().strip()
        self.session_started.emit(goal, steps)
        self.hide()

    def _on_error(self, msg: str):
        self._status.setText(f"Error: {msg}")
        self._start_btn.setEnabled(True)
        self._goal_input.setEnabled(True)


class FocusApp:
    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setQuitOnLastWindowClosed(False)

        self._setup = SetupScreen()
        self._setup.session_started.connect(self._start_session)

        self._overlay = None
        self._monitor = None
        self._nudge_open = False
        self._nudge_dlg = None

    def run(self):
        self._setup.show()
        sys.exit(self._app.exec_())

    def _start_session(self, goal: str, steps: list):
        # Create and show overlay
        self._overlay = OverlayWindow()
        self._overlay.set_plan(goal, steps)
        self._overlay.step_changed.connect(self._on_step_changed)
        self._overlay.show()

        # Start monitor
        self._monitor = WindowMonitor(interval=3)
        self._monitor.set_steps(steps)
        self._monitor.drift_detected.connect(self._on_drift)
        self._monitor.back_on_track.connect(self._on_back_on_track)
        self._monitor.start()

    def _on_step_changed(self, index: int):
        if self._monitor:
            self._monitor.set_current_step(index)

    def _on_drift(self, active_window: str, current_step: str):
        if self._nudge_open:
            return
        self._nudge_open = True
        if self._overlay:
            self._overlay.flash_warning()

        self._nudge_dlg = NudgeDialog(active_window, current_step)
        self._nudge_dlg.snoozed.connect(self._on_snooze)
        self._nudge_dlg.back_on_track.connect(self._dismiss_nudge)
        self._nudge_dlg.finished.connect(lambda _: setattr(self, '_nudge_open', False))
        self._nudge_dlg.show()

    def _dismiss_nudge(self):
        if self._nudge_dlg and self._nudge_dlg.isVisible():
            self._nudge_dlg.accept()
        self._nudge_open = False
        self._nudge_dlg = None

    def _on_snooze(self, seconds: int):
        if self._monitor:
            self._monitor.snooze(seconds)

    def _on_back_on_track(self):
        self._dismiss_nudge()


def main():
    app = FocusApp()
    app.run()


if __name__ == "__main__":
    main()
