"""Speak the alert aloud with the operating system's own voices (offline)."""

from __future__ import annotations

import locale
import re
import shutil
import subprocess
import sys
from typing import Protocol


class Speaker(Protocol):
    def say(self, text: str) -> None: ...

    def close(self) -> None: ...


class Silent:
    def say(self, text: str) -> None:
        pass

    def close(self) -> None:
        pass


class WindowsSpeaker:
    """SAPI voices. Speaks asynchronously and interrupts the previous phrase."""

    _ASYNC_AND_PURGE = 1 | 2  # SVSFlagsAsync | SVSFPurgeBeforeSpeak

    def __init__(self, language: str) -> None:
        import comtypes.client

        self._voice = comtypes.client.CreateObject("SAPI.SpVoice")
        voices = self._voice.GetVoices()
        for i in range(voices.Count):
            token = voices.Item(i)
            if _same_language(_sapi_languages(token), language):
                self._voice.Voice = token
                break

    def say(self, text: str) -> None:
        self._voice.Speak(text, self._ASYNC_AND_PURGE)

    def close(self) -> None:
        self._voice = None


class CommandSpeaker:
    """Runs a speech command (`say`, `spd-say`, `espeak-ng`) without waiting."""

    def __init__(self, command: list[str]) -> None:
        self._command = command
        self._process: subprocess.Popen | None = None

    def say(self, text: str) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()
        self._process = subprocess.Popen(
            [*self._command, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def close(self) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()


def create(language: str) -> Speaker:
    """The best available speaker for `language` (a tag like 'pt' or 'zh-TW')."""
    try:
        if sys.platform == "win32":
            return WindowsSpeaker(language)
        if sys.platform == "darwin" and shutil.which("say"):
            voice = _mac_voice(language)
            return CommandSpeaker(["say", "-v", voice] if voice else ["say"])
        if shutil.which("spd-say"):
            return CommandSpeaker(["spd-say", "-l", language.split("-")[0]])
        for espeak in ("espeak-ng", "espeak"):
            if shutil.which(espeak):
                return CommandSpeaker([espeak, "-v", language.split("-")[0].lower()])
    except Exception as error:  # speech is a nice-to-have; never crash for it
        print(f"Voice disabled: {error}", file=sys.stderr)
    return Silent()


def _same_language(tags: list[str], language: str) -> bool:
    base = language.split("-")[0].lower()
    return any(tag.replace("_", "-").split("-")[0].lower() == base for tag in tags)


def _sapi_languages(token) -> list[str]:
    """SAPI stores languages as hex LCIDs separated by ';', e.g. '416;816'."""
    try:
        raw = token.GetAttribute("Language")
    except Exception:
        return []
    tags = []
    for lcid in filter(None, raw.split(";")):
        name = locale.windows_locale.get(int(lcid, 16))
        if name:
            tags.append(name)
    return tags


def _mac_voice(language: str) -> str | None:
    out = subprocess.run(
        ["say", "-v", "?"], capture_output=True, text=True, timeout=5, check=False
    ).stdout
    # Lines look like: "Luciana             pt_BR    # Olá, meu nome é Luciana."
    for line in out.splitlines():
        match = re.match(r"^(.+?)\s+([a-z]{2,3}[_-][A-Za-z0-9]+)\s+#", line)
        if match and _same_language([match.group(2)], language):
            return match.group(1).strip()
    return None
