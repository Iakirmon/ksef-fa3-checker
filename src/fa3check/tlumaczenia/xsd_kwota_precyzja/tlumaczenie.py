"""XSD-kwota-precyzja — za dużo miejsc dziesiętnych."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Formaty pól (danych) pliku faktury ustrukturyzowanej, pkt 6",
    strona=6,
    cytat=(
        "Kwoty podawane są co do zasady z dokładnością do 2 miejsc po kropce – o ile występują "
        "(np. 12345.56)."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)

_LIMITY = {"TKwotowy": 2, "TIlosci": 6, "TKwotowy2": 8}


@tlumacz(
    id="XSD-kwota-precyzja",
    klucze=(
        KluczBledu(typ_lxml="SCHEMAV_CVC_FRACTIONDIGITS_VALID", typ_xsd="TKwotowy"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_FRACTIONDIGITS_VALID", typ_xsd="TKwotowy2"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_FRACTIONDIGITS_VALID", typ_xsd="TIlosci"),
    ),
    zrodlo=ZRODLO,
)
class TlumaczeniePrecyzjaKwoty:
    def co(self, blad: BladSchematu) -> str:
        limit = _LIMITY.get(blad.typ_xsd or "", 2)
        wartosc = blad.wartosc or "?"
        pole = blad.element or "pole kwotowe"
        return (
            f"W polu {pole} wpisano {wartosc}, a dopuszczalne jest co najwyżej "
            f"{limit} miejsc po kropce (typ {blad.typ_xsd or 'kwotowy'})."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "KSeF odrzuci fakturę, bo pole ma zadeklarowaną precyzję w schemacie FA(3) "
            "i wartość wykracza poza ten limit."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        limit = _LIMITY.get(blad.typ_xsd or "", 2)
        return (
            f"Zaokrąglij wartość w polu {blad.element or 'kwotowym'} do {limit} miejsc "
            "po kropce i użyj kropki jako separatora dziesiętnego."
        )
