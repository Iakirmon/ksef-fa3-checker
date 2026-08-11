"""Niezmienniki architektury — analiza AST."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "fa3check"

ZAKAZANE_IMPORTY_WPISOW = frozenset({"web", "schema", "walidacja", "safexml"})


def _pliki_py(katalog: Path) -> list[Path]:
    if not katalog.is_dir():
        return []
    return sorted(p for p in katalog.rglob("*.py") if p.is_file())


def _moduly_importowane(drzewo: ast.AST) -> set[str]:
    wynik: set[str] = set()
    for node in ast.walk(drzewo):
        if isinstance(node, ast.Import):
            for alias in node.names:
                wynik.add(alias.name.split(".")[0])
                if alias.name.startswith("fa3check."):
                    wynik.add(alias.name.split(".")[1])
        elif isinstance(node, ast.ImportFrom) and node.module:
            czesci = node.module.split(".")
            wynik.add(czesci[0])
            if czesci[0] == "fa3check" and len(czesci) > 1:
                wynik.add(czesci[1])
            elif node.level and len(czesci) >= 1:
                wynik.add(czesci[0])
    return wynik


def test_lxml_parser_tylko_w_safexml() -> None:
    """Parsowanie niezaufanego XML wyłącznie w safexml; schema/struktura wolno importować lxml."""
    dozwolone_import = frozenset({"safexml.py", "schema.py", "struktura.py"})
    # schema/struktura ładują lokalny XSD przez etree.parse — to nie jest wejście użytkownika
    dozwolone_parse = frozenset({"safexml.py", "schema.py", "struktura.py"})
    zakazane_parsowanie = {"fromstring", "XMLParser"}
    naruszonia_import: list[str] = []
    naruszonia_parser: list[str] = []
    for plik in _pliki_py(SRC):
        tekst = plik.read_text(encoding="utf-8")
        drzewo = ast.parse(tekst, filename=str(plik))
        mods = _moduly_importowane(drzewo)
        if "lxml" in mods and plik.name not in dozwolone_import:
            naruszonia_import.append(str(plik.relative_to(ROOT)))
        if plik.name in dozwolone_parse:
            continue
        for node in ast.walk(drzewo):
            if isinstance(node, ast.Attribute) and node.attr in (*zakazane_parsowanie, "parse"):
                naruszonia_parser.append(f"{plik.relative_to(ROOT)}:{node.lineno}:{node.attr}")
    assert naruszonia_import == [], f"lxml poza dozwolonymi: {naruszonia_import}"
    assert naruszonia_parser == [], f"parsowanie poza safexml: {naruszonia_parser}"


def test_lxml_tylko_w_safexml() -> None:
    test_lxml_parser_tylko_w_safexml()


def test_wpisy_tlumaczen_bez_komunikatu() -> None:
    """Katalogi tlumaczenia/ nie odwołują się do .komunikat (tylko klucz)."""
    naruszonia: list[str] = []
    for plik in _pliki_py(SRC / "tlumaczenia"):
        if plik.name == "__init__.py":
            continue
        drzewo = ast.parse(plik.read_text(encoding="utf-8"), filename=str(plik))
        for node in ast.walk(drzewo):
            if isinstance(node, ast.Attribute) and node.attr == "komunikat":
                naruszonia.append(f"{plik.relative_to(ROOT)}:{node.lineno}")
    assert naruszonia == [], naruszonia


def test_wpisy_nie_importuja_warstwy_orkiestracji() -> None:
    naruszonia: list[str] = []
    for rodzaj in ("reguly", "tlumaczenia"):
        for plik in _pliki_py(SRC / rodzaj):
            drzewo = ast.parse(plik.read_text(encoding="utf-8"), filename=str(plik))
            mods = _moduly_importowane(drzewo)
            zle = mods & ZAKAZANE_IMPORTY_WPISOW
            if zle:
                naruszonia.append(f"{plik.relative_to(ROOT)}: {sorted(zle)}")
    assert naruszonia == [], naruszonia


def test_brak_float_w_adnotacjach_regul() -> None:
    naruszonia: list[str] = []
    for plik in _pliki_py(SRC / "reguly"):
        drzewo = ast.parse(plik.read_text(encoding="utf-8"), filename=str(plik))
        for node in ast.walk(drzewo):
            if isinstance(node, ast.Name) and node.id == "float":
                naruszonia.append(f"{plik}:{node.lineno}")
            if isinstance(node, ast.Attribute) and node.attr == "float":
                naruszonia.append(f"{plik}:{node.lineno}")
    assert naruszonia == [], naruszonia


def test_wpisy_bez_io_sieci_zegara() -> None:
    zakazane_wywolania = {"open", "urlopen", "urlretrieve"}
    zakazane_moduly = {"requests", "httpx", "datetime", "time", "random"}
    naruszonia: list[str] = []
    for rodzaj in ("reguly", "tlumaczenia"):
        for plik in _pliki_py(SRC / rodzaj):
            drzewo = ast.parse(plik.read_text(encoding="utf-8"), filename=str(plik))
            mods = _moduly_importowane(drzewo)
            zle_mod = mods & zakazane_moduly
            if zle_mod:
                naruszonia.append(f"{plik}: import {sorted(zle_mod)}")
            for node in ast.walk(drzewo):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Name) and node.func.id in zakazane_wywolania:
                    naruszonia.append(f"{plik}:{node.lineno} {node.func.id}()")
    assert naruszonia == [], naruszonia
