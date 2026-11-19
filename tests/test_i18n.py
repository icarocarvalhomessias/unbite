import json
from importlib import resources

import pytest

from unbite import i18n


def test_every_locale_has_the_same_keys_and_no_blanks():
    for code in i18n.available():
        raw = (resources.files("unbite") / "locales" / f"{code}.json").read_text("utf-8")
        data = json.loads(raw)
        assert set(data) == {"name", "banner", "speech"}, code
        assert all(value.strip() for value in data.values()), code


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("pt_BR.UTF-8", "pt"),
        ("pt-PT", "pt"),
        ("es_MX", "es"),
        ("en_US", "en"),
        ("zh_CN", "zh"),
        ("zh_TW", "zh-TW"),
        ("zh-Hant-HK", "zh-TW"),
        ("zh_HK", "zh-TW"),
        ("ja_JP", "ja"),
        ("xx_YY", "en"),
        ("", "en"),
    ],
)
def test_resolve(tag, expected):
    assert i18n.resolve(tag) == expected


def test_normalize():
    assert i18n.normalize("pt_BR.UTF-8") == "pt-BR"
    assert i18n.normalize("zh_hant_tw") == "zh-Hant-TW"
    assert i18n.normalize("de_DE@euro") == "de-DE"


def test_system_language_reads_the_environment(monkeypatch):
    monkeypatch.setattr(i18n, "_from_platform", lambda: None)
    monkeypatch.setenv("LANGUAGE", "fr_FR:en")
    assert i18n.system_language() == "fr-FR"
