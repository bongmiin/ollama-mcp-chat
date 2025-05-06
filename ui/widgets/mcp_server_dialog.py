import json

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from mcp_server.mcp_manager import MCP_ADD_TEMPLATES, MCPManager


class MCPServerDialog(QDialog):
    def __init__(self, server_name=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MCP server config")
        self.resize(500, 400)
        self.server_name = server_name
        self.mcp_manager = MCPManager()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # server name input (used when adding a new server)
        self.name_layout = QHBoxLayout()
        self.name_label = QLabel("Server name:")
        self.name_edit = QLineEdit()
        if server_name:
            self.name_edit.setText(server_name)
            self.name_edit.setReadOnly(True)
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_edit)
        self.layout.addLayout(self.name_layout)

        # show/modify JSON content
        self.json_edit = QTextEdit()
        self.layout.addWidget(self.json_edit)

        # button area
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.saveServer)
        self.button_layout.addWidget(self.save_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.deleteServer)
        self.button_layout.addWidget(self.delete_button)

        self.layout.addLayout(self.button_layout)

        # load existing server info
        self.loadServerInfo()

    def loadServerInfo(self):
        config = self.mcp_manager.getConfig()
        servers = config.get("mcpServers", {})
        if self.server_name and self.server_name in servers:
            server_data = servers[self.server_name]
            self.json_edit.setPlainText(
                json.dumps(server_data, indent=4, ensure_ascii=False)
            )
        elif self.server_name:
            self.json_edit.setPlainText('{\n    "command": "",\n    "args": []\n}')
        else:
            self.json_edit.setPlainText(
                json.dumps(MCP_ADD_TEMPLATES, indent=4, ensure_ascii=False)
            )

    def saveServer(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Enter a server name.")
            return
        try:
            server_data = json.loads(self.json_edit.toPlainText())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"JSON parsing error: {e}")
            return
        config = self.mcp_manager.getConfig()
        config["mcpServers"][name] = server_data
        valid, msg = self.mcp_manager.validateConfig(config)
        if not valid:
            QMessageBox.warning(self, "Configuration error", msg)
            return
        self.mcp_manager.saveConfig(config)
        QMessageBox.information(self, "Saved", "Server settings saved.")
        self.accept()

    def deleteServer(self):
        name = self.name_edit.text().strip()
        config = self.mcp_manager.getConfig()
        if name in config["mcpServers"]:
            del config["mcpServers"][name]
            self.mcp_manager.saveConfig(config)
            QMessageBox.information(self, "Deleted", "Server deleted.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Server does not exist.")
