"""FastAPI + Jinja2 + HTMX — lokalna warstwa webowa."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fa3check.rejestr import reguly, tlumaczenia
from fa3check.safexml import LIMIT_BAJTOW
from fa3check.typy import Fa3Error, Poziom, Waga, Wynik, Zastrzezenie
from fa3check.walidacja import zwaliduj

_KATALOG = Path(__file__).resolve().parent
_SZABLONY = Jinja2Templates(directory=str(_KATALOG / "szablony"))
# Autoescape włączony domyślnie dla .html — nie używamy |safe w wynikach.

logger = logging.getLogger("fa3check.web")

LIMIT_CZASU_S = 10.0
LIMIT_ZADAN_NA_MIN = 30

_historia: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(title="fa3-check", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(_KATALOG / "static")), name="static")


def _klient_ip(request: Request) -> str:
    if request.client is None:
        return "unknown"
    return request.client.host


def _ogranicznik(ip: str, teraz: float) -> bool:
    """True jeśli żądanie wolno obsłużyć."""
    okno = _historia[ip]
    while okno and teraz - okno[0] > 60.0:
        okno.popleft()
    if len(okno) >= LIMIT_ZADAN_NA_MIN:
        return False
    okno.append(teraz)
    return True


@app.middleware("http")
async def naglowki_i_limit(request: Request, call_next: Any) -> Response:
    teraz = time.monotonic()
    if request.url.path == "/waliduj" and request.method == "POST":
        if not _ogranicznik(_klient_ip(request), teraz):
            return HTMLResponse(
                "<p class='blad'>Zbyt wiele żądań. Odczekaj chwilę i spróbuj ponownie.</p>",
                status_code=429,
            )
        cl = request.headers.get("content-length")
        if cl is not None:
            try:
                if int(cl) > LIMIT_BAJTOW:
                    return HTMLResponse(
                        f"<p class='blad'>Treść żądania przekracza limit "
                        f"{LIMIT_BAJTOW} B (3 MB).</p>",
                        status_code=413,
                    )
            except ValueError:
                pass

    odpowiedz: Response = await call_next(request)
    odpowiedz.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    odpowiedz.headers["X-Content-Type-Options"] = "nosniff"
    odpowiedz.headers["Referrer-Policy"] = "no-referrer"
    return odpowiedz


def _grupuj(zastrzezenia: tuple[Zastrzezenie, ...]) -> list[dict[str, Any]]:
    kolejnosc = [Waga.BLAD, Waga.OSTRZEZENIE, Waga.INFORMACJA]
    etykiety = {
        Waga.BLAD: "Błędy",
        Waga.OSTRZEZENIE: "Ostrzeżenia",
        Waga.INFORMACJA: "Informacje",
    }
    grupy: list[dict[str, Any]] = []
    for waga in kolejnosc:
        pozycje = [z for z in zastrzezenia if z.waga == waga]
        if pozycje:
            grupy.append({"waga": waga.value, "etykieta": etykiety[waga], "pozycje": pozycje})
    return grupy


def _werdykt(wynik: Wynik) -> str:
    bledy = sum(1 for z in wynik.zastrzezenia if z.waga == Waga.BLAD)
    if wynik.czesciowy:
        return (
            "Schemat odrzucił dokument — wynik jest częściowy; "
            "część sprawdzeń semantycznych mogła nie mieć pełnych danych."
        )
    if bledy:
        return f"Znaleziono {bledy} błędów do poprawy przed wysyłką."
    if wynik.zastrzezenia:
        return "Brak błędów blokujących; są ostrzeżenia lub informacje."
    return "Dokument przeszedł sprawdzenia bez zastrzeżeń."


@app.get("/", response_class=HTMLResponse)
async def strona_glowna(request: Request) -> HTMLResponse:
    return _SZABLONY.TemplateResponse(
        request,
        "strona.html",
        {"limit_mb": 3},
    )


@app.post("/waliduj", response_class=HTMLResponse)
async def waliduj_post(
    request: Request,
    xml: str = Form(default=""),
) -> HTMLResponse:
    t0 = time.perf_counter()
    dane = xml.encode("utf-8")
    rozmiar = len(dane)
    kod = 200
    liczba = 0
    try:
        if rozmiar > LIMIT_BAJTOW:
            kod = 413
            return HTMLResponse(
                f"<p class='blad'>Treść przekracza limit {LIMIT_BAJTOW} B (3 MB).</p>",
                status_code=413,
            )
        wynik = zwaliduj(dane)
        liczba = len(wynik.zastrzezenia)
        kontekst = {
            "wynik": wynik,
            "werdykt": _werdykt(wynik),
            "grupy": _grupuj(wynik.zastrzezenia),
        }
        return _SZABLONY.TemplateResponse(request, "wynik.html", kontekst)
    except Fa3Error:
        # zwaliduj nie powinien rzucać; zabezpieczenie transportowe
        kod = 400
        return HTMLResponse(
            "<p class='blad'>Nie udało się przetworzyć dokumentu.</p>",
            status_code=400,
        )
    finally:
        ms = int((time.perf_counter() - t0) * 1000)
        logger.info(
            "waliduj size=%s zastrzezenia=%s czas_ms=%s status=%s",
            rozmiar,
            liczba,
            ms,
            kod,
        )


@app.get("/reguly", response_class=HTMLResponse)
async def lista_regul(request: Request, poziom: str | None = None) -> HTMLResponse:
    filtry = {p.value for p in Poziom}
    wybrany = poziom if poziom in filtry else None
    lista_r = [r for r in reguly() if wybrany is None or r.poziom.value == wybrany]
    lista_t = [t for t in tlumaczenia() if wybrany is None or wybrany == Poziom.SCHEMA.value]
    return _SZABLONY.TemplateResponse(
        request,
        "reguly.html",
        {
            "reguly": lista_r,
            "tlumaczenia": lista_t,
            "poziomy": sorted(filtry),
            "wybrany": wybrany,
        },
    )


@app.get("/zdrowie")
async def zdrowie() -> JSONResponse:
    return JSONResponse({"status": "ok"})
