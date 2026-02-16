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
    popup_done: tuple[int, int] | None = None
    popup_close: tuple[int, int] | None = None
    hero_room_open: bool = False
    upgrades_open: bool = False
    upgrades_points_available: bool = False
    heroes_available: bool = False


class KRUIAnalyzer:
    """Resolution-robust UI analyzer tuned for Steam PC fullscreen gameplay."""

    def detect(self, frame_bgr: np.ndarray) -> UITargets:
        build_spots = self._find_build_spots(frame_bgr)
        start_wave = self._find_start_like_button(frame_bgr)
        continue_button = self._find_continue_like_button(frame_bgr)
        menu_buttons = self._find_menu_buttons(frame_bgr)
        popup_done = self._find_popup_done_button(frame_bgr)
        popup_close = self._find_popup_close_button(frame_bgr)
        upgrades_open = self._detect_upgrades_panel(frame_bgr)
        hero_room_open = self._detect_hero_room_panel(frame_bgr)
        upgrades_points_available = self._detect_upgrade_points_available(frame_bgr) if upgrades_open else False
        heroes_available = self._detect_hero_candidates(frame_bgr) if hero_room_open else False

        kr_confidence = self._kr_scene_confidence(
            frame_bgr,
            build_spots,
            start_wave,
            continue_button,
            menu_buttons,
        )
        return UITargets(
            build_spots=build_spots,
            start_wave=start_wave,
            continue_button=continue_button,
            kr_confidence=kr_confidence,
            menu_buttons=menu_buttons,
            popup_done=popup_done,
            popup_close=popup_close,
            hero_room_open=hero_room_open,
            upgrades_open=upgrades_open,
            upgrades_points_available=upgrades_points_available,
            heroes_available=heroes_available,
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

        regions = {
            "start_game": (0.58, 0.63, 0.93, 0.96),
            "enemy_encyclopedia": (0.66, 0.18, 0.96, 0.36),
            "upgrades": (0.66, 0.36, 0.96, 0.56),
            "close_panel": (0.80, 0.03, 0.98, 0.18),
            "hero_room": (0.66, 0.56, 0.96, 0.78),
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

    def _find_popup_done_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.72 * h) : int(0.95 * h), int(0.52 * w) : int(0.76 * w)]
        return self._find_orange_button(roi, int(0.52 * w), int(0.72 * h), min_area=max(260, int(0.0002 * h * w)))

    def _find_popup_close_button(self, frame_bgr: np.ndarray) -> tuple[int, int] | None:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.12 * h) : int(0.30 * h), int(0.62 * w) : int(0.78 * w)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=16, param1=120, param2=18, minRadius=8, maxRadius=24)
        if circles is None:
            return None
        c = circles[0][0]
        return int(c[0] + 0.62 * w), int(c[1] + 0.12 * h)

    def _detect_upgrades_panel(self, frame_bgr: np.ndarray) -> bool:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.20 * h) : int(0.76 * h), int(0.28 * w) : int(0.74 * w)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=18, param1=120, param2=16, minRadius=10, maxRadius=28)
        count = 0 if circles is None else len(circles[0])
        return count >= 10

    def _detect_hero_room_panel(self, frame_bgr: np.ndarray) -> bool:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.26 * h) : int(0.58 * h), int(0.30 * w) : int(0.53 * w)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 160)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        square_like = 0
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            area = cw * ch
            if area < 350 or area > 6000:
                continue
            ratio = cw / max(1, ch)
            if 0.75 <= ratio <= 1.25:
                square_like += 1
        return square_like >= 8

    def _detect_upgrade_points_available(self, frame_bgr: np.ndarray) -> bool:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.78 * h) : int(0.92 * h), int(0.30 * w) : int(0.43 * w)]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # Gold/yellow number pixels near star.
        mask = cv2.inRange(hsv, np.array([18, 80, 110], dtype=np.uint8), np.array([40, 255, 255], dtype=np.uint8))
        yellow_ratio = float(np.mean(mask > 0))
        return yellow_ratio > 0.03

    def _detect_hero_candidates(self, frame_bgr: np.ndarray) -> bool:
        h, w, _ = frame_bgr.shape
        roi = frame_bgr[int(0.26 * h) : int(0.58 * h), int(0.30 * w) : int(0.53 * w)]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1].astype(np.float32) / 255.0
        # Locked slots tend to be gray/low saturation; unlocked portraits are more colorful.
        return float(np.mean(sat > 0.28)) > 0.08

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
