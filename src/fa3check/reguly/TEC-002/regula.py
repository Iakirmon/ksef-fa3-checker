"""TEC-002 — brak instrukcji przetwarzania XML."""

from __future__ import annotations

from collections.abc import Iterator

from fa3check.faktura import Faktura
from fa3check.rejestr import rejestruj
from fa3check.typy import Poziom, Waga, Zastrzezenie, Zrodlo

ZRODLO = Zrodlo(
    dokument="Weryfikacja faktury (CIRFMF/ksef-docs)",
    wersja="2026-04-09",
    sekcja="Weryfikacja XML — processing instructions",
    cytat="nie może zawierać instrukcji przetwarzania XML (processing instructions),",
    url="https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md",
)


@rejestruj(
    id="TEC-002",
    tytul="Brak instrukcji przetwarzania XML",
    poziom=Poziom.TECHNICZNA,
    waga=Waga.BLAD,
    zrodlo=ZRODLO,
    dotyczy="/*",
)
def brak_instrukcji_przetwarzania(f: Faktura) -> Iterator[Zastrzezenie]:
    dane = f.surowe_bajty()
    if dane.startswith(b"\xef\xbb\xbf"):
        dane = dane[3:]
    tekst = dane.decode("utf-8", errors="replace").lstrip()
    reszta = tekst
    if reszta.startswith("<?xml"):
        koniec = reszta.find("?>")
        if koniec != -1:
            reszta = reszta[koniec + 2 :]
    if "<?" in reszta:
        yield Zastrzezenie(
            wpis="TEC-002",
            waga=Waga.BLAD,
            poziom=Poziom.TECHNICZNA,
            xpath="/*",
            linia=1,
            co=(
                "Dokument zawiera instrukcję przetwarzania XML "
                "(fragment „<?…?>” poza prologiem) — niedozwolona w FA(3)."
            ),
            dlaczego=(
                "KSeF odrzuci fakturę — processing instructions są niedozwolone "
                "w fakturze FA(3)."
            ),
            jak_naprawic=(
                "Usuń wszystkie instrukcje przetwarzania (np. xml-stylesheet) z pliku."
            ),
            zrodlo=ZRODLO,
        )
