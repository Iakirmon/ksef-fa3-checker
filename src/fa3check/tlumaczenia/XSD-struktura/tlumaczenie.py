"""XSD-struktura — brak, nadmiar lub zła kolejność elementów."""

from fa3check.rejestr import tlumacz
from fa3check.struktura import RoznicaStruktury
from fa3check.typy import BladSchematu, KluczBledu, Zrodlo

ZRODLO = Zrodlo(
    dokument="Broszura informacyjna dotycząca struktury logicznej FA(3)",
    wersja="2026-03-04",
    sekcja="Formaty pól (danych) — charakter obligatoryjny pól",
    strona=4,
    cytat=(
        "obligatoryjny - zapisów dokonuje się obowiązkowo (np. NIP w elemencie "
        "Podmiot1/DaneIdentyfikacyjne); obligatoryjny charakter danego pola wynika w "
        "szczególności z treści obowiązujących przepisów ustawy i jest warunkowany strukturą "
        "logiczną wzoru,"
    ),
    url="https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/",
)


@tlumacz(
    id="XSD-struktura",
    klucz=KluczBledu(typ_lxml="SCHEMAV_ELEMENT_CONTENT"),
    zrodlo=ZRODLO,
)
class TlumaczenieStruktura:
    def __init__(self) -> None:
        self._roznica: RoznicaStruktury | None = None

    def ustaw_roznice(self, roznica: RoznicaStruktury) -> None:
        self._roznica = roznica

    def co(self, blad: BladSchematu) -> str:
        r = self._roznica
        if r is not None:
            czesci: list[str] = []
            if r.brakujace:
                czesci.append("brakuje pól: " + ", ".join(r.brakujace))
            if r.nadmiarowe:
                czesci.append("nadmiarowe pola: " + ", ".join(r.nadmiarowe))
            if r.przestawione:
                czesci.append("zaburzona kolejność przy: " + ", ".join(r.przestawione))
            if czesci:
                return (
                    f"W elemencie {r.rodzic} struktura jest niepoprawna — "
                    + "; ".join(czesci)
                    + "."
                )
        pole = blad.element or "sąsiednie pole"
        return (
            f"Struktura wokół pola {pole} (linia {blad.linia}) jest niezgodna ze wzorem FA(3) "
            "— brak wymaganego elementu, element nadmiarowy albo zła kolejność."
        )

    def dlaczego(self, blad: BladSchematu) -> str:
        return (
            "KSeF odrzuci fakturę, bo kolejność i kompletność elementów muszą odpowiadać "
            "strukturze logicznej wzoru FA(3)."
        )

    def jak_naprawic(self, blad: BladSchematu) -> str:
        r = self._roznica
        if r and r.brakujace:
            return (
                f"Dodaj brakujące obligatoryjne pola w elemencie {r.rodzic}: "
                + ", ".join(r.brakujace)
                + "."
            )
        if r and r.przestawione:
            return (
                f"Uporządkuj dzieci elementu {r.rodzic} zgodnie z kolejnością ze schematu FA(3)."
            )
        if r and r.nadmiarowe:
            return (
                f"Usuń nieznane elementy z {r.rodzic}: " + ", ".join(r.nadmiarowe) + "."
            )
        return (
            "Porównaj fragment XML ze schematem FA(3) i broszurą — uzupełnij brakujące "
            "pola obligatoryjne i przywróć kolejność elementów."
        )
