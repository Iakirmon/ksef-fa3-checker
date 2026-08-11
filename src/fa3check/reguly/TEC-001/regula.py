"""TEC-001 — kodowanie UTF-8 bez BOM."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Weryfikacja XML — UTF-8 bez BOM",
    cytat=("musi być kodowana w UTF-8 bez znaku BOM (3 pierwsze bajty 0xEF 0xBB 0xBF),"),
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
)

_BOM = b"\xef\xbb\xbf"


@rejestruj(
    id="TEC-001",
    tytul="Kodowanie UTF-8 bez BOM",
    poziom=Poziom.TECHNICZNA,
    waga=Waga.BLAD,
    zrodlo=ZRODLO,
    dotyczy="/*",
)
def utf8_bez_bom(f: Faktura) -> Iterator[Zastrzezenie]:
    if f.surowe_bajty().startswith(_BOM):
        yield Zastrzezenie(
            wpis="TEC-001",
            waga=Waga.BLAD,
            poziom=Poziom.TECHNICZNA,
            xpath="/*",
            linia=1,
            co=(
                f"Plik zaczyna się od BOM UTF-8 (bajty EF BB BF), a ma {len(f.surowe_bajty())} B. "
                "Wymagane jest UTF-8 bez BOM."
            ),
            dlaczego="KSeF odrzuci fakturę — dokument musi być kodowany w UTF-8 bez znaku BOM.",
            jak_naprawic=(
                "Zapisz plik ponownie w UTF-8 bez BOM (w edytorze wyłącz „UTF-8 with BOM”)."
            ),
            zrodlo=ZRODLO,
        )
