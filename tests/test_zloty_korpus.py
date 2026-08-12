"""Złoty korpus MF — 26/26 bez żadnych zastrzeżeń (uwagi offline osobno)."""

from __future__ import annotations

from pathlib import Path

import pytest

from fa3check.rejestr import reset_do_testow
from fa3check.safexml import sparsuj
from fa3check.schema import mapa_typow, sprawdz, typ_jednoznaczny
from fa3check.walidacja import zwaliduj

ROOT = Path(__file__).resolve().parents[1]
ZLOTY = ROOT / "korpus" / "zloty"
PLIKI = sorted(ZLOTY.glob("fa3-przyklad-*.xml"))


@pytest.fixture(autouse=True)
def _rygor(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_do_testow()
    monkeypatch.setattr("fa3check.walidacja.RYGOR_REGUL", True)


@pytest.mark.parametrize("plik", PLIKI, ids=[p.name for p in PLIKI])
def test_zloty_korpus_plik(plik: Path) -> None:
    dane = plik.read_bytes()
    dok = sparsuj(dane)
    assert sprawdz(dok) == [], f"{plik.name}: błędy XSD"
    wynik = zwaliduj(dane)
    assert wynik.schema_ok, f"{plik.name}: schema_ok=False"
    assert wynik.zastrzezenia == (), (
        f"{plik.name}: zastrzezenia={[z.wpis for z in wynik.zastrzezenia]}"
    )
    assert {z.wpis for z in wynik.uwagi_offline} == {"TEC-006", "TEC-007"}


def test_mapa_typow_kluczowe_pola() -> None:
    oczekiwane = {
        "P_15": "TKwotowy",
        "P_11": "TKwotowy",
        "P_9A": "TKwotowy2",
        "P_1": "TDataT",
        "NIP": "TNrNIP",
        "Nazwa": "TZnakowy512",
        "KursWaluty": "TIlosci",
    }
    mapa = mapa_typow()
    for element, typ in oczekiwane.items():
        assert element in mapa, f"brak {element} w mapie"
        assert typ in mapa[element], f"{element}: {mapa[element]} bez {typ}"
        jedno = typ_jednoznaczny(element)
        assert jedno == typ, f"{element}: jednoznaczny={jedno}"


def test_element_i_typ_bez_komunikatu() -> None:
    """Po uszkodzeniu precyzji P_15 element/typ ustalane z path, nie z message."""
    from copy import copy

    surowy = (ZLOTY / "fa3-przyklad-01.xml").read_bytes()
    dok = sparsuj(surowy)
    # Zepsuj P_15
    ns = {"tns": "http://crd.gov.pl/wzor/2025/06/25/13775/"}
    wezly = dok.korzen.xpath("//tns:P_15", namespaces=ns)
    assert wezly
    wezly[0].text = "1234.567"
    # Przebuduj Dokument z tym samym drzewem
    from fa3check.safexml import Dokument

    dok2 = Dokument(korzen=dok.korzen, surowe=surowy)
    bledy = sprawdz(dok2)
    assert bledy, "oczekiwano błędu schematu"
    blad = next(b for b in bledy if b.typ_lxml == "SCHEMAV_CVC_FRACTIONDIGITS_VALID")
    assert blad.element == "P_15"
    assert blad.typ_xsd == "TKwotowy"
    # Komunikat wyzerowany — nadal mamy element i typ
    blad2 = copy(blad)
    object.__setattr__(blad2, "komunikat", "")  # type: ignore[misc]
    assert blad2.element == "P_15"
    assert blad2.typ_xsd == "TKwotowy"


def test_zly_korzen_zwarciowo() -> None:
    wynik = zwaliduj(b'<?xml version="1.0" encoding="UTF-8"?><html><body/></html>')
    assert not wynik.schema_ok
    assert len(wynik.zastrzezenia) == 1
    assert wynik.zastrzezenia[0].wpis == "KORZEN"
