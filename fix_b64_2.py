with open('atp/gui/pages/chat.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('self._worker = ChatWorker(self._agent, text)', 'self._worker = ChatWorker(text)')
start = c.find('class ChatWorker(QObject)')
end = c.find('class ChatPage(QWidget)')
new_class = 'class ChatWorker(QObject):\n    \"\"\"Worker for async chat processing.\"\"\"\n    finished = Signal(str)\n    error = Signal(str)\n    thinking = Signal(bool)\n\n    def __init__(self, message: str) -> None:\n        super.__init__()\n        self._message = message\n\n    def run(self) -> None:\n        \"\"\"Qºr chat in thread with fresh provider/agent.\"\\"\"\n        loop = None\n        try:\n            self.thinking.emit(True)\n            loop = asyncio.new_event_loop()\n            asyncio.set_event_loop(loop)\n            from app.ai.ollama import OllamaProvider\n            from app.ai.agent import MartinAgent\n            provider = OllamaProvider()\n            agent = MartinAgent(provider)\n            response = loop.run_until_complete(agent.chat(self._message))\n            self.finished.emit(response)\n        except Exception as e:\n            logger.error(f"Chat error: {e}")\n            self.error.emit(str(e))\n        finally:\n            self.thinking.emit(False)\n            if loop:\n                try:\n                    loop.close()
                except Exception:
                    pass'
c = c[:start] + new_class + c[end]
c = c.replace('self._worker = ChatWorker(self._agent, text)', 'self._worker = ChatWorker(text)')
open('atp/gui/pages/chat.py', 'w', encoding='utf-8').write(c)
print('Done')