"""XSD-dlugosc — pole za długie albo puste."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Formaty pól (danych) pliku faktury ustrukturyzowanej, pkt 3",
    strona=5,
    cytat=(
        "Pola znakowe są polami alfanumerycznymi. Dopuszczalne jest stosowanie małych i dużych "
        "liter oraz cyfr. Maksymalna ilość znaków wynosi co do zasady 256."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)

_LIMITY = {"TZnakowy512": 512, "TZnakowy": 256}


@tlumacz(
    id="XSD-dlugosc",
    klucze=(
        KluczBledu(typ_lxml="SCHEMAV_CVC_MAXLENGTH_VALID"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_MINLENGTH_VALID"),
    ),
    zrodlo=ZRODLO,
)
class TlumaczenieDlugosc:
    def co(self, blad: BladSchematu) -> str:
        limit = _LIMITY.get(blad.typ_xsd or "", 256)
        dl = len(blad.wartosc or "")
        return (
            f"Pole {blad.element or 'znakowe'} ma {dl} znaków, a limit dla typu "
            f"{blad.typ_xsd or 'znakowego'} wynosi {limit}."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "KSeF odrzuci fakturę, bo długość pola wykracza poza limit ze schematu FA(3)."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        limit = _LIMITY.get(blad.typ_xsd or "", 256)
        return (
            f"Skróć treść w polu {blad.element or 'znakowym'} do co najwyżej {limit} znaków "
            "albo przenieś nadmiar do pola o większym limicie, jeśli struktura na to pozwala."
        )
