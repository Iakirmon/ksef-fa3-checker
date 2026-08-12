"""XSD-data-zakres — data poza dopuszczalnym zakresem typu."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Formaty pól (danych) pliku faktury ustrukturyzowanej, pkt 8",
    strona=6,
    cytat="Daty podawane są w formacie RRRR-MM-DD (np. 2026-02-01).",
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@tlumacz(
    id="XSD-data-zakres",
    klucze=(
        KluczBledu(typ_lxml="SCHEMAV_CVC_MININCLUSIVE_VALID"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_MAXINCLUSIVE_VALID"),
    ),
    zrodlo=ZRODLO,
)
class TlumaczenieZakresDaty:
    def co(self, blad: BladSchematu) -> str:
        return (
            f"W polu {blad.element or 'daty'} wpisano {blad.wartosc or '?'}. "
            "Dla typu TDataT dopuszczalny zakres to 2006-01-01 do 2050-01-01."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "KSeF odrzuci fakturę, bo data wykracza poza zakres zadeklarowany w schemacie FA(3) "
            "dla tego pola."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        return (
            f"W polu {blad.element or 'daty'} podaj datę w formacie RRRR-MM-DD z zakresu "
            "2006-01-01 … 2050-01-01."
        )
