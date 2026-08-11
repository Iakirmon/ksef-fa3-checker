"""Współdzielone testy reguł — różnicowo po fixture'ach."""

from __future__ import annotations

import pytest

from fa3check.faktura import Faktura
from fa3check.rejestr import odkryj, reguly, reset_do_testow
from fa3check.safexml import sparsuj


def setup_function() -> None:
    reset_do_testow()


def _zastrzezenia_z_pliku(sciezka) -> set[str]:  # type: ignore[no-untyped-def]
    dok = sparsuj(sciezka.read_bytes())
    f = Faktura.z_dokumentu(dok)
    wynik: set[str] = set()
    for r in reguly():
        for z in r.funkcja(f):
            wynik.add(z.wpis)
    return wynik


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "regula_id" in metafunc.fixturenames:
        reset_do_testow()
        odkryj()
        metafunc.parametrize("regula_id", [r.id for r in reguly()])


def test_roznicowo_lamie_minus_przechodzi(regula_id: str) -> None:
    reset_do_testow()
    odkryj()
    regula = next(r for r in reguly() if r.id == regula_id)
    przechodzi = _zastrzezenia_z_pliku(regula.katalog / "fixtures" / "przechodzi.xml")
    lamie = _zastrzezenia_z_pliku(regula.katalog / "fixtures" / "lamie.xml")
    assert lamie - przechodzi == {regula_id}
