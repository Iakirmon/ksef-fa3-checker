"""Testy rejestru wpisów."""

from __future__ import annotations

from pathlib import Path

import pytest

from fa3check.rejestr import odkryj, pobierz, reguly, reset_do_testow, tlumaczenia
from fa3check.typy import Poziom, Waga, WpisBezZrodla, Zrodlo


def setup_function() -> None:
    reset_do_testow()


def test_odkryj_znajduje_sem001() -> None:
    odkryj()
    ids = {r.id for r in reguly()}
    assert "SEM-001" in ids
    r = pobierz("SEM-001")
    assert r.poziom == Poziom.SEMANTYCZNA  # type: ignore[union-attr]
    assert r.waga == Waga.BLAD  # type: ignore[union-attr]
    assert (r.katalog / "zrodlo.md").is_file()  # type: ignore[union-attr]


def test_kazdy_wpis_ma_zrodlo_i_fixture() -> None:
    odkryj()
    for r in reguly():
        assert r.zrodlo.dokument
        assert r.zrodlo.wersja
        assert r.zrodlo.sekcja
        assert r.zrodlo.cytat.strip()
        assert (r.katalog / "fixtures" / "przechodzi.xml").is_file()
        assert (r.katalog / "fixtures" / "lamie.xml").is_file()
    for t in tlumaczenia():
        assert t.zrodlo.cytat.strip()
        assert (t.katalog / "fixtures" / "wywoluje.xml").is_file()


def test_rejestracja_odrzuca_pusty_cytat(tmp_path: Path) -> None:
    from fa3check import rejestr as rej

    reset_do_testow()

    def pusta(_f):  # type: ignore[no-untyped-def]
        if False:
            yield  # pragma: no cover

    with pytest.raises(WpisBezZrodla, match="cytat"):
        rej.rejestruj(
            id="TEST-PUSTY",
            tytul="x",
            poziom=Poziom.SEMANTYCZNA,
            waga=Waga.BLAD,
            zrodlo=Zrodlo(
                dokument="d",
                wersja="v",
                sekcja="s",
                cytat="   ",
            ),
            dotyczy="//tns:Fa",
        )(pusta)


def test_rejestracja_odrzuca_brak_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from fa3check import rejestr as rej

    reset_do_testow()
    modul = tmp_path / "regula_test.py"
    modul.write_text("def f(x):\n    if False:\n        yield 0\n", encoding="utf-8")
    monkeypatch.setattr(rej.inspect, "getfile", lambda _obj: str(modul))

    def fn(_f):  # type: ignore[no-untyped-def]
        if False:
            yield  # pragma: no cover

    with pytest.raises(WpisBezZrodla, match="fixtures"):
        rej.rejestruj(
            id="TEST-FIX",
            tytul="x",
            poziom=Poziom.SEMANTYCZNA,
            waga=Waga.BLAD,
            zrodlo=Zrodlo(dokument="d", wersja="v", sekcja="s", cytat="cytat testowy"),
            dotyczy="//tns:Fa",
        )(fn)
