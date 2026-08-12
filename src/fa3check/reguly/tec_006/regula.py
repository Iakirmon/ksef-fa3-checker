"""TEC-006 — data wystawienia vs data przyjęcia (offline nierozstrzygalne)."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Walidacja dat",
    cytat=(
        "Data wystawienia faktury (`P_1`) nie może być późniejsza niż data przyjęcia "
        "dokumentu do systemu KSeF."
    ),
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
)


@rejestruj(
    id="TEC-006",
    tytul="Data wystawienia nie późniejsza niż data przyjęcia",
    poziom=Poziom.TECHNICZNA,
    waga=Waga.OSTRZEZENIE,
    zrodlo=ZRODLO,
    dotyczy="//tns:P_1",
    rozstrzygalna_offline=False,
)
def data_wystawienia_vs_przyjecia(f: Faktura) -> Iterator[Zastrzezenie]:
    """Bez daty przyjęcia z KSeF reguła nie orzeka — tylko ostrzega."""
    wezly = f.xp("//tns:Fa/tns:P_1")
    if not wezly:
        return
    wezel = wezly[0]
    data = (wezel.text or "").strip()
    if not data:
        return
    yield Zastrzezenie(
        wpis="TEC-006",
        waga=Waga.OSTRZEZENIE,
        poziom=Poziom.TECHNICZNA,
        xpath="//tns:Fa/tns:P_1",
        linia=f.linia(wezel),
        co=(
            f"Data wystawienia P_1={data} nie może być późniejsza niż data przyjęcia w KSeF "
            "— tej drugiej daty nie znamy offline."
        ),
        dlaczego=(
            "KSeF porównuje P_1 z momentem przyjęcia w systemie; lokalnie nie da się tego "
            "rozstrzygnąć po jednym pliku."
        ),
        jak_naprawic=(
            "Upewnij się, że P_1 nie jest datą przyszłą względem planowanego wysłania do KSeF."
        ),
        zrodlo=ZRODLO,
    )
