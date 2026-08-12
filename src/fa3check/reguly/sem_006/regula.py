"""SEM-006 — NrWiersza w DodatkowyOpis wskazuje istniejący wiersz."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Fa / DodatkowyOpis",
    strona=84,
    cytat=(
        "Aby zidentyfikować, którego towaru (wymienionego w elemencie FaWiersz) dotyczy "
        "dana informacja dodatkowa, można wskazać w elemencie DodatkowyOpis, w polu "
        "NrWiersza, numer wiersza faktury, do którego odnosi się dana informacja."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@rejestruj(
    id="SEM-006",
    tytul="NrWiersza w DodatkowyOpis wskazuje istniejący FaWiersz",
    poziom=Poziom.SEMANTYCZNA,
    waga=Waga.OSTRZEZENIE,
    zrodlo=ZRODLO,
    dotyczy="//tns:DodatkowyOpis/tns:NrWiersza",
)
def nr_wiersza_opisu(f: Faktura) -> Iterator[Zastrzezenie]:
    istniejace = {
        (w.text or "").strip()
        for w in f.xp("//tns:Fa/tns:FaWiersz/tns:NrWierszaFa")
        if (w.text or "").strip()
    }
    for wezel in f.xp("//tns:Fa/tns:DodatkowyOpis/tns:NrWiersza"):
        nr = (wezel.text or "").strip()
        if not nr:
            continue
        if nr in istniejace:
            continue
        yield Zastrzezenie(
            wpis="SEM-006",
            waga=Waga.OSTRZEZENIE,
            poziom=Poziom.SEMANTYCZNA,
            xpath="//tns:Fa/tns:DodatkowyOpis/tns:NrWiersza",
            linia=f.linia(wezel),
            co=(
                f"DodatkowyOpis wskazuje NrWiersza={nr}, ale wśród NrWierszaFa nie ma "
                f"takiego numeru (są: {', '.join(sorted(istniejace)) or 'brak'})."
            ),
            dlaczego=(
                "NrWiersza ma wiązać opis dodatkowy z konkretną pozycją FaWiersz; "
                "wskazanie nieistniejącego numeru gubi to powiązanie."
            ),
            jak_naprawic=(
                "Ustaw NrWiersza na jeden z istniejących NrWierszaFa albo usuń pole NrWiersza."
            ),
            zrodlo=ZRODLO,
        )
