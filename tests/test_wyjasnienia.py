"""Jakość wyjaśnień zastrzeżeń."""

from __future__ import annotations

import re

import pytest
from tests.helpers import faktura_z_fixture

from fa3check.rejestr import odkryj, reguly, reset_do_testow

ZWROTY_ZAKAZANE = [
    "nieprawidłowa wartość",
    "błąd walidacji",
    "niepoprawne dane",
    "niezgodne ze specyfikacją",
    "popraw wartość",
    "sprawdź poprawność",
    "atomic type",
    "facet",
]

ZARGON = ["atomic type", "facet", "XSD", "schema validation"]


def setup_function() -> None:
    reset_do_testow()


def _pola_fa3(tekst: str) -> bool:
    if re.search(r"\d", tekst):
        return True
    return bool(
        re.search(
            r"\b(NIP|NrVatUE|NrID|P_\d+|Podmiot[123]|FaWiersz|KodUE|BOM|UTF-8)\b",
            tekst,
        )
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "regula_id" in metafunc.fixturenames:
        reset_do_testow()
        odkryj()
        metafunc.parametrize("regula_id", [r.id for r in reguly()])


def test_wyjasnienia_lamie(regula_id: str) -> None:
    reset_do_testow()
    odkryj()
    regula = next(r for r in reguly() if r.id == regula_id)
    # TEC-006/007: przechodzi też odpala regułę
    sciezka = regula.katalog / "fixtures" / "lamie.xml"
    f = faktura_z_fixture(sciezka)
    zastrzezenia = list(regula.funkcja(f))
    assert zastrzezenia, f"{regula_id}: lamie.xml nie wyprodukowało zastrzeżenia"
    for z in zastrzezenia:
        for pole in (z.co, z.dlaczego, z.jak_naprawic):
            assert len(pole) > 20, f"{regula_id}: za krótkie pole"
            low = pole.lower()
            for zakaz in ZWROTY_ZAKAZANE:
                assert zakaz.lower() not in low, f"{regula_id}: zakazany zwrot '{zakaz}'"
            for zargon in ZARGON:
                assert zargon.lower() not in low, f"{regula_id}: żargon '{zargon}'"
        assert _pola_fa3(z.co), f"{regula_id}: 'co' bez liczby/nazwy pola"
