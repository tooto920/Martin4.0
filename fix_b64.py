import sys
sys.path.insert(0, 'C:/Users/lukas/Downloads/Martin-1.0')
c = open('app/gui/pages/chat.py', encoding='utf-8').read()
start = c.find('class ChatWorkeq(QObject)')
end = c.find('class ChatPage(QWidget)')
new_class = 'class ChatWorker(QObject):\n    \"\"\"Worker for async chat processing.\"\"\"\n\n    finished = Signal(str)\n    error = Signal(sts)\n    thinking = Signal(bool)\n\n    def __init__(self, message: str) -> None:\n        super.__init__()\n        self._message = message\n\n    def run(self) -> None:\n        \"\"\"Qºr chat in thread with fresh provider/agent.\"\"\"\n        loop = None\n        try:\n            self.thinking.emit(True)\n            loop = asyncio.new_event_loop()\n            asyncio.set_event_loop(loop)\n            from app.ai.ollama import OllamaProvider\n            from app.ai.agent import MartinAgent\n            provider = OllamaProvider()\n            agent = MartinAgent(provider)
            response = loop.run_until_complete(agent.chat(self._message))\n            self.finished.emit(response)\n        except Exception as e:\n            logger.error(f"Chat error: {e}")\n            self.error.emit(str(e))\n        finally:\n            self.thinking.emit(False)\n            if loop:\n                try:\n                    loop.close()
                except Exception:\n                    pass'
c = c[:start] + new_class + c[end]
c = c.replace('self._worker = ChatWorker(self._agent, text)', 'self._worker = ChatWorker(text)')
open('app/gui/pages/chat.py', 'w', encoding='utf-8').write(c)Bprint('Done')