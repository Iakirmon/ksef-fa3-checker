"""XSD-korzen — dokument nie jest fakturą FA(3) / zła przestrzeń nazw."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Wzór faktury ustrukturyzowanej",
    strona=3,
    cytat=(
        "Struktury logiczna FA(3) w wersji produkcyjnej jest dostępna pod adresem: "
        "https://crd.gov.pl/wzor/2025/06/25/13775/."
    ),
    url="https://crd.gov.pl/wzor/2025/06/25/13775/",
)


@tlumacz(
    id="XSD-korzen",
    klucz=KluczBledu(typ_lxml="SCHEMAV_CVC_ELT_1"),
    zrodlo=ZRODLO,
)
class TlumaczenieKorzen:
    def co(self, blad: BladSchematu) -> str:
        return (
            f"Element {blad.element or 'korzeniowy'} nie pasuje do globalnej deklaracji wzoru "
            "FA(3) — najczęściej zgubiony lub zły atrybut xmlns albo dokument nie jest fakturą."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "Bez poprawnej przestrzeni nazw i korzenia Faktura dokument nie jest rozpoznawany "
            "jako faktura ustrukturyzowana FA(3)."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        return (
            "Upewnij się, że korzeń to Faktura oraz "
            'xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/".'
        )
