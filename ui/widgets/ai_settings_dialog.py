import json

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app_settings import AppSettings


class AISettingsDialog(QDialog):
    def __init__(self, key, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modify AI settings")
        if key == "prompt":
            self.resize(500, 400)
        else:
            self.resize(400, 120)
        self.key = key
        self.app_settings = AppSettings()
        self.config = self._loadConfig(self.key)
        self.value_type = self.config.get("type", "string")
        self.value = self.config.get("value", "")
        self._initUI()

    def _loadConfig(self, key):
        # read app_settings.json directly
        with open("app_settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, {})

    def _initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(f"Setting item: {self.key}"))
        self.input_widget = None

        if self.key == "ai_service":
            # read ai_service_options from app_settings.json
            options = self._loadConfig("ai_service_options")
            self.input_widget = QComboBox()
            options_type = options.get("type", "")
            options_value = options.get("value", [])
            if options_type == "array" and options_value:
                for v in options_value:
                    self.input_widget.addItem(str(v))
            self.input_widget.setCurrentText(str(self.value))
        elif self.value_type == "string":
            if self.key == "prompt":
                self.input_widget = QTextEdit()
                self.input_widget.setPlainText(str(self.value))
            else:
                self.input_widget = QLineEdit()
                self.input_widget.setText(str(self.value))
        elif self.value_type == "int" or self.value_type == "float":
            self.input_widget = QLineEdit()
            self.input_widget.setText(str(self.value))
        elif self.value_type == "array":
            self.input_widget = QComboBox()
            for v in self.value:
                self.input_widget.addItem(str(v))
            self.input_widget.setCurrentText(str(self.value[0]) if self.value else "")
        else:
            self.input_widget = QLineEdit()
            self.input_widget.setText(str(self.value))

        layout.addWidget(self.input_widget)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.saveSettings)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def saveSettings(self):
        new_value = None
        if self.key == "ai_service":
            if isinstance(self.input_widget, QComboBox):
                new_value = self.input_widget.currentText()
        elif self.value_type == "string":
            if self.key == "prompt":
                if isinstance(self.input_widget, QTextEdit):
                    new_value = self.input_widget.toPlainText()
            else:
                if isinstance(self.input_widget, QLineEdit):
                    new_value = self.input_widget.text()
        elif self.value_type == "int":
            try:
                if isinstance(self.input_widget, QLineEdit):
                    new_value = int(self.input_widget.text())
            except Exception:
                QMessageBox.warning(self, "Error", "Enter an integer value.")
                return
        elif self.value_type == "float":
            try:
                if isinstance(self.input_widget, QLineEdit):
                    new_value = float(self.input_widget.text())
            except Exception:
                QMessageBox.warning(self, "Error", "Enter a float value.")
                return
        elif self.value_type == "array":
            if isinstance(self.input_widget, QComboBox):
                new_value = self.input_widget.currentText()
                # only one option can be selected
                if new_value not in self.value:
                    QMessageBox.warning(self, "Error", "Select a valid option.")
                    return
        else:
            if isinstance(self.input_widget, QLineEdit):
                new_value = self.input_widget.text()

        # modify app_settings.json directly
        with open("app_settings.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if self.key in data:
            data[self.key]["value"] = new_value
            with open("app_settings.json", "w", encoding="utf-8") as f2:
                json.dump(data, f2, indent=4, ensure_ascii=False)
        QMessageBox.information(self, "Saved", "Settings saved.")
        self.accept()
