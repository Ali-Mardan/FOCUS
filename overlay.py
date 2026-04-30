from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QCursor


class StepItem(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, index: int, text: str, is_current: bool, is_done: bool):
        super().__init__()
        self._index = index
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        status = "✓" if is_done else ("▶" if is_current else "○")
        status_label = QLabel(status)
        status_label.setFixedWidth(16)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        font = QFont()
        if is_current:
            font.setBold(True)
            text_label.setStyleSheet("color: #00d4aa;")
            status_label.setStyleSheet("color: #00d4aa;")
        elif is_done:
            text_label.setStyleSheet("color: #666;")
            status_label.setStyleSheet("color: #666;")
        else:
            text_label.setStyleSheet("color: #aaa;")
            status_label.setStyleSheet("color: #aaa;")

        text_label.setFont(font)
        layout.addWidget(status_label)
        layout.addWidget(text_label)

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        self.clicked.emit(self._index)


class OverlayWindow(QWidget):
    step_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._steps = []
        self._current = 0
        self._goal = ""
        self._dragging = False
        self._drag_pos = None
        self._setup_ui()
        self._position_window()

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setMinimumWidth(280)
        self.setMaximumWidth(320)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QPushButton {
                background-color: #16213e;
                color: #00d4aa;
                border: 1px solid #00d4aa;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00d4aa;
                color: #1a1a2e;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header bar
        header = QFrame()
        header.setStyleSheet("background-color: #0f3460; padding: 6px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)

        focus_label = QLabel("FOCUS")
        focus_label.setStyleSheet("color: #00d4aa; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(focus_label)
        header_layout.addStretch()

        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(20, 20)
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setStyleSheet("border: none; color: #aaa; font-size: 14px; background: transparent;")
        header_layout.addWidget(minimize_btn)

        outer.addWidget(header)

        # Content area
        content = QFrame()
        content.setStyleSheet("padding: 8px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        # Goal label
        self._goal_label = QLabel("Goal: —")
        self._goal_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 12px;")
        self._goal_label.setWordWrap(True)
        content_layout.addWidget(self._goal_label)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color: #333;")
        content_layout.addWidget(div)

        # Steps scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(220)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._steps_container = QWidget()
        self._steps_layout = QVBoxLayout(self._steps_container)
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(2)
        self._steps_layout.addStretch()

        scroll.setWidget(self._steps_container)
        content_layout.addWidget(scroll)

        # Progress label
        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet("color: #666; font-size: 11px;")
        content_layout.addWidget(self._progress_label)

        # Next step button
        self._next_btn = QPushButton("Mark Step Done →")
        self._next_btn.clicked.connect(self._advance_step)
        content_layout.addWidget(self._next_btn)

        outer.addWidget(content)

    def _position_window(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.adjustSize()
        self.move(screen.width() - self.width() - 20, 20)

    def set_plan(self, goal: str, steps: list[dict]):
        self._goal = goal
        self._steps = steps
        self._current = 0
        self._goal_label.setText(f"Goal: {goal}")
        self._refresh_steps()

    def _refresh_steps(self):
        # Clear existing
        while self._steps_layout.count() > 1:
            item = self._steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, s in enumerate(self._steps):
            item = StepItem(
                index=i,
                text=s["step"],
                is_current=(i == self._current),
                is_done=(i < self._current)
            )
            item.clicked.connect(self._on_step_clicked)
            self._steps_layout.insertWidget(i, item)

        total = len(self._steps)
        self._progress_label.setText(f"Step {self._current + 1} of {total}")

        if self._current >= len(self._steps) - 1:
            self._next_btn.setText("All steps done!")
            self._next_btn.setEnabled(False)
        else:
            self._next_btn.setText("Mark Step Done →")
            self._next_btn.setEnabled(True)

    def _on_step_clicked(self, index: int):
        self._current = index
        self._refresh_steps()
        self.step_changed.emit(index)

    def _advance_step(self):
        if self._current < len(self._steps) - 1:
            self._current += 1
            self._refresh_steps()
            self.step_changed.emit(self._current)

    def get_current_step(self) -> int:
        return self._current

    def flash_warning(self):
        """Flash red border briefly to signal drift."""
        self.setStyleSheet(self.styleSheet() + "QWidget { border: 2px solid #ff4444; }")
        QTimer.singleShot(1500, lambda: self.setStyleSheet(
            self.styleSheet().replace("QWidget { border: 2px solid #ff4444; }", "")
        ))

    # Allow dragging the frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._dragging = False
