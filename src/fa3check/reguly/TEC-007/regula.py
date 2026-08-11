"""TEC-007 — unikalność faktury (wymaga stanu KSeF)."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Unikalność faktury",
    cytat=(
        "KSeF wykrywa duplikaty faktur globalnie, w oparciu o dane przechowywane w systemie. "
        "Kryterium identyfikacji duplikatu stanowi kombinacja:"
    ),
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
)


@rejestruj(
    id="TEC-007",
    tytul="Unikalność: NIP sprzedawcy + rodzaj + numer",
    poziom=Poziom.TECHNICZNA,
    waga=Waga.INFORMACJA,
    zrodlo=ZRODLO,
    dotyczy="//tns:Fa/tns:P_2",
)
def unikalnosc_faktury(f: Faktura) -> Iterator[Zastrzezenie]:
    nip = f.tekst("//tns:Podmiot1//tns:NIP")
    rodzaj = f.tekst("//tns:Fa/tns:RodzajFaktury")
    numer = f.tekst("//tns:Fa/tns:P_2")
    if not (nip and rodzaj and numer):
        return
    wezly = f.xp("//tns:Fa/tns:P_2")
    linia = f.linia(wezly[0]) if wezly else None
    yield Zastrzezenie(
        wpis="TEC-007",
        waga=Waga.INFORMACJA,
        poziom=Poziom.TECHNICZNA,
        xpath="//tns:Fa/tns:P_2",
        linia=linia,
        co=(
            f"Klucz unikalności to NIP sprzedawcy {nip} + rodzaj {rodzaj} + numer {numer}. "
            "Duplikatu nie da się wykryć offline."
        ),
        dlaczego=(
            "KSeF utrzymuje unikalność globalnie i przy kolizji zwraca kod 440 „Duplikat faktury”; "
            "lokalny walidator nie ma dostępu do tej bazy."
        ),
        jak_naprawic=(
            "Przed wysyłką upewnij się, że ten numer nie był już użyty dla tego NIP i rodzaju "
            "faktury w KSeF."
        ),
        zrodlo=ZRODLO,
    )
