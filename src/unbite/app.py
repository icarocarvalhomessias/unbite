"""The main loop: camera frame -> detection -> tracker -> alert."""

from __future__ import annotations

import csv
import signal
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from unbite.banner import Banner, beep
from unbite.detection import HandMouthDetector, HeldObject, ObjectInHandDetector, to_mp_image
from unbite.geometry import Reach
from unbite.i18n import Messages
from unbite.speech import Speaker
from unbite.tracker import HabitTracker

PREVIEW_TITLE = "unbite (press q to quit)"
_GREEN, _RED, _ORANGE, _GRAY, _MOUTH = (
    (0, 200, 0),
    (0, 0, 255),
    (0, 160, 255),
    (200, 200, 200),
    (255, 200, 0),
)


@dataclass
class Monitor:
    capture: cv2.VideoCapture
    detector: HandMouthDetector
    objects: ObjectInHandDetector | None
    tracker: HabitTracker
    messages: Messages
    speaker: Speaker
    sound: bool = True
    show_banner: bool = True
    preview: bool = False
    log_path: Path | None = None

    def run(self) -> None:
        self._root = tk.Tk()
        self._root.withdraw()
        self._banner = Banner(self._root, self.messages.banner, sound=self.sound)
        self._start = time.monotonic()
        self._root.after(0, self._step)
        # Tk swallows exceptions raised in callbacks, so turn Ctrl+C into a clean quit.
        previous = signal.signal(signal.SIGINT, lambda *_: self._root.quit())
        try:
            self._root.mainloop()
        finally:
            signal.signal(signal.SIGINT, previous)
            self.capture.release()
            cv2.destroyAllWindows()
            self.detector.close()
            if self.objects:
                self.objects.close()
            self.speaker.close()

    def _step(self) -> None:
        ok, frame = self.capture.read()
        if not ok:
            self._root.after(100, self._step)
            return

        frame = cv2.flip(frame, 1)  # mirror, so the preview feels natural
        image = to_mp_image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        now = time.monotonic()
        reach = self.detector.measure(image, int((now - self._start) * 1000))

        held: list[HeldObject] = []
        # The object detector is the slowest model: run it only when it matters.
        if reach and self.objects and self.tracker.near_mouth(reach.distance):
            held = self.objects.find(image, reach.hand)

        if self.tracker.update(now, reach.distance if reach else None, bool(held)):
            self._alert(reach)

        if self.preview and not self._draw_preview(frame, reach, held, now):
            self._root.quit()
            return
        self._root.after(1, self._step)

    def _alert(self, reach: Reach) -> None:
        if self.show_banner:
            self._banner.show()
        elif self.sound:
            beep(self._root)
        self.speaker.say(self.messages.speech)
        if self.log_path:
            _append_log(self.log_path, reach.distance)

    def _draw_preview(
        self, frame: np.ndarray, reach: Reach | None, held: list[HeldObject], now: float
    ) -> bool:
        """Draw the debug view. Returns False when the user asks to quit."""
        if reach is None:
            _label(frame, "no face or no hand in view", 0, _GRAY)
        else:
            touching = self.tracker.near_mouth(reach.distance)
            color = _RED if touching else _GREEN
            mouth = tuple(int(v) for v in reach.mouth)
            tip = tuple(int(v) for v in reach.fingertip)
            cv2.line(frame, mouth, tip, color, 2)
            cv2.circle(frame, mouth, 6, _MOUTH, -1)
            cv2.circle(frame, tip, 6, color, -1)
            _label(
                frame,
                f"distance {reach.distance:.2f}  (threshold {self.tracker.settings.threshold})",
                0,
                color,
            )
            for obj in held:
                b = obj.box
                cv2.rectangle(frame, (int(b.x0), int(b.y0)), (int(b.x1), int(b.y1)), _ORANGE, 2)
                cv2.putText(
                    frame,
                    f"{obj.label} {obj.score:.2f}",
                    (int(b.x0), int(b.y0) - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    _ORANGE,
                    2,
                )
            if touching and self.tracker.holding_object(now):
                _label(frame, "object in hand: no alert", 1, _ORANGE)

        cv2.imshow(PREVIEW_TITLE, frame)
        key = cv2.waitKey(1) & 0xFF
        closed = cv2.getWindowProperty(PREVIEW_TITLE, cv2.WND_PROP_VISIBLE) < 1
        return key != ord("q") and not closed


def _label(frame: np.ndarray, text: str, line: int, color: tuple[int, int, int]) -> None:
    cv2.putText(frame, text, (10, 30 + 32 * line), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)


def _append_log(path: Path, distance: float) -> None:
    """One row per alert: time and distance. Never images."""
    is_new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_new:
            writer.writerow(["time", "distance"])
        writer.writerow([datetime.now().isoformat(timespec="seconds"), f"{distance:.2f}"])
