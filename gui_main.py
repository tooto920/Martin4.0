"""
Martin GUI - Main entry point for the desktop application.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.computer.monitor import get_resource_monitor
from app.core.logger import setup_logger
from app.gui.main_window import MainWindow


def main() -> int:
    """Main entry point for GUI application."""
    logger = setup_logger()
    logger.info("Starting Martin GUI...")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Martin")
    app.setApplicationVersion("3.0.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start resource monitor in background
    resource_monitor = get_resource_monitor()

    # Use a timer to periodically run async tasks
    async def start_monitor():
        await resource_monitor.start()

    # Run initial async setup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_monitor())

    # Timer to keep asyncio loop alive for background tasks
    def process_async():
        try:
            loop.call_soon_threadsafe(lambda: None)
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Async processing error: {e}")

    timer = QTimer()
    timer.timeout.connect(process_async)
    timer.start(100)

    # Run Qt event loop
    result = app.exec()

    # Cleanup
    loop.run_until_complete(resource_monitor.stop())
    loop.close()
    logger.info("Martin GUI stopped")

    return result


if __name__ == "__main__":
    sys.exit(main())