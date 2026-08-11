"""Dowód sensu TEC-005: XSD przepuszcza NIP z błędną sumą, reguła nie."""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from tests.helpers import faktura_z_fixture

from fa3check.rejestr import odkryj, pobierz, reset_do_testow


def _suma_kontrolna_ok(nip: str) -> bool:
    wagi = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    if len(nip) != 10 or not nip.isdigit():
        return False
    suma = sum(int(nip[i]) * wagi[i] for i in range(9))
    reszta = suma % 11
    if reszta == 10:
        return False
    return reszta == int(nip[9])


def test_tec005_xsd_przepuszcza_zla_suma() -> None:
    reset_do_testow()
    odkryj()
    regula = pobierz("TEC-005")
    lamie = Path(regula.katalog / "fixtures" / "lamie.xml")  # type: ignore[union-attr]
    schema = etree.XMLSchema(etree.parse("korpus/schema/schemat_FA(3)_v1-0E.xsd"))
    drzewo = etree.parse(str(lamie))
    assert schema.validate(drzewo), f"XSD odrzucił: {schema.error_log}"

    f = faktura_z_fixture(lamie)
    zas = list(regula.funkcja(f))  # type: ignore[union-attr]
    assert any(z.wpis == "TEC-005" for z in zas)
    ns = {"tns": "http://crd.gov.pl/wzor/2025/06/25/13775/"}
    nip = drzewo.xpath("//tns:Podmiot1//tns:NIP", namespaces=ns)[0].text
    assert nip and not _suma_kontrolna_ok(nip)
    print(f"TEC-005 dowód: NIP {nip} — XSD OK, suma kontrolna FAIL, reguła odpala")
