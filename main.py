import sys
import random

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog
from PyQt6.QtGui import QPainter, QColor, QPolygonF, QPen
from PyQt6.QtCore import Qt, QTimer, QPointF

class RandomWheel(QWidget):
    SIZE = 720
    POINTER_LENGTH = int(SIZE * 0.06)
    POINTER_HEIGHT = int(SIZE * 0.0375)
    INITIAL_SPIN_STEP = 15
    SPIN_INTERVAL = 10
    MAX_SEGMENTS = 20
    FULL_CIRCLE_DEGREES = 360

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Zufallsrad")
        self.setGeometry(100, 100, int(self.SIZE*(16/9)), self.SIZE)

        self.radius = self.SIZE // 3
        self.NUM_SEGMENTS = 10
        self.angle_per_segment = self.FULL_CIRCLE_DEGREES / self.NUM_SEGMENTS
        self.current_angle = random.randint(0, self.FULL_CIRCLE_DEGREES)
        self.winning = []

        self.colors = [
            QColor(255, 50, 50), QColor(50, 255, 50), QColor(50, 50, 255),
            QColor(255, 255, 50), QColor(255, 165, 50), QColor(255, 192, 203),
            QColor(128, 50, 128), QColor(50, 255, 255), QColor(128, 128, 128),
            QColor(255, 105, 180)
        ]
        self.color_names = [
            "Rot", "Grün", "Blau", "Gelb", "Orange", "Rosa", "Lila",
            "Cyan", "Grau", "Pink"
        ]

        self.colors_label = QLabel(self._generate_colors_text(), self)
        self.colors_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.colors_label.setStyleSheet("font-size: 18px; color: white;")

        self.file_button = QPushButton("Select File", self)
        self.file_button.clicked.connect(self._select_file)
        self.spin_button = QPushButton("Spin", self)
        self._set_button_style(self.spin_button, 'green')
        self.spin_button.clicked.connect(self._spin_wheel)

        self.result_label = QLabel("Winner: ", self)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 20px; color: yellow;")

        self._layout_widgets()

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_wheel)

    def _set_button_style(self, button, color):
        button.setFixedSize(100, 100)
        button.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background-color: {color};
                font-size: 16px;
                border-radius: 50px;
                border: 2px solid white;
            }}
            QPushButton:pressed {{
                background-color: red;
            }}
        """)

    def _generate_colors_text(self):
        """Generate a string showing which color corresponds to each segment."""
        return "\n".join(f"Segment {i + 1}: {name}" for i, name in enumerate(self.color_names[:self.NUM_SEGMENTS]))

    def _select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Text Files (*.txt)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            with open(file_path, 'r') as file:
                content = [line.rstrip() for line in file]
            
            self.NUM_SEGMENTS = min(len(content), self.MAX_SEGMENTS)
            self.angle_per_segment = self.FULL_CIRCLE_DEGREES / self.NUM_SEGMENTS

            if len(self.color_names) < self.NUM_SEGMENTS:
                self.color_names.extend(['Color'] * (self.NUM_SEGMENTS - len(self.color_names)))

            color_text = "\n".join(f"{content[i]}: {self.color_names[i]}" for i in range(self.NUM_SEGMENTS))
            self.colors_label.setText(color_text)
            self.result_label.setText("Winner: ")
            self._layout_widgets()

    def _layout_widgets(self):
        self.file_button.move(20, 20)
        self.spin_button.move((self.width() - self.spin_button.width()) // 2, (self.height() - self.spin_button.height()) // 2)
        self.colors_label.move(self.width() - self.SIZE // 4, self.height() - (25 * self.NUM_SEGMENTS))
        self.result_label.move((self.width() - self.result_label.width()) // 2, self.height() - self.SIZE//16)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_widgets()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_x, center_y = self.width() // 2, self.height() // 2

        self.winning.clear()
        for i in range(self.NUM_SEGMENTS):
            start_angle = self.angle_per_segment * i + self.current_angle
            segment_color = self.colors[i % len(self.colors)]
            painter.setBrush(segment_color)
            painter.drawPie(center_x - self.radius, center_y - self.radius, self.radius * 2, self.radius * 2,
                            int(start_angle * 16), int(self.angle_per_segment * 16))
            self.winning.append((start_angle % self.FULL_CIRCLE_DEGREES, i))

        pointer_x, pointer_y = center_x, center_y - self.radius - self.POINTER_HEIGHT // 2 - 10
        pointer_polygon = QPolygonF([
            QPointF(pointer_x - self.POINTER_LENGTH // 2, pointer_y),
            QPointF(pointer_x + self.POINTER_LENGTH // 2, pointer_y),
            QPointF(pointer_x, pointer_y + self.POINTER_HEIGHT)
        ])

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor(255, 0, 0))
        painter.drawPolygon(pointer_polygon)

    def _spin_wheel(self):
        self.spin_button.setEnabled(False)
        self._set_button_style(self.spin_button, 'red')
        self.spins = random.randint(5, 8) * self.FULL_CIRCLE_DEGREES
        self.final_angle = random.randint(0, self.FULL_CIRCLE_DEGREES)
        self.total_spin = self.spins + self.final_angle
        self.current_spin = 0
        self.current_spin_step = self.INITIAL_SPIN_STEP

        self.rollback = self.total_spin // 60 + 1 if random.random() < 0.33 else 0
        self.rollback_turn = random.choice([False, True])
        self.rollback_stop = self.total_spin // 60

        self.timer.start(self.SPIN_INTERVAL)

    def _calculate_winner_index(self):
        adjusted_segments = [(start_angle, i, (self.FULL_CIRCLE_DEGREES - start_angle + 90) if start_angle > 90 else (90 - start_angle))
                             for start_angle, i in self.winning]
        return min(range(len(adjusted_segments)), key=lambda i: adjusted_segments[i][2])

    def _update_wheel(self):
        if self.current_spin < self.total_spin:
            self.current_angle = (self.current_angle + self.current_spin_step) % self.FULL_CIRCLE_DEGREES
            self.current_spin += self.current_spin_step

            remaining_spin = self.total_spin - self.current_spin
            self.current_spin_step = max(self.INITIAL_SPIN_STEP * remaining_spin // self.total_spin, 1)
            
            self.update()

        elif self.rollback < self.rollback_stop:
            if self.rollback_turn:
                self.current_angle = (self.current_angle + self.current_spin_step) % self.FULL_CIRCLE_DEGREES
            else:
                self.current_angle = (self.current_angle - self.current_spin_step) % self.FULL_CIRCLE_DEGREES

            self.current_spin_step /= 1.08
            self.rollback += 1

            self.update()
        else:
            self.timer.stop()
            winner_index = self._calculate_winner_index()
            self.result_label.setText(f"Winner: {self.color_names[winner_index]}")
            self.result_label.adjustSize()
            self.spin_button.setEnabled(True)
            self._set_button_style(self.spin_button, 'green')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wheel = RandomWheel()
    wheel.show()
    sys.exit(app.exec())
