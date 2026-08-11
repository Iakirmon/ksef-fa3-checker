"""Testy safexml — wektory z korpus/zlosliwe/ (oczekiwanie per wektor)."""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from fa3check.safexml import LIMIT_BAJTOW, _parser, sparsuj
from fa3check.typy import Fa3Error, LimitPrzekroczony, XmlNiebezpieczny, XmlNiepoprawny

ROOT = Path(__file__).resolve().parents[1]
ZLOSLIWE = ROOT / "korpus" / "zlosliwe"

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
    dane = (ROOT / "korpus" / "zloty" / "fa3-przyklad-01.xml").read_bytes()
    dok = sparsuj(dane)
    assert dok.korzen.tag.endswith("Faktura")


def test_bomba_entyfikacyjna() -> None:
    dane = (ZLOSLIWE / "bomba-entyfikacyjna.xml").read_bytes()
    with pytest.raises(Fa3Error):
        sparsuj(dane)


def test_xxe_lokalny_odrzuca_doctype() -> None:
    dane = (ZLOSLIWE / "xxe-lokalny.xml").read_bytes()
    with pytest.raises(XmlNiebezpieczny, match="DOCTYPE"):
        sparsuj(dane)


def test_xxe_lokalny_bez_wycieku_gdy_doctype_dozwolony() -> None:
    """Druga warstwa: nawet bez zakazu DOCTYPE treść pliku nie wycieka (resolve_entities=False)."""
    dane = (ZLOSLIWE / "xxe-lokalny.xml").read_bytes()
    sekret = (ZLOSLIWE / "_sekret_do_xxe.txt").read_text(encoding="utf-8").strip()
    assert "SEKRET_XXE" in sekret
    # Parsuj z tym samym parserem co produkcja (encje nie są rozwiązywane),
    # ale bez naszego jawnego odrzucenia DOCTYPE.
    korzen = etree.fromstring(dane, parser=_parser())
    tekst = "".join(korzen.itertext())
    assert sekret not in tekst
    assert "SEKRET_XXE" not in tekst


def test_xxe_sieciowy_odrzuca_doctype() -> None:
    dane = (ZLOSLIWE / "xxe-sieciowy.xml").read_bytes()
    with pytest.raises(XmlNiebezpieczny, match="DOCTYPE"):
        sparsuj(dane)


def test_zagniezdzenie_10000() -> None:
    dane = (ZLOSLIWE / "zagniezdzenie-10000.xml").read_bytes()
    with pytest.raises(Fa3Error):
        sparsuj(dane)


def test_kodowanie_niezgodne_zlosliwe() -> None:
    dane = (ZLOSLIWE / "kodowanie-niezgodne.xml").read_bytes()
    with pytest.raises(XmlNiepoprawny, match="kodowania"):
        sparsuj(dane)


def test_zlosliwe_bom() -> None:
    dane = (ZLOSLIWE / "z-bom.xml").read_bytes()
    with pytest.raises(XmlNiepoprawny, match="BOM"):
        sparsuj(dane)


def test_plik_4mb_przed_parsowaniem() -> None:
    dane = b"x" * (4 * 1024 * 1024)
    with pytest.raises(LimitPrzekroczony):
        sparsuj(dane)
