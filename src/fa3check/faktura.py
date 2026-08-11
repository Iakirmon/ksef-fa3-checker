"""Cienka fasada nad dokumentem FA(3)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from fa3check.safexml import Dokument

NS = {"tns": "http://crd.gov.pl/wzor/2025/06/25/13775/"}


class Faktura:
    """Fasada XPath / Decimal nad sparsowaną fakturą."""

    def __init__(self, korzen: Any, surowe: bytes) -> None:
        self._korzen = korzen
        self._surowe = surowe

    @classmethod
    def z_dokumentu(cls, dok: Dokument) -> Faktura:
        return cls(korzen=dok.korzen, surowe=dok.surowe)

    def xp(self, wyrazenie: str) -> list[Any]:
        wynik = self._korzen.xpath(wyrazenie, namespaces=NS)
        if isinstance(wynik, list):
            return wynik
        return [wynik]

    def tekst(self, wyrazenie: str) -> str | None:
        wezly = self.xp(wyrazenie)
        if not wezly:
            return None
        wezel = wezly[0]
        if isinstance(wezel, str):
            tekst = wezel.strip()
            return tekst or None
        tekst = (wezel.text or "").strip()
        return tekst or None

    def dec(self, wyrazenie: str) -> Decimal | None:
        tekst = self.tekst(wyrazenie)
        if tekst is None:
            return None
        try:
            return Decimal(tekst)
        except InvalidOperation:
            return None

    def linia(self, wezel: Any) -> int | None:
        linia = getattr(wezel, "sourceline", None)
        return int(linia) if linia is not None else None

    def obecny(self, wyrazenie: str) -> bool:
        return bool(self.xp(wyrazenie))

    def surowe_bajty(self) -> bytes:
        return self._surowe
