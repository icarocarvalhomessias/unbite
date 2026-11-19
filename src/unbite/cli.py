"""Command line entry point: `unbite`."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from unbite import __version__, i18n
from unbite.tracker import Settings


def build_parser() -> argparse.ArgumentParser:
    defaults = Settings()
    parser = argparse.ArgumentParser(
        prog="unbite",
        description="Watches your webcam and warns you when your hand goes to your mouth. "
        "Everything runs locally; no image is ever saved or sent anywhere.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    cam = parser.add_argument_group("camera")
    cam.add_argument(
        "--camera",
        type=int,
        metavar="N",
        help="camera index (default: the last one found, usually the external one)",
    )
    cam.add_argument("--list-cameras", action="store_true", help="list cameras and exit")
    cam.add_argument(
        "--preview",
        action="store_true",
        help="show the camera with the measured distance, to tune the settings",
    )

    det = parser.add_argument_group("detection")
    det.add_argument(
        "--threshold",
        type=float,
        default=defaults.threshold,
        metavar="X",
        help="fingertip-to-mouth distance, in mouth widths, that counts as touching "
        f"(default {defaults.threshold}; lower = stricter)",
    )
    det.add_argument(
        "--hold",
        type=float,
        default=defaults.hold,
        metavar="SEC",
        help=f"seconds at the mouth before alerting (default {defaults.hold})",
    )
    det.add_argument(
        "--cooldown",
        type=float,
        default=defaults.cooldown,
        metavar="SEC",
        help=f"minimum seconds between alerts (default {defaults.cooldown})",
    )
    det.add_argument(
        "--no-objects",
        action="store_true",
        help="alert even with a phone, cup or food in your hand",
    )

    out = parser.add_argument_group("alert")
    out.add_argument(
        "--lang",
        metavar="CODE",
        help="alert language, e.g. en, pt, es, zh-TW (default: the system's)",
    )
    out.add_argument("--list-languages", action="store_true", help="list languages and exit")
    out.add_argument(
        "--voice",
        action="store_true",
        help="also speak the alert aloud with the system's voice (off by default)",
    )
    out.add_argument("--no-sound", action="store_true", help="do not beep")
    out.add_argument("--no-banner", action="store_true", help="do not show the red banner")
    out.add_argument(
        "--log",
        type=Path,
        metavar="FILE",
        help="append the time of each alert to a CSV file (no images)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    os.environ.setdefault("GLOG_minloglevel", "2")  # quiet MediaPipe's C++ logs
    os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")  # quiet probing of missing cameras

    if args.list_languages:
        for code in i18n.available():
            print(f"{code:6} {i18n.load(code).name}")
        return 0

    # Heavy imports (OpenCV, MediaPipe) only after the quick commands above.
    from unbite import camera

    cameras = camera.list_cameras()
    if args.list_cameras:
        for info in cameras:
            print(f"camera {info.index}: {info.width}x{info.height}")
        return 0
    if not cameras:
        print("No camera found.", file=sys.stderr)
        return 1

    from unbite import speech
    from unbite.app import Monitor
    from unbite.detection import HandMouthDetector, ObjectInHandDetector
    from unbite.tracker import HabitTracker

    language = i18n.resolve(args.lang or i18n.system_language())
    messages = i18n.load(language)
    index = args.camera if args.camera is not None else cameras[-1].index

    monitor = Monitor(
        capture=camera.open_camera(index),
        detector=HandMouthDetector(),
        objects=None if args.no_objects else ObjectInHandDetector(),
        tracker=HabitTracker(Settings(args.threshold, args.hold, args.cooldown)),
        messages=messages,
        speaker=speech.create(language) if args.voice else speech.Silent(),
        sound=not args.no_sound,
        show_banner=not args.no_banner,
        preview=args.preview,
        log_path=args.log,
    )
    print(
        f"unbite is watching camera {index} (language: {messages.name}). Press Ctrl+C to stop.",
        file=sys.stderr,
    )
    monitor.run()
    return 0
