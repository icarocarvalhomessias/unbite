"""Opening webcams with OpenCV."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import cv2

# DirectShow opens quickly and reliably on Windows; elsewhere let OpenCV pick.
_BACKEND = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY


@dataclass(frozen=True)
class CameraInfo:
    index: int
    width: int
    height: int


def list_cameras(max_index: int = 5) -> list[CameraInfo]:
    """Probe the first indices and return the cameras that deliver a frame."""
    found = []
    for index in range(max_index):
        capture = cv2.VideoCapture(index, _BACKEND)
        try:
            if capture.isOpened():
                ok, frame = capture.read()
                if ok:
                    found.append(CameraInfo(index, frame.shape[1], frame.shape[0]))
        finally:
            capture.release()
    return found


def open_camera(index: int, width: int = 640, height: int = 480) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(index, _BACKEND)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open camera {index}.")
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return capture
