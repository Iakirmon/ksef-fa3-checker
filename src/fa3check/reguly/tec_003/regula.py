"""TEC-003 — brak niedozwolonych znaków Unicode."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Weryfikacja XML — niezalecane znaki Unicode",
    cytat=(
        "nie może zawierać niezalecanych znaków Unicode określonych w specyfikacji "
        "[XML W3C](https://www.w3.org/TR/xml/#charsets), tj. znaków z zakresów:"
    ),
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
)


def _niedozwolony(cp: int) -> bool:
    if 0x7F <= cp <= 0x84:
        return True
    if 0x86 <= cp <= 0x9F:
        return True
    if 0xFDD0 <= cp <= 0xFDEF:
        return True
    return (cp & 0xFFFF) >= 0xFFFE


@rejestruj(
    id="TEC-003",
    tytul="Brak niedozwolonych znaków Unicode",
    poziom=Poziom.TECHNICZNA,
    waga=Waga.BLAD,
    zrodlo=ZRODLO,
    dotyczy="/*",
)
def brak_niedozwolonych_unicode(f: Faktura) -> Iterator[Zastrzezenie]:
    try:
        tekst = f.surowe_bajty().decode("utf-8")
    except UnicodeDecodeError:
        return
    for i, ch in enumerate(tekst):
        if _niedozwolony(ord(ch)):
            yield Zastrzezenie(
                wpis="TEC-003",
                waga=Waga.BLAD,
                poziom=Poziom.TECHNICZNA,
                xpath="/*",
                linia=tekst.count("\n", 0, i) + 1,
                co=(
                    f"W pliku występuje niedozwolony znak Unicode U+{ord(ch):04X} "
                    f"(pozycja bajtowa ok. {i})."
                ),
                dlaczego=(
                    "KSeF odrzuci fakturę — znaki z zakresów niezalecanych w XML 1.0 są zabronione."
                ),
                jak_naprawic=(
                    f"Usuń lub zastąp znak U+{ord(ch):04X} w treści faktury znakiem dozwolonym."
                ),
                zrodlo=ZRODLO,
            )
            return
