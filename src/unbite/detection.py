"""MediaPipe wrappers: find the face, the hands and objects held in a hand."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from unbite import models
from unbite.geometry import Box, Point, Reach, nearest_reach

# COCO labels of things people often bring to their mouth for a good reason:
# talking on the phone, drinking, eating, brushing teeth.
DEFAULT_OBJECTS = (
    "cell phone",
    "cup",
    "bottle",
    "wine glass",
    "fork",
    "spoon",
    "knife",
    "banana",
    "apple",
    "orange",
    "sandwich",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "toothbrush",
)


@dataclass(frozen=True)
class HeldObject:
    label: str
    score: float
    box: Box


class HandMouthDetector:
    """Measures how close a fingertip is to the mouth in each video frame."""

    def __init__(self) -> None:
        self._hands = vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(models.ensure(models.HAND))),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        )
        self._face = vision.FaceLandmarker.create_from_options(
            vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(models.ensure(models.FACE))),
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
            )
        )

    def measure(self, image: mp.Image, timestamp_ms: int) -> Reach | None:
        """Nearest fingertip-to-mouth reach, or None if no face or no hand is visible."""
        hands = self._hands.detect_for_video(image, timestamp_ms)
        face = self._face.detect_for_video(image, timestamp_ms)
        if not face.face_landmarks or not hands.hand_landmarks:
            return None
        size = (image.width, image.height)
        return nearest_reach(
            _to_pixels(face.face_landmarks[0], size),
            (_to_pixels(hand, size) for hand in hands.hand_landmarks),
        )

    def close(self) -> None:
        self._hands.close()
        self._face.close()


class ObjectInHandDetector:
    """Finds allowed objects (phone, cup, food...) touching a given hand."""

    def __init__(self, labels: Sequence[str] = DEFAULT_OBJECTS, min_score: float = 0.3) -> None:
        self._detector = vision.ObjectDetector.create_from_options(
            vision.ObjectDetectorOptions(
                base_options=BaseOptions(model_asset_path=str(models.ensure(models.OBJECTS))),
                running_mode=vision.RunningMode.IMAGE,
                category_allowlist=list(labels),
                score_threshold=min_score,
                max_results=5,
            )
        )

    def find(self, image: mp.Image, hand: Box, margin: float = 0.2) -> list[HeldObject]:
        found = []
        for detection in self._detector.detect(image).detections:
            b = detection.bounding_box
            box = Box(b.origin_x, b.origin_y, b.origin_x + b.width, b.origin_y + b.height)
            if box.expanded(margin).overlaps(hand):
                category = detection.categories[0]
                found.append(HeldObject(category.category_name, category.score, box))
        return found

    def close(self) -> None:
        self._detector.close()


def to_mp_image(rgb: np.ndarray) -> mp.Image:
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))


def _to_pixels(landmarks, size: tuple[int, int]) -> list[Point]:
    width, height = size
    return [(p.x * width, p.y * height) for p in landmarks]
