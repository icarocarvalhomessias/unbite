"""Download and cache the MediaPipe models, pinned by version and checksum."""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

_BASE = "https://storage.googleapis.com/mediapipe-models"


@dataclass(frozen=True)
class Model:
    filename: str
    url: str
    sha256: str


HAND = Model(
    "hand_landmarker.task",
    f"{_BASE}/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1",
)
FACE = Model(
    "face_landmarker.task",
    f"{_BASE}/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
    "64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff",
)
OBJECTS = Model(
    "efficientdet_lite0.tflite",
    f"{_BASE}/object_detector/efficientdet_lite0/float16/1/efficientdet_lite0.tflite",
    "4b59100025bea1235a84c1038879a6cccc9f6c49f5e41144e91e74d99e780993",
)


def cache_dir() -> Path:
    """Per-user cache folder, following each OS's convention."""
    if override := os.environ.get("UNBITE_CACHE"):
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "unbite" / "models"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure(model: Model, folder: Path | None = None) -> Path:
    """Return the local path of `model`, downloading and verifying it if needed."""
    folder = folder or cache_dir()
    path = folder / model.filename
    if path.exists() and _sha256(path) == model.sha256:
        return path

    folder.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {model.filename} (first run only)...", file=sys.stderr)
    with tempfile.NamedTemporaryFile(dir=folder, delete=False, suffix=".part") as tmp:
        tmp_path = Path(tmp.name)
        with urllib.request.urlopen(model.url, timeout=60) as response:
            while chunk := response.read(1 << 20):
                tmp.write(chunk)

    actual = _sha256(tmp_path)
    if actual != model.sha256:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Checksum mismatch for {model.filename}: expected {model.sha256}, got {actual}."
        )
    tmp_path.replace(path)
    return path
