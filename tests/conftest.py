"""Konfiguracja pytest."""

from __future__ import annotations

import pytest

import fa3check.walidacja as walidacja
from fa3check.rejestr import reset_do_testow


@pytest.fixture(autouse=True)
def _reset_rejestru() -> None:
    reset_do_testow()
    walidacja.RYGOR_REGUL = True
    yield
    reset_do_testow()
    walidacja.RYGOR_REGUL = False
