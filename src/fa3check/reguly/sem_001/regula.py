"""SEM-001 — polski NIP nabywcy w niewłaściwym polu."""

from __future__ import annotations

import re
from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Formaty pól (danych) pliku faktury ustrukturyzowanej, ramka WAŻNE",
    strona=6,
    cytat=(
        "Polski identyfikator podatkowy NIP nabywcy należy podawać w polu NIP "
        "w elemencie Podmiot2/DaneIdentyfikacyjne. Nie należy wskazywać go w polu "
        "NrVatUE, ani w polu NrID. Faktura zostanie odpowiednio udostępniona nabywcy "
        "w KSeF wyłącznie, gdy jego identyfikator podatkowy NIP ujęto w polu NIP, "
        "a nie w polu NrVatUE lub NrID."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)

_WZORZEC_NIP = re.compile(r"^[1-9]((\d[1-9])|([1-9]\d))\d{7}$")


def _wyglada_na_polski_nip(wartosc: str) -> bool:
    s = wartosc.strip()
    if s.upper().startswith("PL") and len(s) > 2 and s[2:].isdigit():
        s = s[2:]
    return _WZORZEC_NIP.match(s) is not None


def _czysty_nip(wartosc: str) -> str:
    s = wartosc.strip()
    if s.upper().startswith("PL") and len(s) > 2:
        return s[2:]
    return s


@rejestruj(
    id="SEM-001",
    tytul="Polski NIP nabywcy podany w polu NrVatUE albo NrID",
    poziom=Poziom.SEMANTYCZNA,
    waga=Waga.BLAD,
    zrodlo=ZRODLO,
    dotyczy="//tns:Podmiot2/tns:DaneIdentyfikacyjne",
)
def nip_nabywcy_we_wlasciwym_polu(f: Faktura) -> Iterator[Zastrzezenie]:
    """Wykrywa polski NIP zapisany w NrVatUE albo NrID zamiast w polu NIP."""
    if f.obecny("//tns:Podmiot2/tns:DaneIdentyfikacyjne/tns:NIP"):
        return

    for pole in ("NrVatUE", "NrID"):
        wyrazenie = f"//tns:Podmiot2/tns:DaneIdentyfikacyjne/tns:{pole}"
        wezly = f.xp(wyrazenie)
        if not wezly:
            continue
        wezel = wezly[0]
        wartosc = (wezel.text or "").strip()
        if not wartosc or not _wyglada_na_polski_nip(wartosc):
            continue
        numer = _czysty_nip(wartosc)
        yield Zastrzezenie(
            wpis="SEM-001",
            waga=Waga.BLAD,
            poziom=Poziom.SEMANTYCZNA,
            xpath=wyrazenie,
            linia=f.linia(wezel),
            co=(
                f"Numer {numer} wygląda na polski NIP, a jest zapisany w polu {pole}. "
                "Pole NIP w elemencie Podmiot2/DaneIdentyfikacyjne jest puste."
            ),
            dlaczego=(
                "Faktura zostanie przyjęta przez KSeF i dostanie numer, ale nabywca jej "
                "nie zobaczy — system udostępnia fakturę nabywcy tylko wtedy, gdy jego NIP "
                f"jest w polu NIP, a nie w {pole}."
            ),
            jak_naprawic=(
                f"Przenieś {numer} do pola NIP w elemencie "
                f"Podmiot2/DaneIdentyfikacyjne i usuń {pole}. Pole NrVatUE służy do "
                "numerów VAT UE kontrahentów zagranicznych, a NrID — do innych "
                "identyfikatorów podatkowych."
            ),
            zrodlo=ZRODLO,
        )
