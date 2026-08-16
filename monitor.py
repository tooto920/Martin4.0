"""
System resource monitor for Martin.
Monitors CPU, RAM, GPU, and VRAM usage.
"""
import asyncio
from dataclasses import dataclass

import psutil

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

from app.core.events import get_event_bus
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SystemResources:
    """System resource usage snapshot."""
    cpu_percent: float
    ram_used_gb: float
    ram_total_gb: float
    ram_percent: float
    gpu_percent: float | None = None
    gpu_used_mb: float | None = None
    gpu_total_mb: float | None = None
    gpu_name: str | None = None
    gpu_available: bool = False


class ResourceMonitor:
    """Monitors system resources in background."""

    def __init__(self, update_interval: float = 1.0) -> None:
        self._update_interval = update_interval
        self._running = False
        self._task: asyncio.Task | None = None
        self._latest: SystemResources | None = None
        self._event_bus = get_event_bus()

    @property
    def latest(self) -> SystemResources | None:
        """Get latest resource snapshot."""
        return self._latest

    async def start(self) -> None:
        """Start monitoring."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitor started")

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitor stopped")

    async def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                resources = await self._collect_resources()
                self._latest = resources
                self._event_bus.publish("resources_updated", resources=resources)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Resource collection failed: {e}")

            await asyncio.sleep(self._update_interval)

    async def _collect_resources(self) -> SystemResources:
        """Collect current resource usage."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # RAM
        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)
        ram_percent = ram.percent

        # GPU
        gpu_percent = None
        gpu_used_mb = None
        gpu_total_mb = None
        gpu_name = None
        gpu_available = False

        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    gpu_available = True
                    gpu_name = gpu.name
                    gpu_percent = gpu.load * 100
                    gpu_used_mb = gpu.memoryUsed
                    gpu_total_mb = gpu.memoryTotal
            except Exception as e:  # noqa: BLE001
                logger.debug(f"GPU info unavailable: {e}")

        return SystemResources(
            cpu_percent=cpu_percent,
            ram_used_gb=ram_used_gb,
            ram_total_gb=ram_total_gb,
            ram_percent=ram_percent,
            gpu_percent=gpu_percent,
            gpu_used_mb=gpu_used_mb,
            gpu_total_mb=gpu_total_mb,
            gpu_name=gpu_name,
            gpu_available=gpu_available,
        )


_resource_monitor: ResourceMonitor | None = None


def get_resource_monitor() -> ResourceMonitor:
    """Get global resource monitor instance."""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor