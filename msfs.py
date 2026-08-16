"""
MSFS 2024 integration for Martin.
Provides aircraft and flight data via SimConnect polling.
"""
import asyncio
from dataclasses import dataclass

from app.core.config import get_config
from app.core.events import get_event_bus
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AircraftInfo:
    """Aircraft information."""
    name: str
    image_path: str = ""
    category: str = ""
    manufacturer: str = ""


@dataclass
class FlightData:
    """Flight data snapshot."""
    altitude_ft: float = 0.0
    speed_kts: float = 0.0
    heading_deg: float = 0.0
    vertical_speed_fpm: float = 0.0
    fuel_lbs: float = 0.0
    autopilot_on: bool = False
    gear_down: bool = True
    flaps_position: str = "UP"
    latitude: float = 0.0
    longitude: float = 0.0
    position: str = ""
    destination: str = ""
    flight_status: str = ""


class MSFSIntegration:
    """MSFS 2024 integration via SimConnect."""

    def __init__(self, update_interval: float = 2.0) -> None:
        self._config = get_config()
        self._update_interval = update_interval
        self._running = False
        self._task: asyncio.Task | None = None
        self._event_bus = get_event_bus()
        self._connected = False
        self._aircraft = AircraftInfo(name="Not connected")
        self._flight = FlightData()
        self._simconnect = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def aircraft(self) -> AircraftInfo:
        return self._aircraft

    @property
    def flight_data(self) -> FlightData:
        return self._flight

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("MSFS integration started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MSFS integration stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._update_state()
            except Exception as e:  # noqa: BLE001
                logger.debug(f"MSFS poll error: {e}")
            await asyncio.sleep(self._update_interval)

    async def _update_state(self) -> None:
        try:
            import psutil
            msfs_running = any(
                p.info["name"].lower() in ("flight simulator.exe", "fs2024.exe")
                for p in psutil.process_iter(["name"])
            )
        except Exception:  # noqa: BLE001
            msfs_running = False

        if msfs_running and not self._connected:
            self._connected = True
            self._aircraft = AircraftInfo(
                name="Default Aircraft",
                category="Placeholder",
                manufacturer="Unknown",
                image_path="",
            )
            self._event_bus.publish("msfs_connected")
            logger.info("MSFS connected (process detected)")
        elif not msfs_running and self._connected:
            self._connected = False
            self._aircraft = AircraftInfo(name="Not connected")
            self._flight = FlightData()
            self._event_bus.publish("msfs_disconnected")
            logger.info("MSFS disconnected")

        if self._connected:
            self._event_bus.publish("msfs_data_updated", aircraft=self._aircraft, flight=self._flight)

    def update_aircraft_data(self, data: dict) -> None:
        self._aircraft = AircraftInfo(
            name=data.get("name", self._aircraft.name),
            image_path=data.get("image_path", self._aircraft.image_path),
            category=data.get("category", self._aircraft.category),
            manufacturer=data.get("manufacturer", self._aircraft.manufacturer),
        )

    def update_flight_data(self, data: dict) -> None:
        self._flight = FlightData(
            altitude_ft=data.get("altitude", self._flight.altitude_ft),
            speed_kts=data.get("speed", self._flight.speed_kts),
            heading_deg=data.get("heading", self._flight.heading_deg),
            vertical_speed_fpm=data.get("vertical_speed", self._flight.vertical_speed_fpm),
            fuel_lbs=data.get("fuel", self._flight.fuel_lbs),
            autopilot_on=data.get("autopilot", self._flight.autopilot_on),
            gear_down=data.get("gear", self._flight.gear_down),
            flaps_position=data.get("flaps", self._flight.flaps_position),
            position=data.get("position", self._flight.position),
            destination=data.get("destination", self._flight.destination),
            flight_status=data.get("flight_status", self._flight.flight_status),
        )


_msfs: MSFSIntegration | None = None


def get_msfs_integration() -> MSFSIntegration:
    global _msfs
    if _msfs is None:
        _msfs = MSFSIntegration()
    return _msfs

