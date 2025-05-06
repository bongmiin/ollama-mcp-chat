# Ollama MCP Chat

Ollama MCP Chat is a desktop chatbot application that integrates Ollama's local LLM models with MCP (Model Context Protocol) servers, supporting various tool calls and extensible features. It provides a GUI based on Python and PySide6, and allows you to freely extend its capabilities via MCP servers.

This project can be very useful as base code for developers who want to create AI applications with GUI in Python.

## Key Features

- Run Ollama LLM models locally for free
- Integrate and call various tools via MCP servers
- Manage and save chat history
- Real-time streaming responses and tool call results
- Intuitive desktop GUI (PySide6-based)
- GUI support for adding, editing, and removing MCP servers

## System Requirements

- Python 3.12 or higher
- [Ollama](https://ollama.ai) installed (for local LLM execution)
- [uv](https://github.com/astral-sh/uv) (recommended for package management)
- MCP server (can be implemented or use external MCP servers)
- [smithery.ai](https://smithery.ai) (recommended for MCP repository)

## Installation

1. Clone the repository
```bash
git clone https://github.com/your-repo/ollama-mcp-chat.git
cd ollama-mcp-chat
```

2. Install uv (if not installed)
```bash
# Using pip
pip install uv

# Or using curl (Unix-like systems)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using PowerShell (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Install dependencies
```bash
# Install dependencies
uv sync
```

4. Install Ollama and download a model
- recommend [qwen3:14b](ollama run qwen3:14b)
```bash
# Install Ollama (see https://ollama.ai for details)
ollama pull <model-name>
```

5. MCP server configuration (optional)
- Add MCP server information to the `mcp_config.json` file
- Example:
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["./mcp/mcp_server_weather.py"],
      "transport": "stdio"
    }
  }
}
```

## How to Run

```bash
uv run main.py
```
- The GUI will launch, and you can start chatting and using MCP tools.

## Main Files

- `ui/chat_window.py`: Main GUI window, handles chat/history/settings/server management
- `agent/chat_history.py`: Manages and saves/loads chat history
- `worker.py`: Handles asynchronous communication with LLM and MCP servers
- `agent/llm_ollama.py`: Integrates Ollama LLM and MCP tools, handles streaming responses
- `mcp_server/mcp_manager.py`: Manages and validates MCP server configuration files

## Extending MCP Servers

1. Add new MCP server information to `mcp_config.json`
2. Implement and prepare the MCP server executable
3. Restart the application and check the MCP server list in the GUI

## Chat History

- All conversations are automatically saved to `chat_history.json`
- You can load previous chats or start a new chat from the GUI

## Exit Commands

- Type `quit`, `exit`, or `bye` in the program to exit

## Notes

- Basic LLM chat works even without MCP server configuration
- Be mindful of your PC's performance and memory usage, especially with large LLM models
- MCP servers can be implemented in Python, Node.js, or other languages, and external MCP servers are also supported

## License

MIT License
