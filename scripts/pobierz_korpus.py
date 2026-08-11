#!/usr/bin/env python3
"""Pobiera korpus FA(3): schemat, 26 przykładów, broszurę, weryfikacja-faktury.md."""

from __future__ import annotations

import hashlib
import io
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
KORPUS = ROOT / "korpus"

URL_SCHEMA = (
    "https://raw.githubusercontent.com/CIRFMF/ksef-docs/main/"
    "faktury/schemy/FA/schemat_FA(3)_v1-0E.xsd"
)
URL_BAZOWE = {
    "ElementarneTypyDanych_v10-0E.xsd": (
        "https://raw.githubusercontent.com/CIRFMF/ksef-docs/main/"
        "faktury/schemy/FA/bazowe/ElementarneTypyDanych_v10-0E.xsd"
    ),
    "KodyKrajow_v10-0E.xsd": (
        "https://raw.githubusercontent.com/CIRFMF/ksef-docs/main/"
        "faktury/schemy/FA/bazowe/KodyKrajow_v10-0E.xsd"
    ),
    "StrukturyDanych_v10-0E.xsd": (
        "https://raw.githubusercontent.com/CIRFMF/ksef-docs/main/"
        "faktury/schemy/FA/bazowe/StrukturyDanych_v10-0E.xsd"
    ),
}
URL_PRZYKLADY = (
    "https://ksef.podatki.gov.pl/media/e5cia0ey/"
    "przykladowe-pliki-dla-struktury-logicznej-e-faktury-fa-3.zip"
)
URL_BROSZURA = (
    "https://ksef.podatki.gov.pl/media/jknpcymf/"
    "broszura-informacyjna-dotyczaca-struktury-logicznej-fa-3-04032026.pdf"
)
URL_WERYFIKACJA = (
    "https://raw.githubusercontent.com/CIRFMF/ksef-docs/main/faktury/weryfikacja-faktury.md"
)

# Oficjalny schemat wskazuje HTTP; lokalnie walidujemy względem wendorowanych bazowych.
SCHEMA_IMPORT_REWRITE = (
    'schemaLocation="http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/'
    'DefinicjeTypy/StrukturyDanych_v10-0E.xsd"',
    'schemaLocation="bazowe/StrukturyDanych_v10-0E.xsd"',
)

USER_AGENT = "fa3-check-korpus/0.1 (+https://github.com/Iakirmon/fa3-check)"


def pobierz(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=120) as resp:  # noqa: S310 — URL-e z docs/zrodla.md
        return resp.read()


def sha256(dane: bytes) -> str:
    return hashlib.sha256(dane).hexdigest()


def zapisz(sciezka: Path, dane: bytes) -> str:
    sciezka.parent.mkdir(parents=True, exist_ok=True)
    sciezka.write_bytes(dane)
    return sha256(dane)


def pobierz_schemat(wpisy: list[dict[str, str]]) -> None:
    schema_dir = KORPUS / "schema"
    bazowe = schema_dir / "bazowe"
    bazowe.mkdir(parents=True, exist_ok=True)

    surowy = pobierz(URL_SCHEMA)
    tekst = surowy.decode("utf-8")
    if SCHEMA_IMPORT_REWRITE[0] not in tekst:
        raise SystemExit(
            "Nie znaleziono oczekiwanego schemaLocation w schemacie FA(3) — "
            "sprawdź, czy wzór się nie zmienił."
        )
    lokalny = tekst.replace(*SCHEMA_IMPORT_REWRITE).encode("utf-8")
    digest = zapisz(schema_dir / "schemat_FA(3)_v1-0E.xsd", lokalny)
    wpisy.append(
        {
            "plik": "schema/schemat_FA(3)_v1-0E.xsd",
            "url": URL_SCHEMA,
            "pierwotna": "schemat_FA(3)_v1-0E.xsd",
            "sha256": digest,
            "uwagi": (
                "schemaLocation StrukturyDanych przepisany na "
                "bazowe/StrukturyDanych_v10-0E.xsd (offline)"
            ),
        }
    )

    for nazwa, url in URL_BAZOWE.items():
        dane = pobierz(url)
        digest = zapisz(bazowe / nazwa, dane)
        wpisy.append(
            {
                "plik": f"schema/bazowe/{nazwa}",
                "url": url,
                "pierwotna": nazwa,
                "sha256": digest,
                "uwagi": "",
            }
        )


def pobierz_przyklady(wpisy: list[dict[str, str]]) -> None:
    zloty = KORPUS / "zloty"
    zloty.mkdir(parents=True, exist_ok=True)
    for stary in zloty.glob("fa3-przyklad-*.xml"):
        stary.unlink()

    archiwum = pobierz(URL_PRZYKLADY)
    wpisy.append(
        {
            "plik": "(archiwum źródłowe, niecommitowane)",
            "url": URL_PRZYKLADY,
            "pierwotna": "przykladowe-pliki-dla-struktury-logicznej-e-faktury-fa-3.zip",
            "sha256": sha256(archiwum),
            "uwagi": "rozpakowane do zloty/fa3-przyklad-NN.xml",
        }
    )

    znalezione: dict[int, tuple[str, bytes]] = {}
    with zipfile.ZipFile(io.BytesIO(archiwum)) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".xml"):
                continue
            nazwa = Path(info.filename).name
            m = re.search(r"(\d+)\s*$", Path(nazwa).stem)
            if not m:
                continue
            nr = int(m.group(1))
            znalezione[nr] = (nazwa, zf.read(info))

    if set(znalezione) != set(range(1, 27)):
        raise SystemExit(f"Oczekiwano przykładów 1–26, znaleziono: {sorted(znalezione)}")

    for nr in range(1, 27):
        pierwotna, dane = znalezione[nr]
        docelowa = f"fa3-przyklad-{nr:02d}.xml"
        digest = zapisz(zloty / docelowa, dane)
        wpisy.append(
            {
                "plik": f"zloty/{docelowa}",
                "url": URL_PRZYKLADY,
                "pierwotna": pierwotna,
                "sha256": digest,
                "uwagi": "",
            }
        )


def pobierz_broszure(wpisy: list[dict[str, str]]) -> None:
    broszura_dir = KORPUS / "broszura"
    broszura_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = broszura_dir / "broszura-fa3.pdf"
    txt_path = broszura_dir / "broszura-fa3.txt"

    pdf = pobierz(URL_BROSZURA)
    pdf_digest = zapisz(pdf_path, pdf)
    if shutil.which("pdftotext") is None:
        raise SystemExit("Brak pdftotext (poppler). Zainstaluj i uruchom ponownie.")

    cmd = [
        "pdftotext",
        "-layout",
        "-enc",
        "UTF-8",
        str(pdf_path),
        str(txt_path),
    ]
    subprocess.run(cmd, check=True)

    surowy = txt_path.read_text(encoding="utf-8")
    strony = surowy.split("\f")
    linie: list[str] = []
    for i, strona in enumerate(strony, start=1):
        if i > 1 or strona.strip():
            linie.append(f"=== strona {i} ===")
            # Usuń wiodące/końcowe puste linie strony, zachowaj treść
            linie.append(strona.rstrip("\n"))
            if not strona.endswith("\n"):
                linie.append("")
    # Ostatnia pusta strona po końcowym \f — usuń pusty znacznik na końcu
    while linie and linie[-1] == "":
        linie.pop()
    # Jeśli ostatni znacznik bez treści (pusta strona końcowa)
    if (
        linie
        and linie[-1].startswith("=== strona ")
        and (len(linie) == 1 or linie[-2].startswith("=== strona "))
    ):
        linie.pop()

    tekst = "\n".join(linie)
    if not tekst.endswith("\n"):
        tekst += "\n"
    txt_path.write_text(tekst, encoding="utf-8")
    txt_digest = sha256(tekst.encode("utf-8"))

    wpisy.append(
        {
            "plik": "broszura/broszura-fa3.pdf",
            "url": URL_BROSZURA,
            "pierwotna": "broszura-informacyjna-dotyczaca-struktury-logicznej-fa-3-04032026.pdf",
            "sha256": pdf_digest,
            "uwagi": "PDF niecommitowany; tylko w PROVENANCE",
        }
    )
    wpisy.append(
        {
            "plik": "broszura/broszura-fa3.txt",
            "url": URL_BROSZURA,
            "pierwotna": "(wyciąg z PDF)",
            "sha256": txt_digest,
            "uwagi": (
                "pdftotext -layout -enc UTF-8 broszura-fa3.pdf broszura-fa3.txt; "
                "znak wysuwu strony (\\f) zamieniony na === strona N ==="
            ),
        }
    )


def pobierz_weryfikacje(wpisy: list[dict[str, str]]) -> None:
    zrodla = KORPUS / "zrodla"
    zrodla.mkdir(parents=True, exist_ok=True)
    dane = pobierz(URL_WERYFIKACJA)
    digest = zapisz(zrodla / "weryfikacja-faktury.md", dane)
    wpisy.append(
        {
            "plik": "zrodla/weryfikacja-faktury.md",
            "url": URL_WERYFIKACJA,
            "pierwotna": "faktury/weryfikacja-faktury.md",
            "sha256": digest,
            "uwagi": "CIRFMF/ksef-docs, MIT",
        }
    )


def napisz_provenance(wpisy: list[dict[str, str]]) -> None:
    dzisiaj = date.today().isoformat()
    linie = [
        "# PROVENANCE",
        "",
        f"Data pobrania: {dzisiaj}",
        "",
        "Źródła URL-i: `docs/zrodla.md`.",
        "",
        "| Plik | Nazwa pierwotna | SHA-256 | URL | Uwagi |",
        "|---|---|---|---|---|",
    ]
    for w in wpisy:
        linie.append(
            f"| `{w['plik']}` | `{w['pierwotna']}` | `{w['sha256']}` | {w['url']} | {w['uwagi']} |"
        )
    linie.append("")
    linie.append("## Konwersja broszury")
    linie.append("")
    linie.append("```")
    linie.append("pdftotext -layout -enc UTF-8 korpus/broszura/broszura-fa3.pdf \\")
    linie.append("  korpus/broszura/broszura-fa3.txt")
    linie.append("# potem znak wysuwu strony (\\f) → wiersz === strona N === (od 1)")
    linie.append("```")
    linie.append("")
    (KORPUS / "PROVENANCE.md").write_text("\n".join(linie), encoding="utf-8")


def main() -> None:
    KORPUS.mkdir(parents=True, exist_ok=True)
    wpisy: list[dict[str, str]] = []
    print("Schemat…", flush=True)
    pobierz_schemat(wpisy)
    print("Przykłady…", flush=True)
    pobierz_przyklady(wpisy)
    print("Broszura…", flush=True)
    pobierz_broszure(wpisy)
    print("Weryfikacja faktury…", flush=True)
    pobierz_weryfikacje(wpisy)
    napisz_provenance(wpisy)
    print("Gotowe.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — skrypt CLI
        print(f"Błąd: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
