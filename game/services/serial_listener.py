import logging
import threading
from collections.abc import Callable

from django.conf import settings

try:
    import serial
    from serial import SerialException
except ImportError:  # pragma: no cover - fallback for env without pyserial
    serial = None

    class SerialException(Exception):
        pass


LOGGER = logging.getLogger(__name__)


class ArduinoSerialListener:
    """Listens to Arduino serial and forwards button events."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self, on_button: Callable[[str], None]) -> None:
        if serial is None:
            LOGGER.warning("pyserial not installed; serial listener disabled.")
            return

        with self._lock:
            if self._running:
                return

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                args=(on_button,),
                daemon=True,
                name="arduino-serial-listener",
            )
            self._thread.start()
            self._running = True

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            self._running = False

    def _parse_line(self, line: str) -> str | None:
        clean = line.strip().lower()
        if not clean:
            return None

        # Accepted protocols:
        # BTN:azul
        # azul
        if clean.startswith("btn:"):
            return clean.split(":", maxsplit=1)[1].strip()
        return clean

    def _run(self, on_button: Callable[[str], None]) -> None:
        port = settings.ARDUINO_SERIAL_PORT
        baud_rate = settings.ARDUINO_BAUD_RATE

        while not self._stop_event.is_set():
            try:
                with serial.Serial(port=port, baudrate=baud_rate, timeout=1) as ser:
                    LOGGER.info("Serial connected at %s @ %s", port, baud_rate)
                    while not self._stop_event.is_set():
                        raw = ser.readline().decode("utf-8", errors="ignore")
                        button = self._parse_line(raw)
                        if button:
                            on_button(button)
            except SerialException as exc:
                LOGGER.warning("Serial failure (%s). Retrying...", exc)
                self._stop_event.wait(2)
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Unexpected serial listener error: %s", exc)
                self._stop_event.wait(2)

        self._running = False


arduino_listener = ArduinoSerialListener()
