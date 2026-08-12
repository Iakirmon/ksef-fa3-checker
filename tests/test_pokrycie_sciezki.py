"""Dodatkowe ścieżki walidacji i tłumaczeń pod pokrycie."""

from __future__ import annotations

from pathlib import Path

from fa3check import walidacja as wal_mod
from fa3check.rejestr import odkryj, reset_do_testow, tlumaczenia
from fa3check.typy import BladSchematu, Waga
from fa3check.walidacja import zwaliduj


def setup_function() -> None:
    reset_do_testow()


def test_zwaliduj_doctype_jako_zastrzezenie() -> None:
    xml = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b"<!DOCTYPE Faktura>"
        b'<Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/"/>'
    )
    wynik = zwaliduj(xml)
    assert not wynik.schema_ok
    assert wynik.zastrzezenia[0].wpis == "XML-NIEBEZPIECZNY"


def test_zwaliduj_limit_rozmiaru() -> None:
    from fa3check.safexml import LIMIT_BAJTOW

    wynik = zwaliduj(b"x" * (LIMIT_BAJTOW + 1))
    assert wynik.zastrzezenia[0].wpis == "LIMIT"


def test_zwaliduj_xml_niepoprawny() -> None:
    wynik = zwaliduj(b"to nie jest xml <<<")
    assert wynik.zastrzezenia[0].wpis == "XML-NIEPOPRAWNY"


def test_awaria_reguly_jako_informacja(monkeypatch: object) -> None:
    reset_do_testow()
    odkryj()
    from fa3check.rejestr import reguly

    monkeypatch.setattr(wal_mod, "RYGOR_REGUL", False)  # type: ignore[attr-defined]

    def wybuch(_f):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    for r in reguly():
        if r.id == "SEM-001":
            object.__setattr__(r, "funkcja", wybuch)  # type: ignore[misc]
            break

    dane = Path("korpus/zloty/fa3-przyklad-01.xml").read_bytes()
    # Faktura złota — SEM-001 nie powinna i tak odpalić; wymuś przez monkeypatch poziomu
    # Nadpisz funkcję już zrobione; wywołaj bezpośrednio _uruchom_reguly
    from fa3check.faktura import Faktura
    from fa3check.safexml import sparsuj
    from fa3check.typy import Poziom

    f = Faktura.z_dokumentu(sparsuj(dane))
    online, _offline = wal_mod._uruchom_reguly(f, {Poziom.SEMANTYCZNA})
    assert any(z.wpis == "SEM-001" and z.waga == Waga.INFORMACJA for z in online)


def test_zapasowe_i_wzorzec_vatue() -> None:
    odkryj()
    zap = next(t for t in tlumaczenia() if t.id == "XSD-zapasowe")
    blad = BladSchematu(
        typ_lxml="SCHEMAV_CVC_UNKNOWN",
        element="X",
        typ_xsd=None,
        xpath="/*",
        linia=1,
        wartosc="y",
        komunikat="x",
    )
    inst = zap.klasa()
    assert "FA(3)" in inst.co(blad)
    assert "schematu" in inst.dlaczego(blad).lower() or "KSeF" in inst.dlaczego(blad)
    assert "Popraw" in inst.jak_naprawic(blad) or "popraw" in inst.jak_naprawic(blad).lower()

    wz = next(t for t in tlumaczenia() if t.id == "XSD-wzorzec")
    blad_ue = BladSchematu(
        typ_lxml="SCHEMAV_CVC_PATTERN_VALID",
        element="NrVatUE",
        typ_xsd="TNrVatUE",
        xpath="/*",
        linia=1,
        wartosc="PL-1",
        komunikat="",
    )
    inst_w = wz.klasa()
    assert "identyfikacji podatkowej" in inst_w.co(blad_ue)
    assert "ciąg cyfr" in inst_w.jak_naprawic(blad_ue)
