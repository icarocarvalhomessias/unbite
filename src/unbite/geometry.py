"""Pure geometry helpers. No camera, no models: easy to test."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

Point = tuple[float, float]

# MediaPipe hand landmark indices of the five fingertips.
FINGERTIPS = (4, 8, 12, 16, 20)
# MediaPipe face mesh indices: mouth corners and inner lips.
MOUTH_CORNERS = (61, 291)
MOUTH_LIPS = (13, 14)


@dataclass(frozen=True)
class Box:
    """Axis-aligned box in pixels."""

    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def around(cls, points: Iterable[Point]) -> Box:
        xs, ys = zip(*points, strict=True)
        return cls(min(xs), min(ys), max(xs), max(ys))

    def expanded(self, ratio: float) -> Box:
        dx = (self.x1 - self.x0) * ratio
        dy = (self.y1 - self.y0) * ratio
        return Box(self.x0 - dx, self.y0 - dy, self.x1 + dx, self.y1 + dy)

    def overlaps(self, other: Box) -> bool:
        return (
            self.x0 < other.x1 and other.x0 < self.x1 and self.y0 < other.y1 and other.y0 < self.y1
        )


@dataclass(frozen=True)
class Reach:
    """How close the nearest fingertip is to the mouth."""

    distance: float
    """Distance in mouth widths, so it does not depend on how far you sit."""
    mouth: Point
    fingertip: Point
    hand: Box


def mouth_center_and_width(face: Sequence[Point]) -> tuple[Point, float]:
    """Center of the mouth and its width, from face mesh points in pixels."""
    corner_a, corner_b = face[MOUTH_CORNERS[0]], face[MOUTH_CORNERS[1]]
    lip_top, lip_bottom = face[MOUTH_LIPS[0]], face[MOUTH_LIPS[1]]
    points = (corner_a, corner_b, lip_top, lip_bottom)
    center = (sum(p[0] for p in points) / 4, sum(p[1] for p in points) / 4)
    width = max(math.dist(corner_a, corner_b), 1.0)
    return center, width


def nearest_reach(face: Sequence[Point], hands: Iterable[Sequence[Point]]) -> Reach | None:
    """The fingertip closest to the mouth across all hands, or None without hands."""
    mouth, width = mouth_center_and_width(face)
    best: Reach | None = None
    for hand in hands:
        for index in FINGERTIPS:
            tip = hand[index]
            distance = math.dist(tip, mouth) / width
            if best is None or distance < best.distance:
                best = Reach(distance, mouth, tip, Box.around(hand))
    return best
