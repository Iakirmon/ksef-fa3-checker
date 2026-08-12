"""Defekt D — zmiana nazw katalogów wpisów na poprawne nazwy modułów Pythona.

Katalogi `SEM-001` i `XSD-kwota-precyzja` nie są poprawnymi nazwami modułów, więc wypadały
ze `mypy --strict` (14 sprawdzanych plików zamiast 35). Identyfikator wyświetlany pozostaje
w polu `id` dekoratora i nie zmienia się.

Sprawdzone na klonie repozytorium: 137 testów zielonych, `mypy --strict src/` obejmuje 35 plików
i przechodzi bez zastrzeżeń, zero zmian w kodzie poza nazwami katalogów i konfiguracją.

Uruchomienie z katalogu głównego repozytorium:

    python scripts/zmien_nazwy_wpisow.py --na-probe     # tylko pokaż, co zrobi
    python scripts/zmien_nazwy_wpisow.py                # wykonaj przez `git mv`

Po wykonaniu:
  1. usuń blok `exclude` z `[tool.mypy]` w `pyproject.toml`,
  2. usuń `--exclude '(^src/fa3check/(tlumaczenia|reguly)/.+)'` z kroku Mypy w ci.yml,
  3. `mypy --strict src/` musi pokazać 35 plików i zero błędów,
  4. `pytest -q` musi dać 137 zielonych.

Jeśli skrypt przerwie z komunikatem o istniejącym katalogu docelowym: prawdopodobnie została
resztka po wcześniejszej próbie. `git clean -fd` jej nie usuwa, bo katalog zawiera ignorowany
`__pycache__`. Sprzątnij i powtórz:

    find src -name __pycache__ -type d -exec rm -rf {} +
    find src -type d -empty -delete
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BAZA = Path("src/fa3check")
RODZAJE = ("reguly", "tlumaczenia")


def nowa_nazwa(stara: str) -> str:
    """`SEM-001` → `sem_001`, `XSD-kwota-precyzja` → `xsd_kwota_precyzja`."""
    return stara.lower().replace("-", "_").replace(".", "_")


def zbierz() -> list[tuple[Path, Path]]:
    if not BAZA.is_dir():
        sys.exit(f"Nie widzę {BAZA} — uruchom z katalogu głównego repozytorium.")
    pary: list[tuple[Path, Path]] = []
    for rodzaj in RODZAJE:
        katalog_rodzaju = BAZA / rodzaj
        if not katalog_rodzaju.is_dir():
            continue
        for katalog in sorted(katalog_rodzaju.iterdir()):
            if not katalog.is_dir() or katalog.name.startswith(("_", ".")):
                continue
            nowa = nowa_nazwa(katalog.name)
            if nowa != katalog.name:
                pary.append((katalog, katalog.parent / nowa))
    return pary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--na-probe", action="store_true", help="pokaż zmiany bez wykonania")
    args = p.parse_args()

    pary = zbierz()
    if not pary:
        print("Nic do zmiany — wszystkie katalogi mają już poprawne nazwy.")
        return 0

    for stara, nowa in pary:
        print(f"  {stara.name}  ->  {nowa.name}")
    print(f"\nrazem: {len(pary)} katalogów")

    if args.na_probe:
        print("\nPróba — nic nie zmieniono. Uruchom bez --na-probe, żeby wykonać.")
        return 0

    kolizje = [n for _, n in pary if n.exists()]
    if kolizje:
        sys.exit(f"Przerywam — katalog docelowy już istnieje: {kolizje}")

    for stara, nowa in pary:
        subprocess.run(["git", "mv", str(stara), str(nowa)], check=True)

    print("\nGotowe. Teraz:")
    print("  1. usuń blok exclude z [tool.mypy] w pyproject.toml")
    print("  2. usuń --exclude z kroku Mypy w .github/workflows/ci.yml")
    print("  3. mypy --strict src/     (oczekiwane: 35 plików, zero błędów)")
    print("  4. pytest -q              (oczekiwane: 137 zielonych)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
