"""When to alert: a small state machine over time, independent of the camera."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Settings:
    threshold: float = 0.9
    """Fingertip-to-mouth distance, in mouth widths, that counts as touching."""
    hold: float = 0.6
    """Seconds the hand must stay at the mouth before alerting."""
    cooldown: float = 4.0
    """Minimum seconds between two alerts."""
    object_grace: float = 1.5
    """Seconds an object seen in the hand keeps suppressing alerts (detectors flicker)."""


class HabitTracker:
    """Feed it one observation per frame; it says when to alert."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._touch_started: float | None = None
        self._last_alert = float("-inf")
        self._object_seen = float("-inf")

    def near_mouth(self, distance: float | None) -> bool:
        return distance is not None and distance < self.settings.threshold

    def holding_object(self, now: float) -> bool:
        return now - self._object_seen < self.settings.object_grace

    def update(self, now: float, distance: float | None, object_in_hand: bool = False) -> bool:
        """Return True when an alert should fire at time `now` (seconds, monotonic)."""
        if object_in_hand:
            self._object_seen = now

        if not self.near_mouth(distance) or self.holding_object(now):
            self._touch_started = None
            return False

        if self._touch_started is None:
            self._touch_started = now
        held = now - self._touch_started >= self.settings.hold
        rested = now - self._last_alert >= self.settings.cooldown
        if held and rested:
            self._last_alert = now
            return True
        return False
