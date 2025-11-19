from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtGui import QIntValidator

class SplitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Split Segments")

        # Layouts
        layout = QVBoxLayout(self)
        input_layout = QHBoxLayout()
        button_layout = QHBoxLayout()

        # Widgets
        self.label = QLabel("Number of pieces:")
        self.line_edit = QLineEdit()
        self.line_edit.setValidator(QIntValidator(2, 100, self)) # Min 2, Max 100 pieces
        self.line_edit.setText("2")

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Assemble layouts
        input_layout.addWidget(self.label)
        input_layout.addWidget(self.line_edit)

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(input_layout)
        layout.addLayout(button_layout)

        # Connections
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_num_pieces(self):
        return int(self.line_edit.text())