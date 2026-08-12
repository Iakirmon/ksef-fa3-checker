"""Współdzielone testy reguł — różnicowo po fixture'ach."""

from __future__ import annotations

import pytest

from fa3check.rejestr import odkryj, reguly, reset_do_testow
from tests.helpers import faktura_z_fixture

# Reguły offline zawsze informujące — nie mają sensownej pary przechodzi/lamie.
_BEZ_ROZNICY = frozenset({"TEC-006", "TEC-007"})


def setup_function() -> None:
    reset_do_testow()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "regula_id" in metafunc.fixturenames:
        reset_do_testow()
        odkryj()
        ids = [r.id for r in reguly() if r.id not in _BEZ_ROZNICY]
        metafunc.parametrize("regula_id", ids)


def _zastrzezenia_z_pliku(sciezka) -> set[str]:  # type: ignore[no-untyped-def]
    f = faktura_z_fixture(sciezka)
    wynik: set[str] = set()
    for r in reguly():
        for z in r.funkcja(f):
            wynik.add(z.wpis)
    return wynik


def test_roznicowo_lamie_minus_przechodzi(regula_id: str) -> None:
    reset_do_testow()
    odkryj()
    regula = next(r for r in reguly() if r.id == regula_id)
    przechodzi = _zastrzezenia_z_pliku(regula.katalog / "fixtures" / "przechodzi.xml")
    lamie = _zastrzezenia_z_pliku(regula.katalog / "fixtures" / "lamie.xml")
    assert lamie - przechodzi == {regula_id}


def test_tec006_ostrzezenie() -> None:
    reset_do_testow()
    odkryj()
    regula = next(r for r in reguly() if r.id == "TEC-006")
    f = faktura_z_fixture(regula.katalog / "fixtures" / "przechodzi.xml")
    zas = list(regula.funkcja(f))
    assert len(zas) == 1
    assert zas[0].waga.value == "ostrzezenie"


def test_tec007_informacja() -> None:
    reset_do_testow()
    odkryj()
    regula = next(r for r in reguly() if r.id == "TEC-007")
    f = faktura_z_fixture(regula.katalog / "fixtures" / "przechodzi.xml")
    zas = list(regula.funkcja(f))
    assert len(zas) == 1
    assert zas[0].waga.value == "informacja"
