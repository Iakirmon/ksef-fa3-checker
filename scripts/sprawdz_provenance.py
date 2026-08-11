#!/usr/bin/env python3
"""Sprawdza, że pliki w korpus/ mają SHA-256 zgodne z PROVENANCE.md."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KORPUS = ROOT / "korpus"
PROVENANCE = KORPUS / "PROVENANCE.md"


def commitowany(rel: str) -> bool:
    if rel.endswith(".pdf") or "archiwum" in rel:
        return False
    return (
        rel.startswith("schema/")
        or rel.startswith("zloty/fa3-przyklad-")
        or rel == "broszura/broszura-fa3.txt"
        or rel == "zrodla/weryfikacja-faktury.md"
    )


def main() -> None:
    if not PROVENANCE.is_file():
        raise SystemExit("Brak korpus/PROVENANCE.md")

    tekst = PROVENANCE.read_text(encoding="utf-8")
    wiersze = [w for w in tekst.splitlines() if w.startswith("| `")]
    bledy: list[str] = []
    sprawdzone = 0

    for wiersz in wiersze:
        m = re.match(
            r"\| `([^`]+)` \| `([^`]*)` \| `([0-9a-f]{64})` \|",
            wiersz,
        )
        if not m:
            continue
        rel, _pierwotna, oczekiwany = m.groups()
        if not commitowany(rel):
            continue

        sciezka = KORPUS / rel
        if not sciezka.is_file():
            bledy.append(f"brak pliku: {rel}")
            continue
        aktualny = hashlib.sha256(sciezka.read_bytes()).hexdigest()
        if aktualny != oczekiwany:
            bledy.append(f"SHA niezgodne: {rel}\n  oczekiwano {oczekiwany}\n  jest      {aktualny}")
        else:
            sprawdzone += 1

    if "broszura/broszura-fa3.pdf" not in tekst:
        bledy.append("PROVENANCE nie zawiera wpisu PDF broszury")
    elif not re.search(
        r"`broszura/broszura-fa3\.pdf` \| `[^`]*` \| `([0-9a-f]{64})`",
        tekst,
    ):
        bledy.append("PROVENANCE: nieparsowalny SHA PDF")

    if sprawdzone < 30:
        bledy.append(f"za mało sprawdzonych plików: {sprawdzone} (oczekiwano ≥ 30)")

    if bledy:
        print("\n".join(bledy), file=sys.stderr)
        raise SystemExit(1)

    print(f"PROVENANCE OK ({sprawdzone} plików)")


if __name__ == "__main__":
    main()
