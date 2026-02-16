from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass(slots=True)
class UITargets:
    build_spots: list[tuple[int, int]]
    start_wave: tuple[int, int] | None
    continue_button: tuple[int, int] | None


class KRUIAnalyzer:
    """Heuristic UI analyzer to quickly identify actionable points on screen."""

    def detect(self, frame_bgr: np.ndarray) -> UITargets:
        build_spots = self._find_build_spots(frame_bgr)
        start_wave = self._find_start_like_button(frame_bgr)
        continue_button = self._find_continue_like_button(frame_bgr)
        return UITargets(build_spots=build_spots, start_wave=start_wave, continue_button=continue_button)

    def _find_build_spots(self, frame_bgr: np.ndarray) -> list[tuple[int, int]]:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 1.3)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=40,
            param1=90,
            param2=26,
            minRadius=12,
            maxRadius=42,
        )

        h, w = gray.shape
        spots: list[tuple[int, int]] = []
        if circles is not None:
            for c in circles[0]:
                x, y, r = int(c[0]), int(c[1]), int(c[2])
                # Avoid HUD (top/bottom bars) where false positives are common.
                if y < int(0.12 * h) or y > int(0.88 * h):
                    continue
                if x < int(0.05 * w) or x > int(0.95 * w):
                    continue
                if self._is_far(spots, (x, y), min_dist=32):
                    spots.append((x, y))

        # Order from left->right then top->bottom for deterministic opening strategy.
        spots.sort(key=lambda p: (p[0], p[1]))
        return spots[:18]

    def _find_start_like_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.72 * h) : h, int(0.68 * w) : w]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower = np.array([8, 110, 110], dtype=np.uint8)
        upper = np.array([32, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        return self._largest_blob_center(mask, x_offset=int(0.68 * w), y_offset=int(0.72 * h), min_area=250)

    def _find_continue_like_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.58 * h) : int(0.92 * h), int(0.25 * w) : int(0.75 * w)]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower = np.array([12, 90, 90], dtype=np.uint8)
        upper = np.array([38, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        return self._largest_blob_center(mask, x_offset=int(0.25 * w), y_offset=int(0.58 * h), min_area=500)

    @staticmethod
    def _largest_blob_center(
        mask: np.ndarray, x_offset: int, y_offset: int, min_area: int
    ) -> tuple[int, int] | None:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < min_area:
            return None
        m = cv2.moments(largest)
        if m["m00"] <= 0:
            return None
        cx = int(m["m10"] / m["m00"]) + x_offset
        cy = int(m["m01"] / m["m00"]) + y_offset
        return cx, cy

    @staticmethod
    def _is_far(points: list[tuple[int, int]], candidate: tuple[int, int], min_dist: int) -> bool:
        if not points:
            return True
        cx, cy = candidate
        for px, py in points:
            if (px - cx) ** 2 + (py - cy) ** 2 < min_dist**2:
                return False
        return True
