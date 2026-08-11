#!/usr/bin/env python3
"""Tabela pokrycia rejestrów — generowana, nie wpisywana z ręki."""

from __future__ import annotations

from collections import Counter

from fa3check.rejestr import odkryj, reguly, reset_do_testow, tlumaczenia


def main() -> None:
    reset_do_testow()
    odkryj()
    r = reguly()
    t = tlumaczenia()
    po_poziomach = Counter(x.poziom.value for x in r)
    z_strona = sum(1 for x in r if x.zrodlo.strona is not None)
    # Offline: wszystko poza TEC-006/007 (wymagają stanu KSeF) — heurystyka dokumentacyjna
    online = {"TEC-006", "TEC-007"}
    offline = sum(1 for x in r if x.id not in online)

    print("## Pokrycie rejestrów\n")
    print("| Rejestr | Liczba |")
    print("|---|---|")
    print(f"| Reguły łącznie | {len(r)} |")
    for poz, n in sorted(po_poziomach.items()):
        print(f"| — poziom `{poz}` | {n} |")
    print(f"| Tłumaczenia schematu | {len(t)} |")
    print(f"| Reguły z numerem strony broszury | {z_strona} |")
    print(f"| Reguły rozstrzygalne offline (szacunek) | {offline} |")
    print()
    print("Identyfikatory reguł:", ", ".join(x.id for x in r))
    print("Identyfikatory tłumaczeń:", ", ".join(x.id for x in t))


if __name__ == "__main__":
    main()
