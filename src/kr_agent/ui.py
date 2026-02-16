from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass(slots=True)
class UITargets:
    build_spots: list[tuple[int, int]]
    start_wave: tuple[int, int] | None
    continue_button: tuple[int, int] | None
    kr_confidence: float


class KRUIAnalyzer:
    """Resolution-robust UI analyzer for Kingdom Rush."""

    def detect(self, frame_bgr: np.ndarray) -> UITargets:
        build_spots = self._find_build_spots(frame_bgr)
        start_wave = self._find_start_like_button(frame_bgr)
        continue_button = self._find_continue_like_button(frame_bgr)
        kr_confidence = self._kr_scene_confidence(frame_bgr, build_spots, start_wave, continue_button)
        return UITargets(
            build_spots=build_spots,
            start_wave=start_wave,
            continue_button=continue_button,
            kr_confidence=kr_confidence,
        )

    def _find_build_spots(self, frame_bgr: np.ndarray) -> list[tuple[int, int]]:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        min_side = min(h, w)

        blur = cv2.GaussianBlur(gray, (7, 7), 1.2)
        min_radius = max(8, int(0.010 * min_side))
        max_radius = max(min_radius + 5, int(0.040 * min_side))

        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(20, int(0.03 * min_side)),
            param1=95,
            param2=24,
            minRadius=min_radius,
            maxRadius=max_radius,
        )

        spots: list[tuple[int, int]] = []
        if circles is not None:
            for c in circles[0]:
                x, y = int(c[0]), int(c[1])
                if self._is_valid_playfield_point(x, y, w, h) and self._is_far(spots, (x, y), min_dist=max(18, int(0.02 * min_side))):
                    spots.append((x, y))

        # Fallback: contour circularity search if hough misses.
        if len(spots) < 2:
            edges = cv2.Canny(blur, 70, 160)
            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < (min_radius * min_radius * 0.8) or area > (max_radius * max_radius * 4.5):
                    continue
                perimeter = cv2.arcLength(contour, True)
                if perimeter <= 0:
                    continue
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity < 0.55:
                    continue
                x, y, cw, ch = cv2.boundingRect(contour)
                cx, cy = x + cw // 2, y + ch // 2
                if self._is_valid_playfield_point(cx, cy, w, h) and self._is_far(spots, (cx, cy), min_dist=max(18, int(0.02 * min_side))):
                    spots.append((cx, cy))

        spots.sort(key=lambda p: (p[0], p[1]))
        return spots[:20]

    def _find_start_like_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.70 * h) : h, int(0.64 * w) : w]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower = np.array([8, 100, 90], dtype=np.uint8)
        upper = np.array([35, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        return self._largest_blob_center(mask, x_offset=int(0.64 * w), y_offset=int(0.70 * h), min_area=max(200, int(0.00025 * h * w)))

    def _find_continue_like_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.52 * h) : int(0.94 * h), int(0.20 * w) : int(0.80 * w)]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower = np.array([10, 85, 85], dtype=np.uint8)
        upper = np.array([40, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        return self._largest_blob_center(mask, x_offset=int(0.20 * w), y_offset=int(0.52 * h), min_area=max(380, int(0.00045 * h * w)))

    def _kr_scene_confidence(
        self,
        frame_bgr: np.ndarray,
        build_spots: list[tuple[int, int]],
        start_wave: tuple[int, int] | None,
        continue_button: tuple[int, int] | None,
    ) -> float:
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        sat = float(np.mean(hsv[:, :, 1]) / 255.0)
        val = float(np.mean(hsv[:, :, 2]) / 255.0)
        spot_score = min(1.0, len(build_spots) / 8.0)
        ui_score = 0.25 if (start_wave is not None or continue_button is not None) else 0.0

        # Weighted confidence in [0, 1]
        conf = 0.45 * sat + 0.25 * (1.0 - abs(val - 0.55)) + 0.20 * spot_score + ui_score
        return float(np.clip(conf, 0.0, 1.0))

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
    def _is_valid_playfield_point(x: int, y: int, width: int, height: int) -> bool:
        if y < int(0.10 * height) or y > int(0.90 * height):
            return False
        if x < int(0.03 * width) or x > int(0.97 * width):
            return False
        return True

    @staticmethod
    def _is_far(points: list[tuple[int, int]], candidate: tuple[int, int], min_dist: int) -> bool:
        if not points:
            return True
        cx, cy = candidate
        for px, py in points:
            if (px - cx) ** 2 + (py - cy) ** 2 < min_dist**2:
                return False
        return True
