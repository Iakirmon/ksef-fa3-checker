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
    klucz=KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID"),
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
            f"Wartość „{blad.wartosc or '?'}” w polu {blad.element or '?'} nie pasuje do "
            "wymaganego wzorca zapisu."
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
            f"Popraw zapis w polu {blad.element or 'wskazanym'} zgodnie z broszurą FA(3) "
            "— bez spacji i zbędnych znaków rozdzielających."
        )
