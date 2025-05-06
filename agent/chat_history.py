import json
import os


class ChatHistory:
    def __init__(self, history_file="chat_history.json"):
        self.history_file = history_file
        self.chat_list = []
        self.loadHistory()

    def loadHistory(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.chat_list = data.get("chat_list", [])
        else:
            self.chat_list = []

    def saveHistory(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump({"chat_list": self.chat_list}, f, ensure_ascii=False, indent=2)

    def createChat(self, title, messages=[]):
        chat = {"title": title, "messages": messages}
        self.chat_list.append(chat)
        self.saveHistory()
        return len(self.chat_list) - 1  # Return the index of the newly created chat

    def updateChatTitle(self, chat_index, new_title):
        if 0 <= chat_index < len(self.chat_list):
            self.chat_list[chat_index]["title"] = new_title
            self.saveHistory()
        else:
            raise IndexError("Invalid chat index. Please check the index.")

    def addMessage(self, chat_index, message):
        if 0 <= chat_index < len(self.chat_list):
            self.chat_list[chat_index]["messages"].append(message)
            self.saveHistory()
        else:
            raise IndexError("Invalid chat index. Please check the index.")

    def getChatList(self):
        return self.chat_list

    def getMessages(self, chat_index):
        if 0 <= chat_index < len(self.chat_list):
            return self.chat_list[chat_index]["messages"]
        else:
            raise IndexError("Invalid chat index. Please check the index.")
