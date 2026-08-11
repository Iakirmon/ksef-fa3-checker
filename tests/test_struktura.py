"""Testy porownaj() — różnice struktury względem schematu FA(3)."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from lxml import etree

from fa3check.safexml import sparsuj
from fa3check.struktura import porownaj

ROOT = Path(__file__).resolve().parents[1]
ZLOTY = ROOT / "korpus" / "zloty"
NS = "http://crd.gov.pl/wzor/2025/06/25/13775/"
NSMAP = {"tns": NS}
TYPY_ZLOTY = ("Faktura", "Fa", "Podmiot2", "FaWiersz", "Platnosc")


def _naglowek_z_zlotego() -> etree._Element:
    dok = sparsuj((ZLOTY / "fa3-przyklad-01.xml").read_bytes())
    wezly = dok.korzen.xpath("//tns:Naglowek", namespaces=NSMAP)
    assert len(wezly) == 1
    return deepcopy(wezly[0])


def _fa_z_zlotego() -> etree._Element:
    dok = sparsuj((ZLOTY / "fa3-przyklad-01.xml").read_bytes())
    wezly = dok.korzen.xpath("//tns:Fa", namespaces=NSMAP)
    assert len(wezly) == 1
    return deepcopy(wezly[0])


def test_brak_wymaganego_elementu_naglowek() -> None:
    """TNaglowek: brak WariantFormularza (wymagany, minOccurs=1)."""
    naglowek = _naglowek_z_zlotego()
    for dziecko in list(naglowek):
        if etree.QName(dziecko).localname == "WariantFormularza":
            naglowek.remove(dziecko)
            break
    else:
        pytest.fail("brak WariantFormularza w złotym korpusie")

    roznica = porownaj(naglowek, "TNaglowek")

    assert roznica.rodzic == "Naglowek"
    assert roznica.brakujace == ("WariantFormularza",)
    assert roznica.nadmiarowe == ()
    assert roznica.przestawione == ()
    assert roznica.pewnosc_kolejnosci is True


def test_brak_wymaganego_elementu_fa() -> None:
    """Fa: brak P_2 (wymagany numer faktury)."""
    fa = _fa_z_zlotego()
    for dziecko in list(fa):
        if etree.QName(dziecko).localname == "P_2":
            fa.remove(dziecko)
            break
    else:
        pytest.fail("brak P_2 w złotym korpusie")

    roznica = porownaj(fa)

    assert roznica.brakujace == ("P_2",)
    assert roznica.nadmiarowe == ()
    assert roznica.przestawione == ()


def test_element_nadmiarowy() -> None:
    """TNaglowek: niezadeklarowane dziecko XtraPole."""
    naglowek = _naglowek_z_zlotego()
    etree.SubElement(naglowek, f"{{{NS}}}XtraPole").text = "x"

    roznica = porownaj(naglowek, "TNaglowek")

    assert roznica.nadmiarowe == ("XtraPole",)
    assert roznica.brakujace == ()
    assert roznica.przestawione == ()


def test_zla_kolejnosc() -> None:
    """TNaglowek: WariantFormularza przed KodFormularza."""
    naglowek = _naglowek_z_zlotego()
    dzieci = list(naglowek)
    naglowek.remove(dzieci[0])
    naglowek.insert(1, dzieci[0])

    roznica = porownaj(naglowek, "TNaglowek")

    assert roznica.przestawione == ("KodFormularza",)
    assert roznica.brakujace == ()
    assert roznica.nadmiarowe == ()


def test_kombinacja_brak_i_nadmiar() -> None:
    """TNaglowek: brak WariantFormularza i nadmiarowe XtraPole."""
    naglowek = _naglowek_z_zlotego()
    for dziecko in list(naglowek):
        if etree.QName(dziecko).localname == "WariantFormularza":
            naglowek.remove(dziecko)
            break
    etree.SubElement(naglowek, f"{{{NS}}}XtraPole").text = "x"

    roznica = porownaj(naglowek, "TNaglowek")

    assert roznica.brakujace == ("WariantFormularza",)
    assert roznica.nadmiarowe == ("XtraPole",)
    assert roznica.przestawione == ()


def test_fa_zla_kolejnosc_kod_waluty() -> None:
    """Fa: pierwsze dziecko przestawione — wykrywa KodWaluty (sonda z specu)."""
    fa = _fa_z_zlotego()
    dzieci = list(fa)
    fa.remove(dzieci[0])
    fa.insert(1, dzieci[0])

    roznica = porownaj(fa)

    assert roznica.przestawione == ("KodWaluty",)
    assert roznica.pewnosc_kolejnosci is False


@pytest.mark.parametrize("plik", sorted(ZLOTY.glob("fa3-przyklad-*.xml")), ids=lambda p: p.name)
def test_zloty_brakujace_puste(plik: Path) -> None:
    """Poprawne faktury MF nie mogą dawać fałszywych brakujących."""
    dok = sparsuj(plik.read_bytes())
    for typ in TYPY_ZLOTY:
        for wezel in dok.korzen.xpath(f"//tns:{typ}", namespaces=NSMAP):
            roznica = porownaj(wezel)
            assert roznica.brakujace == (), (
                f"{plik.name}/{typ}: fałszywie brakujące {roznica.brakujace}"
            )
            assert roznica.nadmiarowe == (), (
                f"{plik.name}/{typ}: nieznane dzieci {roznica.nadmiarowe}"
            )
            assert roznica.przestawione == (), (
                f"{plik.name}/{typ}: fałszywie przestawione {roznica.przestawione}"
            )
