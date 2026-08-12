"""XSD-kwota-zapis — wartość nie jest liczbą (spacja, przecinek)."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Formaty pól (danych) pliku faktury ustrukturyzowanej, pkt 5",
    strona=6,
    cytat=(
        "Pola kwotowe (numeryczne) służą do podania wartości liczbowej. "
        "Wartość należy wpisać "
        "ciągiem cyfr, nie można używać separatorów dla tysięcy (np. spacji). "
        "Jako separator miejsc "
        "dziesiętnych można używać wyłącznie kropki („ . ”)."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@tlumacz(
    id="XSD-kwota-zapis",
    klucze=(
        KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1", typ_xsd="TKwotowy"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1", typ_xsd="TKwotowy2"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1", typ_xsd="TIlosci"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TKwotowy"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TKwotowy2"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TIlosci"),
    ),
    zrodlo=ZRODLO,
)
class TlumaczenieZapisKwoty:
    def co(self, blad: BladSchematu) -> str:
        return (
            f"W polu {blad.element or 'kwotowym'} wartość „{blad.wartosc or '?'}” nie jest "
            "poprawną liczbą — najczęściej przez spację tysięcy albo przecinek zamiast kropki."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "KSeF odrzuci fakturę już na etapie sprawdzenia typu pola: ze spacją lub przecinkiem "
            "wartość nie jest liczbą w rozumieniu schematu."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        return (
            f"W polu {blad.element or 'kwotowym'} wpisz liczbę ciągiem cyfr, bez spacji, "
            "z kropką jako jedynym separatorem miejsc dziesiętnych (np. 1234.56)."
        )
