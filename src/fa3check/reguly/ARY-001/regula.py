"""ARY-001 — różnica P_15 i sumy P_15Z."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal, InvalidOperation

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Fa / ZaliczkaCzesciowa",
    strona=78,
    cytat=(
        "różnica kwoty w polu P_15 i sumy poszczególnych pól P_15Z stanowi kwotę "
        "pozostałą ponad płatności otrzymane przed wykonaniem czynności "
        "udokumentowanej fakturą"
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@rejestruj(
    id="ARY-001",
    tytul="Suma P_15Z nie przekracza P_15",
    poziom=Poziom.ARYTMETYCZNA,
    waga=Waga.OSTRZEZENIE,
    zrodlo=ZRODLO,
    dotyczy="//tns:Fa/tns:P_15",
)
def p15_a_suma_p15z(f: Faktura) -> Iterator[Zastrzezenie]:
    """Gdy są P_15Z, ich suma nie powinna przekraczać P_15 (reszta byłaby ujemna)."""
    p15 = f.dec("//tns:Fa/tns:P_15")
    if p15 is None:
        return
    wezly = f.xp("//tns:Fa/tns:ZaliczkaCzesciowa/tns:P_15Z")
    if not wezly:
        return
    wartosci: list[Decimal] = []
    for wezel in wezly:
        tekst = (getattr(wezel, "text", None) or "").strip()
        if not tekst:
            return
        try:
            wartosci.append(Decimal(tekst))
        except InvalidOperation:
            return
    suma = sum(wartosci, start=Decimal("0"))
    if suma <= p15:
        return
    yield Zastrzezenie(
        wpis="ARY-001",
        waga=Waga.OSTRZEZENIE,
        poziom=Poziom.ARYTMETYCZNA,
        xpath="//tns:Fa/tns:P_15",
        linia=None,
        co=(
            f"Suma pól P_15Z wynosi {suma}, a P_15 wynosi {p15} — różnica byłaby ujemna "
            f"({p15 - suma})."
        ),
        dlaczego=(
            "Według broszury różnica P_15 i sumy P_15Z to kwota pozostała ponad wcześniejsze "
            "płatności; ujemna reszta oznacza niespójne kwoty zaliczek."
        ),
        jak_naprawic=(
            "Zmniejsz poszczególne P_15Z albo podnieś P_15 tak, by suma zaliczek nie "
            "przekraczała należności ogółem."
        ),
        zrodlo=ZRODLO,
    )
