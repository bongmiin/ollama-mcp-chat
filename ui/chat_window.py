import queue

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from agent.chat_history import ChatHistory
from app_settings import AppSettings
from constants import EVENT_DATA, EVENT_TYPE
from mcp_server.mcp_manager import MCPManager
from ui.widgets.ai_settings_dialog import AISettingsDialog
from ui.widgets.mcp_server_dialog import MCPServerDialog
from worker import Worker

BOOTSTRAP_QSS = """
QWidget {
    font-family: 'Noto Sans KR', 'Consolas', 'Segoe UI', 'Malgun Gothic', Arial, sans-serif;
    font-size: 12px;
    background: #e8e9ea;
    color: #212529;
}
QFrame[panel="sidebar"] {
    background: #e8e9ea;
    color: #212529;
    border-radius: 8px;
}
QLabel {
    font-weight: bold;
    color: #212529;
}
QListWidget, QListWidgetItem {
    background: #fff;
    color: #212529;
}
QPushButton {
    background-color: #0d6efd;
    color: #fff;
    border-radius: 4px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #0b5ed7;
}
QPushButton:disabled {
    background-color: #6c757d;
    color: #fff;
}
QLineEdit {
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 6px;
    background: #fff;
    color: #212529;
}
QLineEdit:disabled {
    background: #e8e9ea;
}
QTextEdit {
    background: #fff;
    border: 1px solid #ced4da;
    border-radius: 4px;
    color: #212529;
}
QTextEdit:disabled {
    background: #e8e9ea;
}
QTextEdit:read-only {
    background: #e8e9ea;
}
"""


class ChatWindow(QMainWindow):
    ollama_init_done = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ollama MCP Chat")
        self.setGeometry(100, 100, 900, 600)

        self.chat_history = ChatHistory()
        self.current_chat_index = -1
        self.is_new_chat = True

        # make MCPManager instance
        self.mcp_manager = MCPManager()

        # initialize config
        self.config = AppSettings().getAll()
        self.temperature = self.config.get("temperature", {}).get("value", 1)
        self.system_prompt = self.config.get("system_prompt", {}).get("value", "")
        self.llm_model = self.config.get("llm_model", {}).get("value", "")
        self.ai_service = self.config.get("ai_service", {}).get("value", "")
        self.timeout = self.config.get("timeout", {}).get("value", 5 * 60)

        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout()
        if self.main_layout:
            self.central_widget.setLayout(self.main_layout)
            self.sidebar = QFrame()
            if self.sidebar:
                self.sidebar.setFrameShape(QFrame.Shape.StyledPanel)
                self.sidebar.setProperty("panel", "sidebar")
                self.sidebar_layout = QVBoxLayout()
                if self.sidebar_layout:
                    # === Chat history section ===
                    self.chat_history_label_layout = QHBoxLayout()
                    self.chat_history_label = QLabel("Chat history")
                    self.chat_history_label_layout.addWidget(self.chat_history_label)
                    self.new_chat_button = QPushButton("New chat")
                    self.new_chat_button.setFixedWidth(80)
                    self.new_chat_button.clicked.connect(self.startNewChat)
                    self.chat_history_label_layout.addWidget(self.new_chat_button)
                    self.sidebar_layout.addLayout(self.chat_history_label_layout)

                    self.chat_history_list = QListWidget()
                    self.chat_history_list.setSizePolicy(
                        QSizePolicy(
                            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
                        )
                    )
                    self.chat_history_list.setMaximumHeight(150)
                    self.chat_history_list.itemClicked.connect(self.selectChatHistory)
                    self.sidebar_layout.addWidget(self.chat_history_list)
                    self.refreshChatHistoryList()
                    # === End Chat history section ===

                    self.servers_label_layout = QHBoxLayout()
                    self.tools_label = QLabel("MCP servers")
                    self.servers_label_layout.addWidget(self.tools_label)
                    self.servers_label_layout.addStretch()
                    self.add_server_button = QPushButton("Add")
                    self.add_server_button.setFixedWidth(60)
                    self.add_server_button.clicked.connect(self.openNewMCPServerDialog)
                    self.servers_label_layout.addWidget(self.add_server_button)
                    self.sidebar_layout.addLayout(self.servers_label_layout)

                    self.tools_list = QListWidget()
                    size_policy = QSizePolicy(
                        QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
                    )
                    self.tools_list.setSizePolicy(size_policy)
                    mcp_config = self.mcp_manager.getConfig()
                    mcp_servers = mcp_config.get("mcpServers", {})
                    for name, _server in mcp_servers.items():
                        self.tools_list.addItem(name)
                    self.tools_list.itemDoubleClicked.connect(self.openMCPServerDialog)
                    self.sidebar_layout.addWidget(self.tools_list, stretch=1)

                    self.llm_info_label = QLabel("AI settings")
                    self.sidebar_layout.addWidget(self.llm_info_label)

                    self.llm_info_list = QListWidget()
                    self.llm_info_list.addItem(f"AI service: {self.ai_service}")
                    self.llm_info_list.addItem(f"LLM model: {self.llm_model}")
                    self.llm_info_list.addItem(f"TEMP: {self.temperature}")
                    self.llm_info_list.addItem(f"Timeout: {self.timeout} (s)")
                    self.llm_info_list.addItem("Prompt: click to edit")
                    self.sidebar_layout.addWidget(self.llm_info_list)

                    self.llm_info_list.itemDoubleClicked.connect(
                        self.openAISettingDialog
                    )

                    self.sidebar_layout.addStretch()
                self.sidebar.setLayout(self.sidebar_layout)

            self.chat_area = QFrame()
            if self.chat_area:
                self.chat_area.setFrameShape(QFrame.Shape.StyledPanel)
                self.chat_layout = QVBoxLayout()
                if self.chat_layout:
                    self.chat_display = QTextEdit()
                    self.chat_display.setReadOnly(True)
                    self.chat_layout.addWidget(self.chat_display)

                    self.input_layout = QHBoxLayout()
                    self.input_line = QLineEdit()
                    shortcut = QShortcut(QKeySequence("Alt+D"), self)
                    shortcut.activated.connect(self.input_line.setFocus)
                    self.input_line.returnPressed.connect(
                        self.sendMessage
                    )  # "Enter" key to send message
                    self.input_layout.addWidget(self.input_line)
                    self.send_button = QPushButton("&Send")
                    self.send_button.clicked.connect(self.sendMessage)
                    self.input_layout.addWidget(self.send_button)
                    self.clear_button = QPushButton("&Clear")
                    self.clear_button.clicked.connect(self.clearChat)
                    self.input_layout.addWidget(self.clear_button)
                    self.chat_layout.addLayout(self.input_layout)
                self.chat_area.setLayout(self.chat_layout)

        self.main_layout.addWidget(self.sidebar, 2)
        self.main_layout.addWidget(self.chat_area, 5)

        self.setCentralWidget(self.central_widget)
        self.setStyleSheet(BOOTSTRAP_QSS)

        # async processing setup
        self.in_queue = queue.Queue()
        self.out_queue = queue.Queue()

        self.worker_thread = QThread()
        self.worker = Worker(self.in_queue, self.out_queue)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

        # check out_queue periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.checkWorkerResult)
        self.timer.start(100)  # 100ms마다 체크

        # initialize LLM, MCP
        self.agent_initialized = False
        # disable input/send button
        self.input_line.setEnabled(False)
        self.send_button.setEnabled(False)

        self.toggleInput(False)
        self.setNewChatState()
        self.chat_display.append("Initializing agent...")
        self.in_queue.put({EVENT_TYPE: "init"})

    def checkWorkerResult(self):
        try:
            while True:
                event = self.out_queue.get_nowait()
                event_type = event[EVENT_TYPE]
                if event_type == "init_done":
                    self.onInitDone()
                    self.toggleInput(True)
                elif event_type == "chat_message":
                    self.chat_display.append(event[EVENT_DATA])
                    if self.current_chat_index > -1 and self.is_new_chat is False:
                        self.chat_history.addMessage(
                            self.current_chat_index, event[EVENT_DATA]
                        )
                elif event_type == "chat_result":
                    try:
                        output = event[EVENT_DATA]["output"]
                        self.chat_display.append(output)
                        self.input_line.setFocus()
                        if self.current_chat_index > -1 and self.is_new_chat is False:
                            self.chat_history.addMessage(
                                self.current_chat_index, output
                            )
                    except KeyError:
                        print(f"Error: {event[EVENT_DATA]}")
                        self.chat_display.append("Error: output not found in response.")
                        if self.current_chat_index > -1 and self.is_new_chat is False:
                            self.chat_history.addMessage(
                                self.current_chat_index,
                                "Error: output not found in response.",
                            )
                    finally:
                        self.toggleInput(True)
                elif event_type == "chat_error":
                    self.chat_display.append(f"Error: {event[EVENT_DATA]}")
                    if self.current_chat_index > -1 and self.is_new_chat is False:
                        self.chat_history.addMessage(
                            self.current_chat_index, f"Error: {event[EVENT_DATA]}"
                        )
                    self.toggleInput(True)
                elif event_type == "system_message":
                    self.chat_display.append(event[EVENT_DATA])
                    if self.current_chat_index > -1 and self.is_new_chat is False:
                        self.chat_history.addMessage(
                            self.current_chat_index, event[EVENT_DATA]
                        )
        except queue.Empty:
            pass

    def onInitDone(self):
        print("Initialization done. Enable input.")
        self.agent_initialized = True
        self.input_line.setEnabled(True)
        self.send_button.setEnabled(True)
        self.chat_display.append("Agent initialization done. Enter your message.")

    def toggleInput(self, is_enabled=True):
        self.input_line.setEnabled(is_enabled)
        self.chat_display.setReadOnly(not is_enabled)
        self.input_line.setEnabled(is_enabled)
        self.send_button.setEnabled(is_enabled)
        self.clear_button.setEnabled(is_enabled)

    def sendMessage(self):
        message = self.input_line.text()
        if message:
            self.chat_display.append(
                f"\n-------------------------------\nYou: {message}"
            )
            self.in_queue.put({EVENT_TYPE: "chat", EVENT_DATA: message})
            self.input_line.clear()
            self.toggleInput(False)
            if self.is_new_chat:
                # if it's the first message, create a new chat and change the title, save
                title = message[:10] + ("..." if len(message) > 10 else "")
                settings_info = f"[Settings] AI: {self.ai_service}, Model: {self.llm_model}, Temp: {self.temperature}"
                self.current_chat_index = self.chat_history.createChat(
                    title, [settings_info, f"You: {message}"]
                )
                self.is_new_chat = False
                self.refreshChatHistoryList()
                self.chat_history_list.setCurrentRow(self.current_chat_index)
                self.new_chat_button.setEnabled(True)
            else:
                self.chat_history.addMessage(self.current_chat_index, f"You: {message}")

    def clearChat(self):
        self.chat_display.clear()

    def openMCPServerDialog(self, item):
        server_name = item.text()
        dialog = MCPServerDialog(server_name, self)
        if dialog.exec():
            # update the list to reflect the changes
            self.tools_list.clear()
            mcp_config = self.mcp_manager.loadConfigFile()
            mcp_servers = mcp_config.get("mcpServers", {})
            for name in mcp_servers.keys():
                self.tools_list.addItem(name)

    def openNewMCPServerDialog(self):
        dialog = MCPServerDialog(None, self)
        if dialog.exec():
            self.tools_list.clear()
            mcp_config = self.mcp_manager.loadConfigFile()
            mcp_servers = mcp_config.get("mcpServers", {})
            for name in mcp_servers.keys():
                self.tools_list.addItem(name)

    def openAISettingDialog(self, item):
        key_map = [
            "ai_service",
            "llm_model",
            "temperature",
            "timeout",
            "prompt",
        ]
        idx = self.llm_info_list.row(item)
        if idx < 0 or idx >= len(key_map):
            return
        key = key_map[idx]
        dialog = AISettingsDialog(key, self)
        if dialog.exec():
            # update the settings
            self.loadAppSettings()
            self.llm_info_list.clear()
            self.llm_info_list.addItem(f"AI service: {self.ai_service}")
            self.llm_info_list.addItem(f"LLM model: {self.llm_model}")
            self.llm_info_list.addItem(f"TEMP: {self.temperature}")
            self.llm_info_list.addItem(f"Timeout: {self.timeout} (s)")
            self.llm_info_list.addItem("System prompt: click to edit")

            # display changed settings in chat window
            changed_msg = f"[Settings changed] {key} value changed: {getattr(self, key) if hasattr(self, key) else self.system_prompt}"
            self.chat_display.append(changed_msg)

            # record changed settings in current chat history
            if self.current_chat_index >= 0 and not self.is_new_chat:
                self.chat_history.addMessage(self.current_chat_index, changed_msg)

    def loadAppSettings(self):
        self.config = AppSettings().getAll()
        self.temperature = self.config.get("temperature", {}).get("value", 1)
        self.system_prompt = self.config.get("system_prompt", {}).get("value", "")
        self.llm_model = self.config.get("llm_model", {}).get("value", "")
        self.ai_service = self.config.get("ai_service", {}).get("value", "")
        self.timeout = self.config.get("timeout", {}).get("value", 5 * 60)
        return self.config

    def closeEvent(self, event):
        self.worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        super().closeEvent(event)

    def refreshChatHistoryList(self, add_new_chat=False):
        self.chat_history_list.clear()
        for chat in self.chat_history.getChatList():
            self.chat_history_list.addItem(chat["title"])
        if add_new_chat:
            self.chat_history_list.addItem("(New chat)")

    def startNewChat(self):
        self.setNewChatState()
        # send init event to worker
        self.chat_display.append("Initializing agent...")
        self.in_queue.put({EVENT_TYPE: "reset_chat"})

    def selectChatHistory(self, item):
        idx = self.chat_history_list.row(item)
        self.current_chat_index = idx
        max_idx = self.chat_history_list.count() - 1
        # reset chat display
        self.chat_display.clear()
        if idx != max_idx or not self.is_new_chat:
            messages = self.chat_history.getMessages(self.current_chat_index)
            for msg in messages:
                self.chat_display.append(msg)
        # enable/disable new chat button
        if self.is_new_chat:
            self.new_chat_button.setEnabled(False)
        else:
            self.new_chat_button.setEnabled(True)
        # enable/disable input line
        if self.current_chat_index == max_idx:
            self.toggleInput(True)
        else:
            self.toggleInput(False)

    def setNewChatState(self):
        self.is_new_chat = True
        self.refreshChatHistoryList(add_new_chat=True)
        self.current_chat_index = self.chat_history_list.count() - 1
        self.chat_display.clear()
        self.toggleInput(True)
        self.new_chat_button.setEnabled(False)
        self.chat_history_list.setCurrentRow(self.current_chat_index)
        self.chat_history_list.scrollToItem(
            self.chat_history_list.item(self.current_chat_index),
            QAbstractItemView.ScrollHint.PositionAtCenter,
        )
        self.chat_history_list.setFocus()
