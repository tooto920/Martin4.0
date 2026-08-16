# Martin - Local AI Desktop Assistant v3.0

Martin is a modular, local AI desktop assistant for Windows, built with privacy and extensibility in mind. It runs entirely on your hardware using Ollama with Gemma 3 4B.

## Features (Phase 3.0)

- **Local AI Conversation**: Chat with Gemma 3 4B via Ollama
- **Voice Input**: Press-and-hold mic button for speech-to-text via faster-whisper
- **Voice Output Hook**: TTS path prepared for Piper (non-blocking, toggle in chat)
- **Live Dashboard**: Real-time CPU/RAM/GPU/VRAM monitoring, Ollama status, MSFS integration
- **MSFS Integration**: Aircraft name and flight data polling from MSFS 2024
- **Configurable**: YAML-based configuration
- **Structured Logging**: Rotating file logs
- **Memory System**: SQLite-based short-term and long-term memory
- **Tool Registry**: Extensible tool system with safety levels
- **Modern GUI**: PySide6-based dark theme dashboard

## Planned Features (Future Phases)

- Full SimConnect integration with live flight telemetry
- Wake Word Detection
- Computer Control (apps, files, volume, keyboard/mouse)
- Web Search
- Knowledge/RAG System
- More voice models and languages

## Requirements

- Windows 10/11
- Python 3.12+
- Ollama installed and running
- Gemma 3 4B model (`ollama pull gemma3:4b`)
- Optional: faster-whisper, piper-tts for voice features

## Installation

```bash
# Clone or navigate to project
cd Martin-1.0

# Create virtual environment (the launcher does this automatically)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve

# Pull the model (the launcher does this automatically)
ollama pull gemma3:4b
```

## Running Martin

Double-click `Martin.bat` to launch the GUI. The launcher will:
1. Activate the virtual environment (create it if missing)
2. Start Ollama if it is not already running
3. Pull `gemma3:4b` if it is not already available
4. Open the Martin GUI

Alternatively, from a terminal:
```bash
python -m app.gui_main
```

## Usage

Start chatting in Czech (default language) by typing in the chat panel. Press and hold the microphone button to use voice input.

Special commands:
- `konec` / `exit` / `quit` - Exit chat session
- `paměť` - Show long-term memories
- `zapomeň` - Clear conversation history
- `zapamatuj si <text>` - Save to long-term memory

## Project Structure

```
Martin-1.0/
├── Martin.bat                 # Desktop launcher
├── app/
│   ├── gui_main.py            # GUI entry point
│   ├── main.py                # CLI entry point
│   ├── core/                  # Core infrastructure
│   ├── ai/                    # AI components (Ollama, agent, prompts)
│   ├── gui/                   # PySide6 GUI (dashboard, chat, settings)
│   ├── voice/                 # STT/TTS (faster-whisper, piper)
│   ├── memory/                # SQLite memory
│   ├── computer/              # System monitoring
│   └── integrations/          # MSFS and future integrations
├── config/
│   └── config.yaml            # Configuration
├── data/                      # Runtime data
├── tests/                     # Unit tests
├── requirements.txt
└── README.md
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_config.py
```

## Security

- No arbitrary shell execution by default
- Dangerous tools require explicit confirmation
- File operations restricted to allowed paths
- No automatic system modifications
- Structured logging without sensitive data

## License

MIT License
