from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time

import cv2
from mss import mss
import numpy as np

from .config import VisionConfig


@dataclass(slots=True)
class ScreenRegion:
    left: int
    top: int
    width: int
    height: int


class VisionEncoder:
    """Captures game screen and converts to compact neural net input."""

    def __init__(self, region: ScreenRegion, config: VisionConfig) -> None:
        self.region = region
        self.config = config
        self._sct = mss()
        self._frames: deque[np.ndarray] = deque(maxlen=config.frame_stack)

    def capture_raw_bgr(self) -> np.ndarray:
        frame = np.array(
            self._sct.grab(
                {
                    "left": self.region.left,
                    "top": self.region.top,
                    "width": self.region.width,
                    "height": self.region.height,
                }
            )
        )
        return frame[:, :, :3]

    def _single_frame(self) -> np.ndarray:
        bgr = self.capture_raw_bgr()
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (self.config.width, self.config.height), interpolation=cv2.INTER_AREA)
        return resized.astype(np.float32) / 255.0

    def reset_stack(self) -> np.ndarray:
        frame = self._single_frame()
        self._frames.clear()
        for _ in range(self.config.frame_stack):
            self._frames.append(frame.copy())
        return self.encode_state()

    def capture(self) -> np.ndarray:
        self._frames.append(self._single_frame())
        while len(self._frames) < self.config.frame_stack:
            self._frames.append(self._frames[-1])
        return self.encode_state()

    def encode_state(self) -> np.ndarray:
        stacked = np.stack(list(self._frames), axis=0)
        return stacked.ravel()

    def wait_for_boot_screen(self, timeout_seconds: int | None = None) -> bool:
        timeout = timeout_seconds if timeout_seconds is not None else self.config.boot_timeout_s
        end = time.time() + timeout
        while time.time() < end:
            if self.detect_boot_screen(self.capture_raw_bgr()):
                return True
            time.sleep(0.2)
        return False

    @staticmethod
    def detect_boot_screen(frame: np.ndarray) -> bool:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1].mean()
        val = hsv[:, :, 2].mean()
        return sat > 65 and 40 < val < 220

    @staticmethod
    def frame_entropy(flat_state: np.ndarray) -> float:
        bins = np.histogram(flat_state, bins=16, range=(0.0, 1.0))[0].astype(np.float32)
        p = bins / (bins.sum() + 1e-8)
        return float(-(p * np.log(p + 1e-8)).sum())
