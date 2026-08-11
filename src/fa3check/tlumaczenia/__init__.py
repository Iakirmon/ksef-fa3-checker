"""Dopasowanie błędów XSD do tłumaczeń — nigdy po treści komunikatu.

Katalogi `tlumaczenia/<ID>/` to wpisy rejestru; ten pakiet eksportuje `dopasuj` / `na_zastrzezenie`.
"""

from __future__ import annotations

from typing import Any

from fa3check.rejestr import Tlumaczenie, odkryj
from fa3check.rejestr import tlumaczenia as lista_tlumaczen
from fa3check.struktura import RoznicaStruktury, porownaj
from fa3check.typy import BladSchematu, KluczBledu, Poziom, Waga, Zastrzezenie


def _score(klucz: KluczBledu, blad: BladSchematu) -> int | None:
    if klucz.typ_lxml is not None and klucz.typ_lxml != blad.typ_lxml:
        return None
    if klucz.typ_xsd is not None and klucz.typ_xsd != blad.typ_xsd:
        return None
    if klucz.element is not None and klucz.element != blad.element:
        return None
    score = 0
    if klucz.element is not None:
        score += 4
    if klucz.typ_xsd is not None:
        score += 2
    if klucz.typ_lxml is not None:
        score += 1
    return score


def dopasuj(blad: BladSchematu) -> Tlumaczenie:
    """Dopasuj wyłącznie po KluczBledu — nie po blad.komunikat."""
    odkryj()
    najlepsze: Tlumaczenie | None = None
    najlepszy_score = -1
    zapasowe: Tlumaczenie | None = None
    for t in lista_tlumaczen():
        if t.id == "XSD-zapasowe":
            zapasowe = t
            continue
        for klucz in t.klucze or (t.klucz,):
            wynik = _score(klucz, blad)
            if wynik is None:
                continue
            if wynik > najlepszy_score:
                najlepszy_score = wynik
                najlepsze = t
    if najlepsze is not None:
        return najlepsze
    if zapasowe is None:
        raise RuntimeError("Brak tłumaczenia XSD-zapasowe w rejestrze")
    return zapasowe


def na_zastrzezenie(
    blad: BladSchematu,
    rodzic: Any | None = None,
) -> Zastrzezenie:
    tlum = dopasuj(blad)
    inst: Any = tlum.klasa()
    if (
        blad.typ_lxml == "SCHEMAV_ELEMENT_CONTENT"
        and rodzic is not None
        and hasattr(inst, "ustaw_roznice")
    ):
        roznica: RoznicaStruktury = porownaj(rodzic)
        inst.ustaw_roznice(roznica)
    return Zastrzezenie(
        wpis=tlum.id,
        waga=Waga.BLAD,
        poziom=Poziom.SCHEMA,
        xpath=blad.xpath or "/*",
        linia=blad.linia or None,
        co=inst.co(blad),
        dlaczego=inst.dlaczego(blad),
        jak_naprawic=inst.jak_naprawic(blad),
        zrodlo=tlum.zrodlo,
        diagnostyka=blad.komunikat,
    )
