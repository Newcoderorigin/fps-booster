"""Optional integrations for hardware telemetry, CV, and audio spotting."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
from dataclasses import dataclass
from typing import Callable, Deque, Iterable, List, Optional, Sequence
from collections import deque

Frame = Sequence[Sequence[Sequence[int]]]


@dataclass(frozen=True)
class HardwareSnapshot:
    """Represents sampled hardware telemetry."""

    cpu_util: Optional[float]
    gpu_util: Optional[float]
    cpu_temp_c: Optional[float]
    gpu_temp_c: Optional[float]


class HardwareTelemetryCollector:
    """Collects metrics using psutil/GPUtil when available."""

    def __init__(self) -> None:
        spec = importlib.util.find_spec("psutil")
        self._psutil = importlib.import_module("psutil") if spec else None
        gspec = importlib.util.find_spec("GPUtil")
        self._gputil = importlib.import_module("GPUtil") if gspec else None

    def snapshot(self) -> HardwareSnapshot:
        cpu_util = None
        cpu_temp = None
        if self._psutil:
            cpu_util = float(self._psutil.cpu_percent(interval=None))
            try:
                temps = self._psutil.sensors_temperatures()
            except AttributeError:  # pragma: no cover - psutil without temps
                temps = {}
            if temps:
                flat = [reading.current for entries in temps.values() for reading in entries if reading.current]
                if flat:
                    cpu_temp = float(sum(flat) / len(flat))
        gpu_util = None
        gpu_temp = None
        if self._gputil:
            gpus = self._gputil.getGPUs()
            if gpus:
                gpu_util = float(sum(gpu.load for gpu in gpus) / len(gpus) * 100)
                temps = [gpu.temperature for gpu in gpus if getattr(gpu, "temperature", None) is not None]
                if temps:
                    gpu_temp = float(sum(temps) / len(temps))
        return HardwareSnapshot(cpu_util=cpu_util, gpu_util=gpu_util, cpu_temp_c=cpu_temp, gpu_temp_c=gpu_temp)


class YOLOAdapter:
    """Wraps an optional YOLO detector or uses heuristics as fallback."""

    def __init__(self, detector: Callable[[Frame], Iterable[str]]) -> None:
        self._detector = detector

    @classmethod
    def auto(cls, model_name: str = "yolov8n.pt") -> Optional["YOLOAdapter"]:
        spec = importlib.util.find_spec("ultralytics")
        if not spec:
            return None
        module = importlib.import_module("ultralytics")
        model = module.YOLO(model_name)

        def _detect(frame: Frame) -> Iterable[str]:
            results = model.predict(frame, verbose=False)
            labels: List[str] = []
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = result.names.get(cls_id, f"class_{cls_id}")
                    confidence = float(box.conf[0])
                    labels.append(f"{label}:{confidence:.2f}")
            return labels

        return cls(_detect)

    @classmethod
    def heuristic(cls, threshold: float = 0.65) -> "YOLOAdapter":
        def _detect(frame: Frame) -> Iterable[str]:
            bright = 0
            total = 0
            for row in frame:
                for pixel in row:
                    total += 1
                    if sum(pixel) / (3 * 255) >= threshold:
                        bright += 1
            coverage = bright / total if total else 0.0
            if coverage > 0.4:
                return ["luminous_region"]
            if coverage > 0.2:
                return ["glow_patch"]
            return []

        return cls(_detect)

    def detect(self, frame: Frame) -> List[str]:
        return list(self._detector(frame))


class KeywordSpotter:
    """Keyword spotting harness with optional external dependency."""

    def __init__(self, predictor: Callable[[Sequence[float]], Iterable[str]]) -> None:
        self._predictor = predictor

    @classmethod
    def auto(cls) -> Optional["KeywordSpotter"]:
        spec = importlib.util.find_spec("onnxruntime")
        if not spec:
            return None
        ort = importlib.import_module("onnxruntime")
        session = ort.InferenceSession("keyword_spotter.onnx")

        def _predict(samples: Sequence[float]) -> Iterable[str]:
            import numpy as np  # type: ignore

            arr = np.array(samples, dtype=np.float32)[None, :]
            logits = session.run(None, {session.get_inputs()[0].name: arr})[0][0]
            keywords = [session.get_outputs()[0].name]
            if logits[0] > 0.5:
                return keywords
            return []

        return cls(_predict)

    @classmethod
    def heuristic(cls, intensity_threshold: float = 0.3) -> "KeywordSpotter":
        def _predict(samples: Sequence[float]) -> Iterable[str]:
            rms = 0.0
            for sample in samples:
                rms += sample * sample
            rms = (rms / len(samples)) ** 0.5 if samples else 0.0
            if rms >= intensity_threshold:
                return ["impact"]
            return []

        return cls(_predict)

    def predict(self, samples: Sequence[float]) -> List[str]:
        return list(self._predictor(samples))


class OverlayEventBroadcaster:
    """Broadcasts overlay payloads through WebSocket when available."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, buffer: int = 128) -> None:
        if port <= 0:
            raise ValueError("port must be positive")
        if buffer <= 0:
            raise ValueError("buffer must be positive")
        self._host = host
        self._port = port
        self._buffer: Deque[str] = deque(maxlen=buffer)
        self._server = None
        spec = importlib.util.find_spec("websockets")
        self._websockets = importlib.import_module("websockets") if spec else None
        self._clients: List[object] = []

    def publish(self, payload: object) -> None:
        """Store the payload locally for clients to consume."""

        serialized = json.dumps(payload, default=self._serialize)
        self._buffer.append(serialized)

    async def async_publish(self, payload: object) -> None:
        """Broadcast to connected clients if WebSockets are available."""

        self.publish(payload)
        if self._server and self._websockets:
            await asyncio.gather(*(client.send(self._buffer[-1]) for client in list(self._clients)))

    async def start(self) -> None:
        """Start the websocket server if the dependency exists."""

        if not self._websockets:
            return
        self._server = await self._websockets.serve(self._handler, self._host, self._port)

    async def stop(self) -> None:
        """Stop the websocket server."""

        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self._clients.clear()

    async def _handler(self, websocket, _path):  # pragma: no cover - requires websockets
        self._clients.append(websocket)
        try:
            for payload in self._buffer:
                await websocket.send(payload)
            async for _ in websocket:
                pass
        finally:
            self._clients.remove(websocket)

    @staticmethod
    def _serialize(value: object) -> object:
        if hasattr(value, "__dict__"):
            return value.__dict__
        if isinstance(value, (list, tuple)):
            return list(value)
        return str(value)

    def buffered_events(self) -> List[str]:
        """Return buffered events for offline clients."""

        return list(self._buffer)
