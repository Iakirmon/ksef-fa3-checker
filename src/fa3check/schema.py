"""Walidacja wobec schematu FA(3) i mapa element → typ XSD."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from lxml import etree

from fa3check.safexml import Dokument
from fa3check.typy import BladSchematu

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "korpus" / "schema"
SCHEMA_PLIK = SCHEMA_DIR / "schemat_FA(3)_v1-0E.xsd"

XS = "{http://www.w3.org/2001/XMLSchema}"


@lru_cache(maxsize=1)
def wczytaj_schemat() -> etree.XMLSchema:
    parser = etree.XMLParser(load_dtd=False, no_network=True, resolve_entities=False)
    drzewo = etree.parse(str(SCHEMA_PLIK), parser=parser)
    return etree.XMLSchema(drzewo)


def _lokalna_nazwa_typu(wartosc: str) -> str:
    if ":" in wartosc:
        return wartosc.split(":", 1)[1]
    return wartosc


@lru_cache(maxsize=1)
def mapa_typow() -> dict[str, frozenset[str]]:
    """element lokalny → zbiór nazw typów z atrybutu type deklaracji xsd:element."""
    surowa: dict[str, set[str]] = {}
    pliki = [SCHEMA_PLIK, *sorted((SCHEMA_DIR / "bazowe").glob("*.xsd"))]
    for plik in pliki:
        drzewo = etree.parse(str(plik))
        for el in drzewo.iter(f"{XS}element"):
            nazwa = el.get("name")
            typ = el.get("type")
            if not nazwa or not typ:
                continue
            surowa.setdefault(nazwa, set()).add(_lokalna_nazwa_typu(typ))
    return {k: frozenset(v) for k, v in surowa.items()}


def _typ_dla_elementu(nazwa: str | None) -> str | None:
    if not nazwa:
        return None
    typy = mapa_typow().get(nazwa)
    if not typy:
        return None
    if len(typy) != 1:
        return None  # niejednoznaczne typy złożone
    return next(iter(typy))


def _nazwa_elementu(dok: Dokument, xpath: str) -> str | None:
    if not xpath:
        return None
    try:
        wezly = dok.korzen.getroottree().xpath(xpath)
    except etree.XPathError:
        return None
    if not isinstance(wezly, list) or not wezly:
        return None
    wezel = wezly[0]
    try:
        return etree.QName(wezel).localname
    except (TypeError, ValueError):
        return None


def _wartosc_wezla(dok: Dokument, xpath: str) -> str | None:
    if not xpath:
        return None
    try:
        wezly = dok.korzen.getroottree().xpath(xpath)
    except etree.XPathError:
        return None
    if not isinstance(wezly, list) or not wezly:
        return None
    wezel = wezly[0]
    if isinstance(wezel, str):
        return wezel
    tekst = getattr(wezel, "text", None)
    return tekst


def sprawdz(dok: Dokument) -> list[BladSchematu]:
    schemat = wczytaj_schemat()
    ok = schemat.validate(dok.korzen.getroottree())
    if ok:
        return []
    bledy: list[BladSchematu] = []
    for error in cast(Any, schemat.error_log):
        xpath = error.path or ""
        element = _nazwa_elementu(dok, xpath)
        bledy.append(
            BladSchematu(
                typ_lxml=error.type_name or "",
                element=element,
                typ_xsd=_typ_dla_elementu(element),
                xpath=xpath,
                linia=int(error.line or 0),
                wartosc=_wartosc_wezla(dok, xpath),
                komunikat=error.message or "",
            )
        )
    return bledy


def typ_jednoznaczny(element: str) -> str | None:
    """Pomocniczo: jeden typ albo None."""
    return _typ_dla_elementu(element)
