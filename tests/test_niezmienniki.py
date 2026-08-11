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


def test_lxml_tylko_w_safexml() -> None:
    naruszonia: list[str] = []
    for plik in _pliki_py(SRC):
        drzewo = ast.parse(plik.read_text(encoding="utf-8"), filename=str(plik))
        mods = _moduly_importowane(drzewo)
        if "lxml" in mods and plik.name != "safexml.py":
            naruszonia.append(str(plik.relative_to(ROOT)))
    assert naruszonia == [], f"lxml poza safexml.py: {naruszonia}"


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
