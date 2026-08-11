"""Testy słownika tłumaczeń XSD."""

from __future__ import annotations

from dataclasses import replace

import pytest

from fa3check.rejestr import odkryj, reset_do_testow, tlumaczenia
from fa3check.safexml import sparsuj
from fa3check.schema import sprawdz
from fa3check.tlumaczenia import dopasuj
from fa3check.walidacja import zwaliduj


def setup_function() -> None:
    reset_do_testow()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "tlum_id" in metafunc.fixturenames:
        reset_do_testow()
        odkryj()
        metafunc.parametrize(
            "tlum_id",
            [t.id for t in tlumaczenia() if t.id != "XSD-zapasowe"],
        )


def test_fixture_produkuje_dopasowanie(tlum_id: str) -> None:
    reset_do_testow()
    odkryj()
    tlum = next(t for t in tlumaczenia() if t.id == tlum_id)
    dok = sparsuj((tlum.katalog / "fixtures" / "wywoluje.xml").read_bytes())
    bledy = sprawdz(dok)
    assert bledy, f"{tlum_id}: brak błędów XSD"
    dopasowane = {dopasuj(b).id for b in bledy}
    assert tlum_id in dopasowane, f"{tlum_id}: dopasowano {dopasowane}"


def test_dopasowanie_bez_komunikatu() -> None:
    """Po wyzerowaniu komunikatu dopasowanie nadal działa."""
    reset_do_testow()
    odkryj()
    for tlum in tlumaczenia():
        if tlum.id == "XSD-zapasowe":
            continue
        dok = sparsuj((tlum.katalog / "fixtures" / "wywoluje.xml").read_bytes())
        for blad in sprawdz(dok):
            wyzerowany = replace(blad, komunikat="")
            assert dopasuj(wyzerowany).id == dopasuj(blad).id


def test_zadne_fixture_ani_zloty_w_zapasowym() -> None:
    reset_do_testow()
    odkryj()
    from pathlib import Path

    sciezki = [
        t.katalog / "fixtures" / "wywoluje.xml"
        for t in tlumaczenia()
        if t.id != "XSD-zapasowe"
    ]
    sciezki += sorted(Path("korpus/zloty").glob("fa3-przyklad-*.xml"))
    for sciezka in sciezki:
        dok = sparsuj(sciezka.read_bytes())
        for blad in sprawdz(dok):
            assert dopasuj(blad).id != "XSD-zapasowe", (
                f"{sciezka}: {blad.typ_lxml}/{blad.element} → zapasowe"
            )


def test_trzy_rozne_bledy_xsd_obok_siebie() -> None:
    """Faktura z trzema różnymi błędami → trzy sensowne wyjaśnienia."""
    from pathlib import Path

    from lxml import etree

    raw = Path("korpus/zloty/fa3-przyklad-01.xml").read_bytes()
    root = etree.fromstring(raw)
    ns = {"tns": "http://crd.gov.pl/wzor/2025/06/25/13775/"}
    root.xpath("//tns:P_15", namespaces=ns)[0].text = "1234.567"
    root.xpath("//tns:P_1", namespaces=ns)[0].text = "1999-01-01"
    root.xpath("//tns:Podmiot1//tns:Nazwa", namespaces=ns)[0].text = "A" * 513
    dane = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    wynik = zwaliduj(dane)
    ids = {z.wpis for z in wynik.zastrzezenia if z.wpis.startswith("XSD-")}
    assert "XSD-kwota-precyzja" in ids
    assert "XSD-data-zakres" in ids
    assert "XSD-dlugosc" in ids
    for z in wynik.zastrzezenia:
        if z.wpis.startswith("XSD-"):
            assert len(z.co) > 20
            assert len(z.jak_naprawic) > 20
            print(z.wpis, "→", z.co[:100])
