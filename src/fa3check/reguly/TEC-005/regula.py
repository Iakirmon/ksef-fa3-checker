"""TEC-005 — suma kontrolna NIP."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Walidacja numeru NIP",
    cytat=(
        "Sprawdzenie sumy kontrolnej NIP dla: `Podmiot1`, `Podmiot2`, `Podmiot3` oraz "
        "`PodmiotUpowazniony` (jeśli występuje)."
    ),
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
)

_WAGI = (6, 5, 7, 2, 3, 4, 5, 6, 7)
_XPATHY = (
    "//tns:Podmiot1//tns:NIP",
    "//tns:Podmiot2/tns:DaneIdentyfikacyjne/tns:NIP",
    "//tns:Podmiot3//tns:NIP",
    "//tns:PodmiotUpowazniony//tns:NIP",
)


def suma_kontrolna_ok(nip: str) -> bool:
    if len(nip) != 10 or not nip.isdigit():
        return False
    suma = sum(int(nip[i]) * _WAGI[i] for i in range(9))
    reszta = suma % 11
    if reszta == 10:
        return False
    return reszta == int(nip[9])


@rejestruj(
    id="TEC-005",
    tytul="Suma kontrolna NIP",
    poziom=Poziom.TECHNICZNA,
    waga=Waga.BLAD,
    zrodlo=ZRODLO,
    dotyczy="//tns:NIP",
)
def suma_kontrolna_nip(f: Faktura) -> Iterator[Zastrzezenie]:
    widziane: set[str] = set()
    for xp in _XPATHY:
        for wezel in f.xp(xp):
            nip = (wezel.text or "").strip()
            if not nip or nip in widziane:
                continue
            widziane.add(nip)
            if suma_kontrolna_ok(nip):
                continue
            yield Zastrzezenie(
                wpis="TEC-005",
                waga=Waga.BLAD,
                poziom=Poziom.TECHNICZNA,
                xpath=xp,
                linia=f.linia(wezel),
                co=(
                    f"Numer NIP {nip} ma poprawny kształt dziesięciu cyfr, ale błędną "
                    "sumę kontrolną."
                ),
                dlaczego=(
                    "Schemat sprawdza tylko wzorzec NIP, nie modulo. KSeF w środowisku "
                    "produkcyjnym odrzuci fakturę z błędną sumą kontrolną."
                ),
                jak_naprawic=(
                    f"Popraw cyfrę kontrolną NIP {nip} albo wpisz właściwy numer podatnika."
                ),
                zrodlo=ZRODLO,
            )
