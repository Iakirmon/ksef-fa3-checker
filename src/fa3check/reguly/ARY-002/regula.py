"""ARY-002 — wzór KP = WB × SP / (100 + SP)."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="FaWiersz / metoda brutto (art. 106e ust. 7 i 8)",
    strona=90,
    cytat="KP = WB x SP/100+SP",
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)

_TOL = Decimal("0.02")


def _stawka(tekst: str) -> Decimal | None:
    t = tekst.strip().replace("%", "")
    # TStawkaPodatku bywa "23", "5", "0", "zw" itd. — tylko liczby
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


@rejestruj(
    id="ARY-002",
    tytul="Kwota VAT od wartości brutto według wzoru KP",
    poziom=Poziom.ARYTMETYCZNA,
    waga=Waga.BLAD,
    zrodlo=ZRODLO,
    dotyczy="//tns:FaWiersz",
)
def wzor_kp_od_brutto(f: Faktura) -> Iterator[Zastrzezenie]:
    """Gdy wiersz ma P_11A, P_12 (liczbowe) i P_11Vat — sprawdź wzór z broszury."""
    for wezel in f.xp("//tns:Fa/tns:FaWiersz"):
        wb_t = wezel.findtext("{*}P_11A")
        sp_t = wezel.findtext("{*}P_12")
        kp_t = wezel.findtext("{*}P_11Vat")
        if not wb_t or not sp_t or not kp_t:
            continue
        try:
            wb = Decimal(wb_t.strip())
            kp = Decimal(kp_t.strip())
        except InvalidOperation:
            continue
        sp = _stawka(sp_t)
        if sp is None:
            continue
        oczekiwane = (wb * sp / (Decimal("100") + sp)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if abs(kp - oczekiwane) <= _TOL:
            continue
        nr = wezel.findtext("{*}NrWierszaFa") or "?"
        yield Zastrzezenie(
            wpis="ARY-002",
            waga=Waga.BLAD,
            poziom=Poziom.ARYTMETYCZNA,
            xpath="//tns:Fa/tns:FaWiersz",
            linia=f.linia(wezel),
            co=(
                f"Wiersz {nr}: P_11Vat={kp}, a ze wzoru KP=WB×SP/(100+SP) przy "
                f"P_11A={wb} i P_12={sp} wychodzi {oczekiwane}."
            ),
            dlaczego=(
                "Przy metodzie liczenia podatku od wartości brutto broszura podaje wzór "
                "KP = WB × SP/(100+SP); rozjazd kwot oznacza błąd wyliczenia pozycji."
            ),
            jak_naprawic=(
                f"Popraw P_11Vat w wierszu {nr} na {oczekiwane} albo skoryguj P_11A / P_12."
            ),
            zrodlo=ZRODLO,
        )
