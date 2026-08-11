# fa3-check

Walidator faktury ustrukturyzowanej FA(3) (KSeF): wklejasz XML, dostajesz zastrzeżenia
z cytatem ze źródła MF — nie sam komunikat parsera.

## Przykład (SEM-001)

Faktura z polskim NIP-em nabywcy w polu `NrVatUE` zamiast `NIP` przejdzie schemat i może
dostać numer w KSeF, a nabywca jej nie zobaczy.

| Część | Treść |
|---|---|
| **Co** | Numer 5252341139 wygląda na polski NIP, a jest zapisany w polu NrVatUE. Pole NIP w elemencie Podmiot2/DaneIdentyfikacyjne jest puste. |
| **Dlaczego** | Faktura zostanie przyjęta przez KSeF i dostanie numer, ale nabywca jej nie zobaczy — system udostępnia fakturę nabywcy tylko wtedy, gdy jego NIP jest w polu NIP. |
| **Jak naprawić** | Przenieś numer do pola NIP w Podmiot2/DaneIdentyfikacyjne i usuń NrVatUE. |
| **Źródło** | Broszura FA(3), s. 6 — ramka WAŻNE |
| **Cytat** | „Polski identyfikator podatkowy NIP nabywcy należy podawać w polu NIP w elemencie Podmiot2/DaneIdentyfikacyjne…” |

## Pokrycie rejestrów

Wygenerowane z rejestrów (`python scripts/pokrycie.py`), nie wpisane z pamięci:

| Rejestr | Liczba |
|---|---|
| Reguły łącznie | 13 |
| — techniczna | 7 |
| — semantyczna | 4 |
| — arytmetyczna | 2 |
| Tłumaczenia schematu | 8 |
| Reguły z numerem strony broszury | 6 |
| Reguły rozstrzygalne offline (szacunek) | 11 |

## Dlaczego dwa rejestry

FA(3) stoi na XML Schema 1.0 z pełnym zestawem facetów: długości, wzorce, precyzja kwot,
kolejność elementów. Tego nie warto dublować regułami — tłumaczymy komunikaty schematu
na język księgowego (`tlumaczenia/`).

Poza schematem zostaje to, czego XSD nie wyraża: zależności między polami, sumy kontrolne
NIP, arytmetyka VAT, limity techniczne KSeF opisane poza XSD (`reguly/`).

## Jak to jest sprawdzane

`tests/test_zrodla.py` wymaga, by `zrodlo.cytat` każdego wpisu **występował dosłownie**
w wendorowanym pliku źródłowym (`korpus/broszura/broszura-fa3.txt` albo
`korpus/zrodla/weryfikacja-faktury.md`), a dla broszury — by numer strony wskazywał
właściwy znacznik. To bramka CI, nie obietnica w README.

## Stan sztuki

Otwarte i komercyjne walidatory FA(3) różnią się zasięgiem semantyki. Projekt
[`ksefuj`](https://github.com/ksefuj/ksefuj) jest mocny szczególnie tam, gdzie waliduje
**w przeglądarce** (`libxml2-wasm`) — XML nie opuszcza komputera użytkownika. fa3-check
stawia na audytowalność cytatów i warstwę webową z hartowaniem; nie kopiuje reguł ksefuj.

## Ograniczenia

- Zielony wynik **nie** gwarantuje przyjęcia przez KSeF (m.in. unikalność globalna,
  uprawnienia, szyfrowanie sesji — patrz TEC-006/007 i dokument weryfikacji MF).
- Przyjęcie przez KSeF **nie** gwarantuje poprawności faktury (system nie weryfikuje
  pełnej rachunkowości pozycji).

## Prywatność

Plik żyje tylko w pamięci żądania. W logach: rozmiar, liczba zastrzeżeń, czas — bez NIP,
numeru faktury i fragmentów XML. Korpus `korpus/zlosliwe/` i testy XXE/BOM/bomb
pilnują parsera.

## Uruchomienie

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
python -m fa3check.web
```

Strona: http://127.0.0.1:8000 — wyłącznie localhost do czasu świadomego wdrożenia.

## Jak dodać wpis

1. Pytanie kwalifikujące: czy XSD już to łapie facetem / `choice`? Jeśli tak — tłumaczenie,
   nie reguła.
2. Katalog `src/fa3check/reguly/<ID>/` albo `tlumaczenia/<ID>/` z `zrodlo.md` i fixture'ami.
3. Dekorator `@rejestruj` / `@tlumacz`, cytat dosłowny ze źródła.
4. `pytest` — w tym różnicowy test fixture'ów i złoty korpus MF (zero `BLAD`).

## Źródła

Bibliografia i podział broszury: [docs/zrodla.md](docs/zrodla.md).
Wyciąg kandydatów: [docs/reguly-z-broszury.md](docs/reguly-z-broszury.md).

Licencja: MIT.
