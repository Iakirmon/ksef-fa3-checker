"""Rejestr reguł i tłumaczeń — autodiscovery katalogów."""

from __future__ import annotations

import importlib.util
import inspect
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from fa3check.faktura import Faktura
from fa3check.typy import (
    KluczBledu,
    Poziom,
    Waga,
    WpisBezZrodla,
    Zastrzezenie,
    Zrodlo,
)

FunkcjaReguly = Callable[[Faktura], Iterator[Zastrzezenie]]

_REGULY: dict[str, Regula] = {}
_TLUMACZENIA: dict[str, Tlumaczenie] = {}
_ODKRYTE = False


@dataclass(frozen=True, slots=True)
class Regula:
    id: str
    tytul: str
    poziom: Poziom
    waga: Waga
    zrodlo: Zrodlo
    dotyczy: str
    funkcja: FunkcjaReguly
    katalog: Path


@dataclass(frozen=True, slots=True)
class Tlumaczenie:
    id: str
    klucz: KluczBledu
    zrodlo: Zrodlo
    klasa: type
    katalog: Path


def _wymagaj_zrodla(zrodlo: Zrodlo | None, identyfikator: str) -> Zrodlo:
    if zrodlo is None:
        raise WpisBezZrodla(f"{identyfikator}: brak zrodlo")
    if not zrodlo.cytat or not zrodlo.cytat.strip():
        raise WpisBezZrodla(f"{identyfikator}: puste zrodlo.cytat")
    return zrodlo


def _katalog_z_funkcji(obj: Any) -> Path:
    return Path(inspect.getfile(obj)).resolve().parent


def rejestruj(
    *,
    id: str,
    tytul: str,
    poziom: Poziom,
    waga: Waga,
    zrodlo: Zrodlo,
    dotyczy: str,
) -> Callable[[FunkcjaReguly], FunkcjaReguly]:
    def dekorator(fn: FunkcjaReguly) -> FunkcjaReguly:
        if id in _REGULY or id in _TLUMACZENIA:
            raise WpisBezZrodla(f"Duplikat identyfikatora: {id}")
        z = _wymagaj_zrodla(zrodlo, id)
        katalog = _katalog_z_funkcji(fn)
        for nazwa in ("przechodzi.xml", "lamie.xml"):
            if not (katalog / "fixtures" / nazwa).is_file():
                raise WpisBezZrodla(f"{id}: brak fixtures/{nazwa}")
        _REGULY[id] = Regula(
            id=id,
            tytul=tytul,
            poziom=poziom,
            waga=waga,
            zrodlo=z,
            dotyczy=dotyczy,
            funkcja=fn,
            katalog=katalog,
        )
        return fn

    return dekorator


def tlumacz(
    *,
    id: str,
    klucz: KluczBledu,
    zrodlo: Zrodlo,
) -> Callable[[type], type]:
    def dekorator(klasa: type) -> type:
        if id in _REGULY or id in _TLUMACZENIA:
            raise WpisBezZrodla(f"Duplikat identyfikatora: {id}")
        z = _wymagaj_zrodla(zrodlo, id)
        katalog = _katalog_z_funkcji(klasa)
        if not (katalog / "fixtures" / "wywoluje.xml").is_file():
            raise WpisBezZrodla(f"{id}: brak fixtures/wywoluje.xml")
        _TLUMACZENIA[id] = Tlumaczenie(
            id=id,
            klucz=klucz,
            zrodlo=z,
            klasa=klasa,
            katalog=katalog,
        )
        return klasa

    return dekorator


def _zaladuj_modul(sciezka: Path, nazwa: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nazwa, sciezka)
    if spec is None or spec.loader is None:
        raise WpisBezZrodla(f"Nie można załadować {sciezka}")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def odkryj() -> None:
    """Ładuje wszystkie katalogi reguł i tłumaczeń (idempotentne)."""
    global _ODKRYTE
    if _ODKRYTE:
        return
    baza = Path(__file__).resolve().parent
    for rodzaj, plik in (("reguly", "regula.py"), ("tlumaczenia", "tlumaczenie.py")):
        katalog_rodzaju = baza / rodzaj
        if not katalog_rodzaju.is_dir():
            continue
        for katalog in sorted(katalog_rodzaju.iterdir()):
            if not katalog.is_dir() or katalog.name.startswith(("_", ".")):
                continue
            modul_py = katalog / plik
            if not modul_py.is_file():
                continue
            bezpieczna = katalog.name.replace("-", "_").replace(".", "_")
            _zaladuj_modul(modul_py, f"fa3check.{rodzaj}.{bezpieczna}")
    _ODKRYTE = True


def reset_do_testow() -> None:
    """Czyści rejestr — wyłącznie do testów jednostkowych rejestru."""
    global _ODKRYTE
    _REGULY.clear()
    _TLUMACZENIA.clear()
    _ODKRYTE = False


def reguly() -> tuple[Regula, ...]:
    odkryj()
    return tuple(_REGULY[k] for k in sorted(_REGULY))


def tlumaczenia() -> tuple[Tlumaczenie, ...]:
    odkryj()
    return tuple(_TLUMACZENIA[k] for k in sorted(_TLUMACZENIA))


def pobierz(identyfikator: str) -> Regula | Tlumaczenie:
    odkryj()
    if identyfikator in _REGULY:
        return _REGULY[identyfikator]
    if identyfikator in _TLUMACZENIA:
        return _TLUMACZENIA[identyfikator]
    raise KeyError(identyfikator)
