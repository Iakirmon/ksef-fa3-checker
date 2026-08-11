"""Testy warstwy webowej — limity, prywatność logów, XSS, determinizm."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fa3check.safexml import LIMIT_BAJTOW
from fa3check.web import app as webmod

ROOT = Path(__file__).resolve().parents[1]
ZLOTY = ROOT / "korpus" / "zloty"

NIP_MARKER = "5250000000"
NUMER_MARKER = "FAKTURA-PRIVACY-TEST-999"


@pytest.fixture()
def client() -> TestClient:
    webmod._historia.clear()
    return TestClient(webmod.app)


def _bez_czasu(html: str) -> str:
    return re.sub(r"Czas: \d+ ms", "Czas: X ms", html)


def test_zdrowie(client: TestClient) -> None:
    r = client.get("/zdrowie")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_strona_glowna(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "fa3-check" in r.text
    assert "pamięci" in r.text


def test_nadmiar_odrzucany_przed_parsowaniem(client: TestClient) -> None:
    """Content-Length ponad limit → 413 bez wywołania walidacji."""
    r = client.post(
        "/waliduj",
        content=b"xml=" + b"x" * 10,
        headers={
            "content-type": "application/x-www-form-urlencoded",
            "content-length": str(LIMIT_BAJTOW + 100),
        },
    )
    assert r.status_code == 413
    assert "limit" in r.text.lower()


def test_logi_bez_tresci_faktury(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """Udowodnione jako czerwone przy tymczasowym logger.exception(surowy wyjątek)."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
  <Naglowek><NIP>{NIP_MARKER}</NIP></Naglowek>
  <Fa><P_2>{NUMER_MARKER}</P_2></Fa>
</Faktura>"""
    with caplog.at_level(logging.DEBUG, logger="fa3check.web"):
        client.post("/waliduj", data={"xml": xml})
    kawalki: list[str] = [caplog.text]
    for r in caplog.records:
        kawalki.append(r.getMessage())
        if r.exc_text:
            kawalki.append(r.exc_text)
        if r.exc_info and r.exc_info[1] is not None:
            kawalki.append(str(r.exc_info[1]))
    polaczone = "\n".join(kawalki)
    assert NIP_MARKER not in polaczone
    assert NUMER_MARKER not in polaczone
    assert "<Faktura" not in polaczone
    assert "Naglowek" not in polaczone


def test_xss_escapowany(client: TestClient) -> None:
    """Wartość z faktury trafia do wyniku (TEC-007); szablon nie oddaje surowego <script>."""
    dane = (ZLOTY / "fa3-przyklad-01.xml").read_text(encoding="utf-8")
    zlosliwy_numer = "&lt;script&gt;alert(1)&lt;/script&gt;"
    dane = re.sub(r"<P_2>[^<]*</P_2>", f"<P_2>{zlosliwy_numer}</P_2>", dane, count=1)
    r = client.post("/waliduj", data={"xml": dane})
    assert r.status_code == 200
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


def test_powtarzalnosc_odpowiedzi(client: TestClient) -> None:
    dane = (ZLOTY / "fa3-przyklad-01.xml").read_text(encoding="utf-8")
    r1 = client.post("/waliduj", data={"xml": dane})
    r2 = client.post("/waliduj", data={"xml": dane})
    assert r1.status_code == 200
    assert _bez_czasu(r1.text) == _bez_czasu(r2.text)


def test_zloty_korpus_w_budzecie(client: TestClient) -> None:
    t0 = time.perf_counter()
    for plik in sorted(ZLOTY.glob("fa3-przyklad-*.xml")):
        r = client.post("/waliduj", data={"xml": plik.read_text(encoding="utf-8")})
        assert r.status_code == 200
    assert time.perf_counter() - t0 < 60.0


def test_reguly_strona(client: TestClient) -> None:
    r = client.get("/reguly")
    assert r.status_code == 200
    assert "SEM-001" in r.text or "TEC-001" in r.text
