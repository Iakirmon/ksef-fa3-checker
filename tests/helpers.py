"""Wspólne helpery testowe."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from fa3check.faktura import Faktura
from fa3check.safexml import sparsuj
from fa3check.typy import Fa3Error


def faktura_z_fixture(sciezka: Path) -> Faktura:
    """Wczytaj fixture. Dla TEC (BOM/PI/rozmiar) omija bramki safexml, zachowując surowe bajty."""
    dane = sciezka.read_bytes()
    try:
        return Faktura.z_dokumentu(sparsuj(dane))
    except Fa3Error:
        do_parsowania = dane
        if do_parsowania.startswith(b"\xef\xbb\xbf"):
            do_parsowania = do_parsowania[3:]
        # Usuń DOCTYPE na potrzeby testów TEC (safexml i tak go odrzuca w produkcji)
        if b"<!DOCTYPE" in do_parsowania[:200]:
            import re

            do_parsowania = re.sub(
                rb"<!DOCTYPE[^>]*>\s*",
                b"",
                do_parsowania,
                count=1,
            )
        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            load_dtd=False,
            dtd_validation=False,
            huge_tree=False,
            recover=False,
            remove_pis=False,
        )
        korzen = etree.fromstring(do_parsowania, parser=parser)
        return Faktura(korzen=korzen, surowe=dane)
