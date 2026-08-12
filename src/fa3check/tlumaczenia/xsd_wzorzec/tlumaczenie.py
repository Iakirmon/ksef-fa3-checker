"""XSD-wzorzec — wartość nie pasuje do wzorca (np. NIP z myślnikami)."""

from fa3check.rejestr import tlumacz
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Formaty pól (danych) pliku faktury ustrukturyzowanej, pkt 10",
    strona=6,
    cytat=(
        "Numery identyfikacji podatkowej ujęte w strukturze faktury ustrukturyzowanej należy "
        "zapisywać jako ciąg kolejno po sobie następujących cyfr lub liter, bez spacji i innych "
        "znaków rozdzielających oraz poprzez wyodrębnienie literowego kodu kraju do osobnego pola "
        "przeznaczonego na ten kod."
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@tlumacz(
    id="XSD-wzorzec",
    klucze=(
        KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TNrNIP"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TNIPIdWew"),
        KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TNrVatUE"),
    ),
    zrodlo=ZRODLO,
)
class TlumaczenieWzorzec:
    def co(self, blad: BladSchematu) -> str:
        if blad.typ_xsd == "TNrNIP" or blad.element == "NIP":
            return (
                f"W polu NIP wpisano „{blad.wartosc or '?'}” — wygląda na numer z myślnikami "
                "lub spacjami, a wymagany jest ciąg 10 cyfr bez znaków rozdzielających."
            )
        return (
            f"W polu {blad.element or 'identyfikatora podatkowego'} wartość "
            f"„{blad.wartosc or '?'}” nie jest poprawnym numerem identyfikacji podatkowej "
            "— wymagany jest ciąg cyfr lub liter bez spacji i znaków rozdzielających."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "KSeF odrzuci fakturę, bo schemat wymusza dokładny format identyfikatora "
            "bez separatorów."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        if blad.typ_xsd == "TNrNIP" or blad.element == "NIP":
            return (
                "Usuń myślniki i spacje z numeru NIP, zostaw sam ciąg cyfr "
                "(np. 5261040828) i kod kraju przenieś do osobnego pola, jeśli dotyczy."
            )
        return (
            f"W polu {blad.element or 'identyfikatora podatkowego'} zostaw ciąg cyfr lub liter "
            "bez spacji i znaków rozdzielających; kod kraju przenieś do osobnego pola."
        )
