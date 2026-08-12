"""Dosłowność cytatów wobec wendorowanych źródeł."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fa3check.rejestr import odkryj, reguly, reset_do_testow, tlumaczenia

ROOT = Path(__file__).resolve().parents[1]
BROSZURA = ROOT / "korpus" / "broszura" / "broszura-fa3.txt"
WERYFIKACJA = ROOT / "korpus" / "zrodla" / "weryfikacja-faktury.md"
SCHEMA_DIR = ROOT / "korpus" / "schema"


def setup_function() -> None:
    reset_do_testow()


def _normalizuj(tekst: str) -> str:
    return re.sub(r"\s+", " ", tekst).strip()


def _strona_cytatu(broszura: str, cytat: str) -> int | None:
    norm_cytat = _normalizuj(cytat)
    strony = re.split(r"=== strona (\d+) ===\n", broszura)
    # split daje: preamble, nr, treść, nr, treść, ...
    i = 1
    while i + 1 < len(strony):
        nr = int(strony[i])
        tresc = strony[i + 1]
        if norm_cytat in _normalizuj(tresc):
            return nr
        i += 2
    return None


@pytest.fixture(scope="module")
def broszura_txt() -> str:
    return BROSZURA.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def weryfikacja_txt() -> str:
    return WERYFIKACJA.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def schema_txt() -> str:
    fragmenty = [p.read_text(encoding="utf-8") for p in sorted(SCHEMA_DIR.glob("*.xsd"))]
    return "\n".join(fragmenty)


def test_sem001_cytat_na_stronie_6(broszura_txt: str) -> None:
    odkryj()
    from fa3check.rejestr import pobierz

    r = pobierz("SEM-001")
    assert r.zrodlo.strona == 6  # type: ignore[union-attr]
    assert _strona_cytatu(broszura_txt, r.zrodlo.cytat) == 6  # type: ignore[union-attr]


def test_wszystkie_cytaty_doslowne(
    broszura_txt: str, weryfikacja_txt: str, schema_txt: str
) -> None:
    odkryj()
    broszura_n = _normalizuj(broszura_txt)
    wer_n = _normalizuj(weryfikacja_txt)
    schema_n = _normalizuj(schema_txt)

    for wpis in (*reguly(), *tlumaczenia()):
        cytat = wpis.zrodlo.cytat
        assert cytat.strip(), wpis.id
        norm = _normalizuj(cytat)
        dok = wpis.zrodlo.dokument.lower()
        if dok.endswith(".xsd"):
            assert wpis.zrodlo.strona is None, f"{wpis.id}: źródło schematowe ma strona=None"
            assert norm in schema_n, f"{wpis.id}: cytatu brak w korpus/schema/"
        elif "weryfikacja" in dok or "ksef-docs" in dok:
            assert norm in wer_n, f"{wpis.id}: cytatu brak w weryfikacja-faktury.md"
        elif "broszura" in dok or "fa(3)" in dok.lower() or wpis.zrodlo.strona is not None:
            assert norm in broszura_n, f"{wpis.id}: cytatu brak w broszurze"
            if wpis.zrodlo.strona is not None:
                assert _strona_cytatu(broszura_txt, cytat) == wpis.zrodlo.strona, (
                    f"{wpis.id}: zła strona"
                )
        else:
            assert norm in broszura_n or norm in wer_n, f"{wpis.id}: cytatu brak w źródłach"

        if wpis.zrodlo.url:
            assert any(
                d in wpis.zrodlo.url
                for d in (
                    "podatki.gov.pl",
                    "crd.gov.pl",
                    "gov.pl",
                    "github.com/CIRFMF",
                )
            ), f"{wpis.id}: url poza domeną MF/CIRFMF"
