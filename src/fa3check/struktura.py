"""Porównanie dzieci elementu XML z modelem treści ze schematu FA(3)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from lxml import etree

from fa3check.schema import SCHEMA_DIR, SCHEMA_PLIK

XS = "{http://www.w3.org/2001/XMLSchema}"


@dataclass(frozen=True, slots=True)
class RoznicaStruktury:
    rodzic: str
    nadmiarowe: tuple[str, ...]
    brakujace: tuple[str, ...]
    przestawione: tuple[str, ...]
    pewnosc_kolejnosci: bool


@dataclass(frozen=True, slots=True)
class _Czastka:
    nazwa: str
    wymagana: bool
    w_choice: bool
    kolejnosc: int | None


@dataclass(frozen=True, slots=True)
class _Model:
    czastki: tuple[_Czastka, ...]
    zadeklarowane: frozenset[str]
    ma_choice: bool


def _min_occurs(wezel: etree._Element) -> int:
    wartosc = wezel.get("minOccurs")
    if wartosc is None:
        return 1
    try:
        return int(wartosc)
    except ValueError:
        return 1


def _lokalna_nazwa(wartosc: str) -> str:
    if ":" in wartosc:
        return wartosc.split(":", 1)[1]
    return wartosc


@lru_cache(maxsize=1)
def _indeks_schematu() -> tuple[dict[str, etree._Element], dict[str, etree._Element]]:
    elementy: dict[str, etree._Element] = {}
    typy: dict[str, etree._Element] = {}
    pliki = [SCHEMA_PLIK, *sorted((SCHEMA_DIR / "bazowe").glob("*.xsd"))]
    for plik in pliki:
        drzewo = etree.parse(str(plik))
        for el in drzewo.iter(f"{XS}element"):
            nazwa = el.get("name")
            if nazwa and nazwa not in elementy:
                elementy[nazwa] = el
        for ct in drzewo.iter(f"{XS}complexType"):
            nazwa = ct.get("name")
            if nazwa:
                typy[nazwa] = ct
    return elementy, typy


def _complex_type_wezel(
    nazwa_elementu: str | None,
    nazwa_typu: str | None,
) -> etree._Element | None:
    elementy, typy = _indeks_schematu()
    if nazwa_typu:
        return typy.get(nazwa_typu)
    if not nazwa_elementu:
        return None
    dekl = elementy.get(nazwa_elementu)
    if dekl is None:
        return None
    typ_ref = dekl.get("type")
    if typ_ref:
        return typy.get(_lokalna_nazwa(typ_ref))
    for potomek in dekl:
        if etree.QName(potomek).localname == "complexType":
            return potomek
    return None


def _zawartosc_complex_type(ct: etree._Element) -> etree._Element | None:
    for potomek in ct:
        tag = etree.QName(potomek).localname
        if tag in {"sequence", "choice", "all"}:
            return potomek
        if tag == "complexContent":
            for wnuk in potomek:
                if etree.QName(wnuk).localname == "extension":
                    baza = wnuk.get("base")
                    if baza:
                        ct_bazy = _indeks_schematu()[1].get(_lokalna_nazwa(baza))
                        if ct_bazy is not None:
                            return _zawartosc_complex_type(ct_bazy)
                    for wnuk2 in wnuk:
                        if etree.QName(wnuk2).localname in {"sequence", "choice", "all"}:
                            return wnuk2
                if etree.QName(wnuk).localname == "restriction":
                    baza = wnuk.get("base")
                    if baza:
                        ct_bazy = _indeks_schematu()[1].get(_lokalna_nazwa(baza))
                        if ct_bazy is not None:
                            return _zawartosc_complex_type(ct_bazy)
    return None


def _zbierz_czastki(
    wezel: etree._Element,
    lancuch_min: tuple[int, ...],
    w_choice: bool,
    ma_choice: bool,
    kolejnosc: int,
) -> tuple[list[_Czastka], bool, int]:
    wynik: list[_Czastka] = []
    tag = etree.QName(wezel).localname

    if tag == "element":
        nazwa = wezel.get("name")
        if nazwa:
            lancuch = (*lancuch_min, _min_occurs(wezel))
            wymagana = all(m >= 1 for m in lancuch)
            idx = None if w_choice else kolejnosc
            wynik.append(
                _Czastka(
                    nazwa=nazwa,
                    wymagana=wymagana,
                    w_choice=w_choice,
                    kolejnosc=idx,
                )
            )
            if not w_choice:
                kolejnosc += 1
        return wynik, ma_choice, kolejnosc

    if tag not in {"sequence", "choice", "all"}:
        return wynik, ma_choice, kolejnosc

    w_choice_teraz = w_choice or tag == "choice"
    if tag == "choice":
        ma_choice = True
    lancuch_grupy = (*lancuch_min, _min_occurs(wezel))

    for dziecko in wezel:
        dzieci, ma_choice, kolejnosc = _zbierz_czastki(
            dziecko,
            lancuch_grupy,
            w_choice_teraz,
            ma_choice,
            kolejnosc,
        )
        wynik.extend(dzieci)

    return wynik, ma_choice, kolejnosc


def _model_dla_typu(
    nazwa_elementu: str | None,
    nazwa_typu: str | None,
) -> _Model | None:
    ct = _complex_type_wezel(nazwa_elementu, nazwa_typu)
    if ct is None:
        return None
    korzen = _zawartosc_complex_type(ct)
    if korzen is None:
        return None
    czastki, ma_choice, _ = _zbierz_czastki(korzen, (), False, False, 0)
    zadeklarowane = frozenset(c.nazwa for c in czastki)
    return _Model(czastki=tuple(czastki), zadeklarowane=zadeklarowane, ma_choice=ma_choice)


@lru_cache(maxsize=256)
def _model_z_klucza(nazwa_elementu: str | None, nazwa_typu: str | None) -> _Model | None:
    return _model_dla_typu(nazwa_elementu, nazwa_typu)


def _nazwa_wezla(wezel: Any) -> str:
    return etree.QName(wezel).localname


def _dzieci_xml(rodzic: Any) -> list[str]:
    return [_nazwa_wezla(d) for d in rodzic if isinstance(d.tag, str)]


def _brakujace(czastki: tuple[_Czastka, ...], dzieci: list[str]) -> tuple[str, ...]:
    obecne = set(dzieci)
    brak: list[str] = []
    widziane: set[str] = set()
    for c in czastki:
        if not c.wymagana or c.nazwa in widziane:
            continue
        widziane.add(c.nazwa)
        if c.nazwa not in obecne:
            brak.append(c.nazwa)
    return tuple(brak)


def _przestawione(czastki: tuple[_Czastka, ...], dzieci: list[str]) -> tuple[str, ...]:
    indeksy: dict[str, int] = {}
    for c in czastki:
        if c.kolejnosc is not None and c.nazwa not in indeksy:
            indeksy[c.nazwa] = c.kolejnosc

    maksimum = -1
    przestawione: list[str] = []
    widziane: set[str] = set()
    for nazwa in dzieci:
        if nazwa not in indeksy or nazwa in widziane:
            continue
        widziane.add(nazwa)
        idx = indeksy[nazwa]
        if idx < maksimum:
            przestawione.append(nazwa)
        else:
            maksimum = idx
    return tuple(przestawione)


def porownaj(
    rodzic_wezel: Any,
    nazwa_typu_rodzica: str | None = None,
) -> RoznicaStruktury:
    """Porównaj dzieci węzła XML z bezpośrednimi cząstkami typu złożonego ze schematu."""
    nazwa_rodzica = _nazwa_wezla(rodzic_wezel)
    klucz_elementu = None if nazwa_typu_rodzica else nazwa_rodzica
    model = _model_z_klucza(klucz_elementu, nazwa_typu_rodzica)
    dzieci = _dzieci_xml(rodzic_wezel)

    if model is None:
        return RoznicaStruktury(
            rodzic=nazwa_rodzica,
            nadmiarowe=(),
            brakujace=(),
            przestawione=(),
            pewnosc_kolejnosci=True,
        )

    nadmiarowe = tuple(n for n in dzieci if n not in model.zadeklarowane)
    brakujace = _brakujace(model.czastki, dzieci)
    przestawione = _przestawione(model.czastki, dzieci)

    return RoznicaStruktury(
        rodzic=nazwa_rodzica,
        nadmiarowe=nadmiarowe,
        brakujace=brakujace,
        przestawione=przestawione,
        pewnosc_kolejnosci=not model.ma_choice,
    )
