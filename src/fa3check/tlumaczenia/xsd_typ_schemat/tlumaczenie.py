"""XSD-typ-schemat — wartość nie spełnia ograniczenia typu ze schematu."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="schemat_FA(3)_v1-0E.xsd",
    wersja="2026-06-25",
    sekcja="deklaracja schematu",
    cytat='targetNamespace="http://crd.gov.pl/wzor/2025/06/25/13775/"',
    url="https://crd.gov.pl/wzor/2025/06/25/13775/",
)


@tlumacz(
    id="XSD-typ-schemat",
    klucze=(
        KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID"),
    ),
    zrodlo=ZRODLO,
)
class TlumaczenieTypSchemat:
    def co(self, blad: BladSchematu) -> str:
        pole = blad.element or "wskazane"
        wartosc = blad.wartosc or "?"
        typ = blad.typ_xsd or "zadeklarowanym"
        return (
            f"W polu {pole} wartość „{wartosc}” nie spełnia ograniczenia typu {typ} "
            "zadeklarowanego w schemacie FA(3)."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        typ = blad.typ_xsd or "tego pola"
        return (
            f"KSeF odrzuci fakturę, bo wartość nie mieści się w ograniczeniu typu {typ} "
            "ze schematu FA(3)."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        pole = blad.element or "wskazanym"
        typ = blad.typ_xsd or "wymaganym"
        return (
            f"Popraw wartość w polu {pole}, tak aby spełniała ograniczenie typu {typ} "
            "ze schematu FA(3)."
        )
