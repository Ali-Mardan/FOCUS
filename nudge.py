from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class NudgeDialog(QDialog):
    snoozed = pyqtSignal(int)       # seconds to snooze
    back_on_track = pyqtSignal()

    def __init__(self, active_window: str, current_step: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedWidth(360)

        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border: 2px solid #ff4444;
                border-radius: 8px;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Warning header
        header = QLabel("⚠ You're off track!")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(13)
        header.setFont(header_font)
        header.setStyleSheet("color: #ff4444;")
        layout.addWidget(header)

        # What they should be doing
        should_frame = QFrame()
        should_frame.setStyleSheet("background-color: #0f3460; border-radius: 4px; padding: 6px;")
        should_layout = QVBoxLayout(should_frame)
        should_layout.setContentsMargins(8, 6, 8, 6)
        should_layout.setSpacing(2)

        should_title = QLabel("You should be:")
        should_title.setStyleSheet("color: #888; font-size: 11px;")
        should_layout.addWidget(should_title)

        should_label = QLabel(current_step or "Working on your current task")
        should_label.setWordWrap(True)
        should_label.setStyleSheet("color: #00d4aa; font-weight: bold; font-size: 12px;")
        should_layout.addWidget(should_label)
        layout.addWidget(should_frame)

        # What they're actually doing
        doing_frame = QFrame()
        doing_frame.setStyleSheet("background-color: #2a1a1a; border-radius: 4px; padding: 6px;")
        doing_layout = QVBoxLayout(doing_frame)
        doing_layout.setContentsMargins(8, 6, 8, 6)
        doing_layout.setSpacing(2)

        doing_title = QLabel("You're in:")
        doing_title.setStyleSheet("color: #888; font-size: 11px;")
        doing_layout.addWidget(doing_title)

        # Truncate long window titles
        display_window = active_window[:60] + "..." if len(active_window) > 60 else active_window
        doing_label = QLabel(display_window)
        doing_label.setWordWrap(True)
        doing_label.setStyleSheet("color: #ff6666; font-size: 12px;")
        doing_layout.addWidget(doing_label)
        layout.addWidget(doing_frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        back_btn = QPushButton("Get back on track")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4aa;
                color: #1a1a2e;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #00f0c0; }
        """)
        back_btn.clicked.connect(self._on_back)
        btn_layout.addWidget(back_btn)

        snooze_btn = QPushButton("Snooze 5 min")
        snooze_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: 1px solid #555;
            }
            QPushButton:hover { color: #aaa; border-color: #aaa; }
        """)
        snooze_btn.clicked.connect(self._on_snooze)
        btn_layout.addWidget(snooze_btn)

        layout.addLayout(btn_layout)
        self._center_on_screen()

    def _center_on_screen(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.adjustSize()
        x = (screen.width() - self.width()) // 2
        y = screen.height() // 4
        self.move(x, y)

    def _on_back(self):
        self.back_on_track.emit()
        self.accept()

    def _on_snooze(self):
        self.snoozed.emit(300)
        self.reject()
