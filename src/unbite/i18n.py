"""Alert texts in the computer's language."""

from __future__ import annotations

import ctypes
import json
import locale
import os
import subprocess
import sys
from dataclasses import dataclass
from functools import cache
from importlib import resources

FALLBACK = "en"

# Traditional Chinese regions share one file.
_ALIASES = {"zh-HK": "zh-TW", "zh-MO": "zh-TW", "zh-Hant": "zh-TW", "zh-Hans": "zh"}


@dataclass(frozen=True)
class Messages:
    code: str
    name: str
    banner: str
    speech: str


@cache
def available() -> tuple[str, ...]:
    folder = resources.files("unbite") / "locales"
    return tuple(
        sorted(p.name.removesuffix(".json") for p in folder.iterdir() if p.name.endswith(".json"))
    )


def normalize(tag: str) -> str:
    """'pt_BR.UTF-8' -> 'pt-BR', 'zh_Hant_TW' -> 'zh-Hant-TW'."""
    tag = tag.split(".")[0].split("@")[0].replace("_", "-")
    parts = tag.split("-")
    out = [parts[0].lower()]
    for part in parts[1:]:
        out.append(part.title() if len(part) == 4 else part.upper())
    return "-".join(out)


def resolve(tag: str) -> str:
    """Best available locale for a language tag, falling back to English."""
    tag = normalize(tag)
    parts = tag.split("-")
    candidates = [tag]
    if len(parts) > 2:  # zh-Hant-TW -> zh-Hant, zh-TW
        candidates += ["-".join(parts[:2]), f"{parts[0]}-{parts[-1]}"]
    candidates.append(parts[0])
    for candidate in candidates:
        candidate = _ALIASES.get(candidate, candidate)
        if candidate in available():
            return candidate
    return FALLBACK


def system_language() -> str:
    """The user's interface language as a tag like 'pt-BR', or 'en' if unknown."""
    detectors = [_from_platform, _from_env, _from_locale]
    if sys.platform not in ("win32", "darwin"):
        detectors = [_from_env, _from_locale]
    for detect in detectors:
        try:
            tag = detect()
        except Exception:  # a broken detector should never stop the app
            tag = None
        if tag:
            return normalize(tag)
    return FALLBACK


def load(code: str) -> Messages:
    data = json.loads((resources.files("unbite") / "locales" / f"{code}.json").read_text("utf-8"))
    return Messages(code=code, **data)


def _from_platform() -> str | None:
    if sys.platform == "win32":
        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale.get(lcid)
    if sys.platform == "darwin":
        out = subprocess.run(
            ["defaults", "read", "-g", "AppleLanguages"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        ).stdout
        # Output looks like: (\n    "pt-BR",\n    "en-US"\n)
        for line in out.splitlines():
            line = line.strip().strip(",").strip('"')
            if line and line not in "()":
                return line
    return None


def _from_env() -> str | None:
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "").split(":")[0]
        if value and value not in ("C", "POSIX") and not value.startswith("C."):
            return value
    return None


def _from_locale() -> str | None:
    return locale.getlocale()[0]
