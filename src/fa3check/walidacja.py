"""Orkiestracja walidacji FA(3)."""

from __future__ import annotations

import time
from collections.abc import Iterator

from fa3check.faktura import NS, Faktura
from fa3check.rejestr import reguly
from fa3check.safexml import Dokument, sparsuj
from fa3check.schema import sprawdz
from fa3check.tlumaczenia import na_zastrzezenie
from fa3check.typy import (
    Poziom,
    Waga,
    Wynik,
    Zastrzezenie,
    Zrodlo,
)

NS_FA3 = NS["tns"]
KORZEN_OCZEKIWANY = "Faktura"

ZRODLO_KORZEN = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Wzór faktury ustrukturyzowanej",
    strona=3,
    cytat=(
        "Struktury logiczna FA(3) w wersji produkcyjnej jest dostępna pod adresem: "
        "https://crd.gov.pl/wzor/2025/06/25/13775/."
    ),
    url="https://crd.gov.pl/wzor/2025/06/25/13775/",
)

# W testach pytest ustawiane na True — wyjątek reguły wywala test.
RYGOR_REGUL = False


def _kolejnosc_wagi(waga: Waga) -> int:
    return {Waga.BLAD: 0, Waga.OSTRZEZENIE: 1, Waga.INFORMACJA: 2}[waga]


def _sortuj(zastrzezenia: list[Zastrzezenie]) -> tuple[Zastrzezenie, ...]:
    return tuple(
        sorted(
            zastrzezenia,
            key=lambda z: (_kolejnosc_wagi(z.waga), z.linia or 0, z.wpis),
        )
    )


def _qname(tag: str) -> tuple[str | None, str]:
    if isinstance(tag, str) and tag.startswith("{") and "}" in tag:
        ns, lokalna = tag[1:].split("}", 1)
        return ns, lokalna
    return None, str(tag)


def _zastrzezenie_korzenia(dok: Dokument) -> Zastrzezenie:
    przestrzen, lokalna = _qname(dok.korzen.tag)
    przestrzen_txt = przestrzen or "(brak)"
    return Zastrzezenie(
        wpis="KORZEN",
        waga=Waga.BLAD,
        poziom=Poziom.SCHEMA,
        xpath="/*",
        linia=getattr(dok.korzen, "sourceline", None),
        co=(
            f"Korzeń dokumentu to `{lokalna}` w przestrzeni `{przestrzen_txt}`, "
            f"a oczekiwany jest `Faktura` w przestrzeni `{NS_FA3}`."
        ),
        dlaczego=(
            "Bez poprawnego korzenia i przestrzeni nazw dokument nie jest fakturą FA(3) "
            "i nie może być przyjęty do KSeF jako faktura ustrukturyzowana."
        ),
        jak_naprawic=(
            "Upewnij się, że wklejasz XML faktury FA(3) z elementem korzeniowym "
            f'`Faktura` oraz atrybutem xmlns="{NS_FA3}".'
        ),
        zrodlo=ZRODLO_KORZEN,
    )


def _rodzic_bledu(dok: Dokument, xpath: str) -> object | None:
    if not xpath:
        return None
    try:
        wezly = dok.korzen.getroottree().xpath(xpath)
    except Exception:
        return None
    if not isinstance(wezly, list) or not wezly:
        return None
    rodzic = wezly[0].getparent()
    return rodzic if rodzic is not None else None


def _uruchom_reguly(
    faktura: Faktura,
    poziomy: set[Poziom],
) -> Iterator[Zastrzezenie]:
    for regula in reguly():
        if regula.poziom not in poziomy:
            continue
        try:
            yield from regula.funkcja(faktura)
        except Exception as exc:
            if RYGOR_REGUL:
                raise
            yield Zastrzezenie(
                wpis=regula.id,
                waga=Waga.INFORMACJA,
                poziom=regula.poziom,
                xpath=regula.dotyczy,
                linia=None,
                co=f"Reguła {regula.id} nie mogła się wykonać.",
                dlaczego=(
                    "Awaria pojedynczej reguły nie powinna ukrywać pozostałych wyników walidacji."
                ),
                jak_naprawic=(
                    "Zgłoś problem autorowi walidatora; wynik pozostałych reguł "
                    "jest nadal miarodajny."
                ),
                zrodlo=regula.zrodlo,
                diagnostyka=type(exc).__name__,
            )


def _korzen_ok(dok: Dokument) -> bool:
    przestrzen, lokalna = _qname(dok.korzen.tag)
    return lokalna == KORZEN_OCZEKIWANY and przestrzen == NS_FA3


def zwaliduj(dane: bytes) -> Wynik:
    t0 = time.perf_counter()
    dok = sparsuj(dane)
    if not _korzen_ok(dok):
        return Wynik(
            zastrzezenia=_sortuj([_zastrzezenie_korzenia(dok)]),
            schema_ok=False,
            czesciowy=False,
            czas_ms=int((time.perf_counter() - t0) * 1000),
        )

    faktura = Faktura.z_dokumentu(dok)
    zastrzezenia: list[Zastrzezenie] = []
    zastrzezenia.extend(_uruchom_reguly(faktura, {Poziom.TECHNICZNA}))

    bledy = sprawdz(dok)
    schema_ok = not bledy
    for blad in bledy:
        rodzic = _rodzic_bledu(dok, blad.xpath)
        zastrzezenia.append(na_zastrzezenie(blad, rodzic=rodzic))

    # Semantyka i arytmetyka zawsze — także przy błędach schematu.
    zastrzezenia.extend(_uruchom_reguly(faktura, {Poziom.SEMANTYCZNA, Poziom.ARYTMETYCZNA}))

    return Wynik(
        zastrzezenia=_sortuj(zastrzezenia),
        schema_ok=schema_ok,
        czesciowy=not schema_ok,
        czas_ms=int((time.perf_counter() - t0) * 1000),
    )
