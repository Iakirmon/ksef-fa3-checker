"""Fuzz: sparsuj rzuca tylko Fa3Error; zwaliduj zawsze zwraca Wynik."""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from fa3check.safexml import sparsuj
from fa3check.typy import Fa3Error, Wynik
from fa3check.walidacja import zwaliduj

ROOT = Path(__file__).resolve().parents[1]
ZLOTY = list((ROOT / "korpus" / "zloty").glob("fa3-przyklad-*.xml"))
PRZYKLAD = ZLOTY[0].read_bytes() if ZLOTY else b"<a/>"


@settings(
    max_examples=40,
    deadline=2000,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(st.binary(max_size=8000))
def test_sparsuj_losowe_bajty_tylko_fa3error(dane: bytes) -> None:
    try:
        sparsuj(dane)
    except Fa3Error:
        return


@settings(
    max_examples=30,
    deadline=3000,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(st.binary(min_size=1, max_size=200))
def test_sparsuj_mutacje_zlotego(mutacja: bytes) -> None:
    # Podmień fragment środka złotego przykładu
    baza = bytearray(PRZYKLAD)
    if not baza:
        pytest.skip("brak złotego korpusu")
    poz = len(baza) // 2
    baza[poz : poz + len(mutacja)] = mutacja[: min(len(mutacja), 50)]
    try:
        sparsuj(bytes(baza))
    except Fa3Error:
        return


@settings(
    max_examples=40,
    deadline=5000,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(st.binary(max_size=4000))
def test_zwaliduj_zawsze_wynik(dane: bytes) -> None:
    wynik = zwaliduj(dane)
    assert isinstance(wynik, Wynik)
    assert isinstance(wynik.zastrzezenia, tuple)
