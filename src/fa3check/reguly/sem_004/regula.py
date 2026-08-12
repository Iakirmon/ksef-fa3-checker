"""SEM-004 — wspólna data w P_6, nie w powtórzonych P_6A."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="FaWiersz / P_6A",
    strona=88,
    cytat=(
        "W przypadku, gdy dla wszystkich wierszy faktury data jest wspólna – "
        "wypełnia się pole P_6 (element Fa)."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@rejestruj(
    id="SEM-004",
    tytul="Wspólna data dostawy w P_6 zamiast powtórzeń P_6A",
    poziom=Poziom.SEMANTYCZNA,
    waga=Waga.OSTRZEZENIE,
    zrodlo=ZRODLO,
    dotyczy="//tns:Fa/tns:P_6",
)
def wspolna_data_w_p6(f: Faktura) -> Iterator[Zastrzezenie]:
    daty = [
        (w.text or "").strip()
        for w in f.xp("//tns:Fa/tns:FaWiersz/tns:P_6A")
        if (w.text or "").strip()
    ]
    if len(daty) < 2:
        return
    if len(set(daty)) != 1:
        return
    if f.tekst("//tns:Fa/tns:P_6"):
        return
    wspolna = daty[0]
    yield Zastrzezenie(
        wpis="SEM-004",
        waga=Waga.OSTRZEZENIE,
        poziom=Poziom.SEMANTYCZNA,
        xpath="//tns:Fa/tns:P_6",
        linia=None,
        co=(
            f"We wszystkich {len(daty)} wierszach P_6A ma tę samą datę {wspolna}, "
            "a pole P_6 w elemencie Fa jest puste."
        ),
        dlaczego=(
            "Gdy data jest wspólna dla pozycji, broszura każe wypełnić P_6 w Fa, "
            "a nie powtarzać ją w każdym P_6A."
        ),
        jak_naprawic=(f"Wpisz {wspolna} w polu P_6 elementu Fa i usuń powtórzone P_6A z wierszy."),
        zrodlo=ZRODLO,
    )
