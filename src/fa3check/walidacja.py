"""Orkiestracja walidacji FA(3)."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import replace

from fa3check.faktura import NS, Faktura
from fa3check.rejestr import reguly
from fa3check.safexml import Dokument, sparsuj
from fa3check.schema import sprawdz
from fa3check.tlumaczenia import na_zastrzezenie
from fa3check.typy import (
    BladSchematu,
    Fa3Error,
    LimitPrzekroczony,
    Poziom,
    Waga,
    Wynik,
    XmlNiebezpieczny,
    XmlNiepoprawny,
    Zastrzezenie,
    Zrodlo,
)

# Im niższy indeks, tym bardziej szczegółowy kod błędu schematu.
_KOLEJNOSC_SZCZEGOLOWOSCI: tuple[str, ...] = (
    "SCHEMAV_CVC_FRACTIONDIGITS_VALID",
    "SCHEMAV_CVC_MAXLENGTH_VALID",
    "SCHEMAV_CVC_MININCLUSIVE_VALID",
    "SCHEMAV_CVC_PATTERN_VALID",
    "SCHEMAV_CVC_DATATYPE_VALID_1_2_1",
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

ZRODLO_TECH = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Weryfikacja XML",
    cytat="musi być przygotowana jako poprawny dokument XML, zgodny z regułami XML 1.0,",
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
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


def _ranga_szczegolowosci(typ_lxml: str) -> int:
    try:
        return _KOLEJNOSC_SZCZEGOLOWOSCI.index(typ_lxml)
    except ValueError:
        return len(_KOLEJNOSC_SZCZEGOLOWOSCI)


def _odszum_duplikaty_schematu(
    pary: list[tuple[BladSchematu, Zastrzezenie]],
) -> list[Zastrzezenie]:
    """Zostaw jedno zastrzeżenie na (xpath, linia) — najbardziej szczegółowy kod."""
    grupy: dict[tuple[str, int | None], list[tuple[BladSchematu, Zastrzezenie]]] = defaultdict(list)
    for blad, zastrzezenie in pary:
        grupy[(zastrzezenie.xpath, zastrzezenie.linia)].append((blad, zastrzezenie))

    wynik: list[Zastrzezenie] = []
    for grupa in grupy.values():
        if len(grupa) == 1:
            wynik.append(grupa[0][1])
            continue
        grupa_posortowana = sorted(grupa, key=lambda p: _ranga_szczegolowosci(p[0].typ_lxml))
        zwyciezca = grupa_posortowana[0][1]
        odrzucone = [z.wpis for _, z in grupa_posortowana[1:]]
        diagnostyka = zwyciezca.diagnostyka or ""
        dopisek = "odszumione:" + ",".join(odrzucone)
        diagnostyka = f"{diagnostyka}; {dopisek}" if diagnostyka else dopisek
        wynik.append(replace(zwyciezca, diagnostyka=diagnostyka))
    return wynik


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
) -> tuple[list[Zastrzezenie], list[Zastrzezenie]]:
    online: list[Zastrzezenie] = []
    offline: list[Zastrzezenie] = []
    for regula in reguly():
        if regula.poziom not in poziomy:
            continue
        try:
            wynik_reguly = list(regula.funkcja(faktura))
        except Exception as exc:
            if RYGOR_REGUL:
                raise
            wynik_reguly = [
                Zastrzezenie(
                    wpis=regula.id,
                    waga=Waga.INFORMACJA,
                    poziom=regula.poziom,
                    xpath=regula.dotyczy,
                    linia=None,
                    co=f"Reguła {regula.id} nie mogła się wykonać.",
                    dlaczego=(
                        "Awaria pojedynczej reguły nie powinna ukrywać pozostałych "
                        "wyników walidacji."
                    ),
                    jak_naprawic=(
                        "Zgłoś problem autorowi walidatora; wynik pozostałych reguł "
                        "jest nadal miarodajny."
                    ),
                    zrodlo=regula.zrodlo,
                    diagnostyka=type(exc).__name__,
                )
            ]
        cel = online if regula.rozstrzygalna_offline else offline
        cel.extend(wynik_reguly)
    return online, offline


def _korzen_ok(dok: Dokument) -> bool:
    przestrzen, lokalna = _qname(dok.korzen.tag)
    return lokalna == KORZEN_OCZEKIWANY and przestrzen == NS_FA3


def _zastrzezenie_parsowania(exc: Fa3Error) -> Zastrzezenie:
    if isinstance(exc, LimitPrzekroczony):
        co = "Plik przekracza dopuszczalny rozmiar 3 MB."
        jak = "Zmniejsz plik albo usuń zbędne załączniki i spróbuj ponownie."
        wpis = "LIMIT"
    elif isinstance(exc, XmlNiebezpieczny):
        co = "Dokument zawiera konstrukcje XML niedozwolone w fakturze FA(3) (np. DOCTYPE)."
        jak = "Usuń deklarację DOCTYPE i encje zewnętrzne z pliku."
        wpis = "XML-NIEBEZPIECZNY"
    elif isinstance(exc, XmlNiepoprawny):
        co = "Dokument nie jest poprawnym XML-em UTF-8 wymaganym dla faktury FA(3)."
        jak = "Zapisz plik jako UTF-8 bez BOM, bez instrukcji przetwarzania, i sprawdź składnię."
        wpis = "XML-NIEPOPRAWNY"
    else:
        co = "Nie udało się odczytać dokumentu jako faktury FA(3)."
        jak = "Sprawdź, czy wklejasz kompletny plik XML faktury."
        wpis = "XML"
    return Zastrzezenie(
        wpis=wpis,
        waga=Waga.BLAD,
        poziom=Poziom.TECHNICZNA,
        xpath="/*",
        linia=None,
        co=co,
        dlaczego=(
            "Bez poprawnego, bezpiecznego XML-a nie da się wiarygodnie sprawdzić pól faktury FA(3)."
        ),
        jak_naprawic=jak,
        zrodlo=ZRODLO_TECH,
        diagnostyka=type(exc).__name__,
    )


def zwaliduj(dane: bytes) -> Wynik:
    t0 = time.perf_counter()
    try:
        dok = sparsuj(dane)
    except Fa3Error as exc:
        return Wynik(
            zastrzezenia=_sortuj([_zastrzezenie_parsowania(exc)]),
            uwagi_offline=(),
            schema_ok=False,
            czesciowy=False,
            czas_ms=int((time.perf_counter() - t0) * 1000),
        )

    if not _korzen_ok(dok):
        return Wynik(
            zastrzezenia=_sortuj([_zastrzezenie_korzenia(dok)]),
            uwagi_offline=(),
            schema_ok=False,
            czesciowy=False,
            czas_ms=int((time.perf_counter() - t0) * 1000),
        )

    faktura = Faktura.z_dokumentu(dok)
    zastrzezenia: list[Zastrzezenie] = []
    uwagi_offline: list[Zastrzezenie] = []
    online_tec, offline_tec = _uruchom_reguly(faktura, {Poziom.TECHNICZNA})
    zastrzezenia.extend(online_tec)
    uwagi_offline.extend(offline_tec)

    bledy = sprawdz(dok)
    schema_ok = not bledy
    pary_schematu: list[tuple[BladSchematu, Zastrzezenie]] = []
    for blad in bledy:
        rodzic = _rodzic_bledu(dok, blad.xpath)
        pary_schematu.append((blad, na_zastrzezenie(blad, rodzic=rodzic)))
    zastrzezenia.extend(_odszum_duplikaty_schematu(pary_schematu))

    # Semantyka i arytmetyka zawsze — także przy błędach schematu.
    online_reszta, offline_reszta = _uruchom_reguly(
        faktura, {Poziom.SEMANTYCZNA, Poziom.ARYTMETYCZNA}
    )
    zastrzezenia.extend(online_reszta)
    uwagi_offline.extend(offline_reszta)

    return Wynik(
        zastrzezenia=_sortuj(zastrzezenia),
        uwagi_offline=_sortuj(uwagi_offline),
        schema_ok=schema_ok,
        czesciowy=not schema_ok,
        czas_ms=int((time.perf_counter() - t0) * 1000),
    )
