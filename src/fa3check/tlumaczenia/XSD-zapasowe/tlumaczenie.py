"""XSD-zapasowe — tłumaczenie awaryjne, gdy nic precyzyjniejszego nie pasuje."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Wzór faktury ustrukturyzowanej",
    strona=3,
    cytat=(
        "Od 1 lutego 2026 r. obowiązującym wzorem faktury ustrukturyzowanej "
        "jest struktura logiczna FA(3)."
    ),
    url="https://crd.gov.pl/wzor/2025/06/25/13775/",
)


@tlumacz(id="XSD-zapasowe", zrodlo=ZRODLO)
class TlumaczenieZapasowe:
    def co(self, blad: BladSchematu) -> str:
        return (
            f"Pole {blad.element or 'w dokumencie'} w linii {blad.linia} nie spełnia "
            "wymogów struktury FA(3)."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "Naruszenie schematu FA(3) oznacza, że KSeF odrzuci plik na etapie "
            "sprawdzenia zgodności ze wzorem."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        return (
            f"Sprawdź pole {blad.element or 'wskazane w linii ' + str(blad.linia)} "
            "w broszurze FA(3) i popraw wartość albo strukturę."
        )
