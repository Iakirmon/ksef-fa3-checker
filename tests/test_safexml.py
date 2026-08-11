"""Testy safexml — podstawowe wektory (korpus złośliwy w etapie 5)."""

from __future__ import annotations

import pytest

from fa3check.safexml import LIMIT_BAJTOW, sparsuj
from fa3check.typy import LimitPrzekroczony, XmlNiebezpieczny, XmlNiepoprawny

MINI = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/"/>'
)


def test_poprawny_minimalny() -> None:
    dok = sparsuj(MINI)
    assert dok.korzen is not None
    assert dok.surowe == MINI


def test_rozmiar_przed_parsowaniem() -> None:
    dane = b"x" * (LIMIT_BAJTOW + 1)
    with pytest.raises(LimitPrzekroczony):
        sparsuj(dane)


def test_bom() -> None:
    with pytest.raises(XmlNiepoprawny, match="BOM"):
        sparsuj(b"\xef\xbb\xbf" + MINI)


def test_doctype() -> None:
    xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b"<!DOCTYPE Faktura>"
        b'<Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/"/>'
    )
    with pytest.raises(XmlNiebezpieczny, match="DOCTYPE"):
        sparsuj(xml)


def test_instrukcja_przetwarzania() -> None:
    xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b"<?xml-stylesheet href='x.xsl'?>"
        b'<Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/"/>'
    )
    with pytest.raises(XmlNiepoprawny, match="instrukcje"):
        sparsuj(xml)


def test_zle_kodowanie_w_deklaracji() -> None:
    xml = b'<?xml version="1.0" encoding="ISO-8859-2"?><Faktura/>'
    with pytest.raises(XmlNiepoprawny, match="kodowania"):
        sparsuj(xml)


def test_zloty_przyklad_sie_parsuje() -> None:
    from pathlib import Path

    dane = Path("korpus/zloty/fa3-przyklad-01.xml").read_bytes()
    dok = sparsuj(dane)
    assert dok.korzen.tag.endswith("Faktura")
