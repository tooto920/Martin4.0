"""
Event system for Martin.
Simple pub/sub pattern for decoupled communication.
"""
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


class EventBus:
    """Simple event bus for publish/subscribe pattern."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._async_subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type (sync callback)."""
        self._subscribers[event_type].append(callback)

    def subscribe_async(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type (async callback)."""
        self._async_subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event type."""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
        if callback in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(callback)

    def _safe_call(self, callback: Callable, event_type: str, **kwargs: Any) -> None:
        """Call callback safely, logging errors but not propagating them."""
        try:
            callback(**kwargs)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:  # noqa: BLE001
            logger.warning(f"Event callback failed for {event_type}: {e}")

    async def _safe_call_async(self, callback: Callable, event_type: str, **kwargs: Any) -> None:
        """Call async callback safely, logging errors but not propagating them."""
        try:
            await callback(**kwargs)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:  # noqa: BLE001
            logger.warning(f"Async event callback failed for {event_type}: {e}")

    def publish(self, event_type: str, **kwargs: Any) -> None:
        """Publish event to all sync subscribers."""
        for callback in self._subscribers[event_type]:
            self._safe_call(callback, event_type, **kwargs)

    async def publish_async(self, event_type: str, **kwargs: Any) -> None:
        """Publish event to all subscribers (sync and async)."""
        for callback in self._subscribers[event_type]:
            self._safe_call(callback, event_type, **kwargs)

        for callback in self._async_subscribers[event_type]:
            await self._safe_call_async(callback, event_type, **kwargs)


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus