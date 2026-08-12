"""SEM-005 — P_6A tylko przy różnych datach pozycji."""

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
        "Pole wypełnia się w przypadku, gdy dla poszczególnych pozycji faktury "
        "występują różne daty. W przeciwnym przypadku pole pozostaje puste."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@rejestruj(
    id="SEM-005",
    tytul="P_6A przy identycznych datach pozycji",
    poziom=Poziom.SEMANTYCZNA,
    waga=Waga.OSTRZEZENIE,
    zrodlo=ZRODLO,
    dotyczy="//tns:FaWiersz/tns:P_6A",
)
def p6a_przy_roznych_datach(f: Faktura) -> Iterator[Zastrzezenie]:
    daty = [
        (w.text or "").strip()
        for w in f.xp("//tns:Fa/tns:FaWiersz/tns:P_6A")
        if (w.text or "").strip()
    ]
    if len(daty) < 2:
        return
    if len(set(daty)) != 1:
        return
    # SEM-004 pokrywa przypadek bez P_6; tu: P_6 jest, a P_6A i tak powtarza tę samą datę.
    if not f.tekst("//tns:Fa/tns:P_6"):
        return
    wspolna = daty[0]
    yield Zastrzezenie(
        wpis="SEM-005",
        waga=Waga.OSTRZEZENIE,
        poziom=Poziom.SEMANTYCZNA,
        xpath="//tns:FaWiersz/tns:P_6A",
        linia=None,
        co=(f"P_6A powtarza datę {wspolna} w {len(daty)} wierszach — daty pozycji nie są różne."),
        dlaczego=(
            "Broszura przewiduje P_6A tylko wtedy, gdy daty poszczególnych pozycji się różnią; "
            "w przeciwnym razie pole ma zostać puste (wspólna data idzie do P_6)."
        ),
        jak_naprawic=("Usuń P_6A z wierszy; wspólna data pozostaje w polu P_6 elementu Fa."),
        zrodlo=ZRODLO,
    )
