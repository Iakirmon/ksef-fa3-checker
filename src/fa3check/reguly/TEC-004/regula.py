"""TEC-004 — limit rozmiaru pliku (1 MB / 3 MB)."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Rozmiar pliku",
    cytat="Maksymalny rozmiar faktury bez załączników: **1\u00a0MB \\*** (1 000 000 bajtów).",
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
)

LIMIT_BEZ = 1_000_000
LIMIT_Z = 3_000_000


@rejestruj(
    id="TEC-004",
    tytul="Limit rozmiaru pliku faktury",
    poziom=Poziom.TECHNICZNA,
    waga=Waga.BLAD,
    zrodlo=ZRODLO,
    dotyczy="/*",
)
def limit_rozmiaru(f: Faktura) -> Iterator[Zastrzezenie]:
    rozmiar = len(f.surowe_bajty())
    ma_zalacznik = f.obecny("//tns:Zalacznik")
    limit = LIMIT_Z if ma_zalacznik else LIMIT_BEZ
    if rozmiar <= limit:
        return
    opis = "z załącznikiem" if ma_zalacznik else "bez załącznika"
    yield Zastrzezenie(
        wpis="TEC-004",
        waga=Waga.BLAD,
        poziom=Poziom.TECHNICZNA,
        xpath="/*",
        linia=1,
        co=(
            f"Plik ma {rozmiar} B ({opis}), a limit KSeF wynosi {limit} B "
            f"({'3 MB' if ma_zalacznik else '1 MB'})."
        ),
        dlaczego="KSeF odrzuci fakturę przekraczającą limit rozmiaru dla danego wariantu.",
        jak_naprawic=(
            "Zmniejsz rozmiar XML albo przenieś załączniki zgodnie z limitami: "
            "1 000 000 B bez Zalacznik, 3 000 000 B z Zalacznik."
        ),
        zrodlo=ZRODLO,
    )
