"""Typy wynikowe i wyjątki fa3-check."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Poziom(StrEnum):
    SCHEMA = "schema"
    TECHNICZNA = "techniczna"
    SEMANTYCZNA = "semantyczna"
    ARYTMETYCZNA = "arytmetyczna"


class Waga(StrEnum):
    BLAD = "blad"
    OSTRZEZENIE = "ostrzezenie"
    INFORMACJA = "informacja"


@dataclass(frozen=True, slots=True)
class Zrodlo:
    dokument: str
    wersja: str
    sekcja: str
    cytat: str
    strona: int | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class BladSchematu:
    typ_lxml: str
    element: str | None
    typ_xsd: str | None
    xpath: str
    linia: int
    wartosc: str | None
    komunikat: str


@dataclass(frozen=True, slots=True)
class KluczBledu:
    typ_lxml: str | None = None
    typ_xsd: str | None = None
    element: str | None = None


@dataclass(frozen=True, slots=True)
class Zastrzezenie:
    wpis: str
    waga: Waga
    poziom: Poziom
    xpath: str
    linia: int | None
    co: str
    dlaczego: str
    jak_naprawic: str
    zrodlo: Zrodlo
    diagnostyka: str | None = None


@dataclass(frozen=True, slots=True)
class Wynik:
    zastrzezenia: tuple[Zastrzezenie, ...]
    schema_ok: bool
    czesciowy: bool
    czas_ms: int


class Fa3Error(Exception):
    """Bazowy wyjątek projektu."""


class XmlNiebezpieczny(Fa3Error):
    """XML zagrażający bezpieczeństwu (np. DOCTYPE)."""


class XmlNiepoprawny(Fa3Error):
    """XML niepoprawny składniowo lub technicznie."""


class WpisBezZrodla(Fa3Error):
    """Wpis rejestru bez wymaganego źródła lub fixture'ów."""


class LimitPrzekroczony(Fa3Error):
    """Przekroczony limit rozmiaru lub czasu."""


# Alias zgodny z wcześniejszą nazwą w rules
RegulaBezZrodla = WpisBezZrodla
