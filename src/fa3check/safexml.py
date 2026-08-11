"""Bezpieczne parsowanie niezaufanego XML — jedyne miejsce z lxml."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from lxml import etree

from fa3check.typy import LimitPrzekroczony, XmlNiebezpieczny, XmlNiepoprawny

LIMIT_BAJTOW = 3_145_728  # 3 MB
LIMIT_CZASU_S = 5.0

_BOM_UTF8 = b"\xef\xbb\xbf"
_DEKLARACJA_ENCODOWANIA = re.compile(
    rb"""<\?xml\s+[^>]*encoding\s*=\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class Dokument:
    """Sparsowany dokument z surowymi bajtami wejścia."""

    korzen: Any
    surowe: bytes

    @property
    def drzewo(self) -> Any:
        return self.korzen.getroottree()


def _parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        huge_tree=False,
        recover=False,
    )


def sparsuj(dane: bytes) -> Dokument:
    """Parsuj niezaufane bajty. Kolejność sprawdzeń ma znaczenie."""
    if len(dane) > LIMIT_BAJTOW:
        raise LimitPrzekroczony(f"Plik ma {len(dane)} B, limit wynosi {LIMIT_BAJTOW} B (3 MB).")

    if dane.startswith(_BOM_UTF8):
        raise XmlNiepoprawny("Plik zaczyna się od BOM UTF-8; wymagane jest UTF-8 bez BOM.")

    m = _DEKLARACJA_ENCODOWANIA.search(dane[:200])
    if m is not None:
        enc = m.group(1).decode("ascii", errors="replace").lower().replace("_", "-")
        if enc not in {"utf-8", "utf8"}:
            raise XmlNiepoprawny(
                f"Deklaracja kodowania '{enc}' — dopuszczalne jest wyłącznie UTF-8."
            )

    try:
        korzen = etree.fromstring(dane, parser=_parser())
    except etree.XMLSyntaxError as exc:
        raise XmlNiepoprawny(f"Niepoprawny XML: {exc}") from exc

    drzewo = korzen.getroottree()
    doctype = getattr(drzewo.docinfo, "doctype", None) or ""
    if doctype:
        raise XmlNiebezpieczny("Dokument zawiera DOCTYPE; faktura FA(3) nie może go mieć.")

    if drzewo.xpath("//processing-instruction()"):
        raise XmlNiepoprawny("Dokument zawiera instrukcje przetwarzania XML — są niedozwolone.")

    return Dokument(korzen=korzen, surowe=dane)
