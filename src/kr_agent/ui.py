from __future__ import annotations

from dataclasses import dataclass, field
import cv2
import numpy as np


@dataclass(slots=True)
class UITargets:
    build_spots: list[tuple[int, int]]
    start_wave: tuple[int, int] | None
    continue_button: tuple[int, int] | None
    kr_confidence: float
    menu_buttons: dict[str, tuple[int, int]] = field(default_factory=dict)


class KRUIAnalyzer:
    """Resolution-robust UI analyzer tuned for Steam PC fullscreen gameplay."""

    def detect(self, frame_bgr: np.ndarray) -> UITargets:
        build_spots = self._find_build_spots(frame_bgr)
        start_wave = self._find_start_like_button(frame_bgr)
        continue_button = self._find_continue_like_button(frame_bgr)
        menu_buttons = self._find_menu_buttons(frame_bgr)
        kr_confidence = self._kr_scene_confidence(frame_bgr, build_spots, start_wave, continue_button, menu_buttons)
        return UITargets(
            build_spots=build_spots,
            start_wave=start_wave,
            continue_button=continue_button,
            kr_confidence=kr_confidence,
            menu_buttons=menu_buttons,
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
                if self._is_valid_playfield_point(x, y, w, h) and self._is_far(
                    spots, (x, y), min_dist=max(18, int(0.02 * min_side))
                ):
                    spots.append((x, y))

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
                if self._is_valid_playfield_point(cx, cy, w, h) and self._is_far(
                    spots, (cx, cy), min_dist=max(18, int(0.02 * min_side))
                ):
                    spots.append((cx, cy))

        spots.sort(key=lambda p: (p[0], p[1]))
        return spots[:20]

    def _find_start_like_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.70 * h) : h, int(0.64 * w) : w]
        return self._find_orange_button(roi, int(0.64 * w), int(0.70 * h), min_area=max(220, int(0.00023 * h * w)))

    def _find_continue_like_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.50 * h) : int(0.95 * h), int(0.15 * w) : int(0.85 * w)]
        return self._find_orange_button(roi, int(0.15 * w), int(0.50 * h), min_area=max(400, int(0.00040 * h * w)))

    def _find_menu_buttons(self, frame_bgr: np.ndarray) -> dict[str, tuple[int, int]]:
        h, w, _ = frame_bgr.shape
        menu: dict[str, tuple[int, int]] = {}

        # Steam menu profile for 1920x1080, scaled by ratios.
        regions = {
            "start_game": (0.58, 0.63, 0.93, 0.96),
            "enemy_encyclopedia": (0.66, 0.18, 0.96, 0.36),
            "upgrades": (0.66, 0.36, 0.96, 0.56),
            "close_panel": (0.80, 0.03, 0.98, 0.18),
        }

        for name, (x1, y1, x2, y2) in regions.items():
            roi = frame_bgr[int(y1 * h) : int(y2 * h), int(x1 * w) : int(x2 * w)]
            button = self._find_orange_button(
                roi,
                x_offset=int(x1 * w),
                y_offset=int(y1 * h),
                min_area=max(120, int(0.00012 * h * w)),
            )
            if button is not None:
                menu[name] = button

        return menu

    def _kr_scene_confidence(
        self,
        frame_bgr: np.ndarray,
        build_spots: list[tuple[int, int]],
        start_wave: tuple[int, int] | None,
        continue_button: tuple[int, int] | None,
        menu_buttons: dict[str, tuple[int, int]],
    ) -> float:
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        sat = float(np.mean(hsv[:, :, 1]) / 255.0)
        val = float(np.mean(hsv[:, :, 2]) / 255.0)
        spot_score = min(1.0, len(build_spots) / 8.0)
        ui_score = 0.20 if (start_wave is not None or continue_button is not None) else 0.0
        menu_score = min(0.25, 0.08 * len(menu_buttons))
        conf = 0.40 * sat + 0.20 * (1.0 - abs(val - 0.55)) + 0.15 * spot_score + ui_score + menu_score
        return float(np.clip(conf, 0.0, 1.0))

    @staticmethod
    def _find_orange_button(
        roi_bgr: np.ndarray,
        x_offset: int,
        y_offset: int,
        min_area: int,
    ) -> tuple[int, int] | None:
        if roi_bgr.size == 0:
            return None
        hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([8, 85, 80], dtype=np.uint8)
        upper = np.array([40, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < min_area:
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
