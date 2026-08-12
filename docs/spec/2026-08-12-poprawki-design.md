# ksef-fa3-checker — spec poprawek

**Data:** 2026-08-12
**Dotyczy:** <https://github.com/Iakirmon/ksef-fa3-checker> na commicie `7ca2fae`
**Status:** do realizacji
**Dokument nadrzędny:** `docs/spec/2026-08-11-fa3-check-design.md` — ten spec go **uzupełnia
i w trzech punktach koryguje**, nie zastępuje.

---

## 0. Jak czytać ten dokument

Projekt jest zbudowany i działa. To nie jest przepisywanie, a lista sześciu konkretnych defektów
z dowodami, przyczynami i kryteriami odbioru. Kolejność w sekcji 8 jest kolejnością priorytetu —
nie zaczynaj od końca.

**Trzy z sześciu defektów wynikają z błędów w specu z 11 sierpnia, nie z implementacji.** Są
oznaczone jako **[błąd specu]**. W tych przypadkach poprawka polega na zmianie reguły projektu,
a nie na naprawianiu kodu, który tę regułę wiernie wykonał.

### Co zostało zweryfikowane przed napisaniem tego dokumentu

Wszystkie liczby poniżej pochodzą z uruchomienia na sklonowanym repozytorium, nie z lektury.

| Sprawdzenie | Wynik |
|---|---|
| `pytest` | **137 testów, wszystkie zielone** |
| `mypy --strict` z wykluczeniami z `pyproject.toml` | czysto, **14 plików** |
| `ruff format --check .` | czysto, 80 plików |
| `ruff check .` | **2 błędy `I001`** — jedyna przyczyna czerwonego CI |
| `scripts/sprawdz_provenance.py` | OK, 32 pliki |
| Złoty korpus, 26 faktur | zero `BLAD`; **26 × `TEC-006` + 26 × `TEC-007`** |
| Pokrycie | 87% (próg w specie: 90%, nieegzekwowany) |
| Rejestry | 13 reguł + 8 tłumaczeń = 21 wpisów |
| **Próba zmiany nazw katalogów na poprawne identyfikatory** | **137 testów zielonych, `mypy --strict src/` obejmuje 35 plików i przechodzi** |
| `XSD-kwota-zapis` na polu daty `P_1 = 2026-13-45` | **odpala się** z treścią o separatorze tysięcy — drugie wystąpienie defektu B, nieopisane w pierwszej wersji tego dokumentu |
| Typy z facetem `pattern` w FA(3) | **17**, nie 2: trzy kwotowe, trzy podatkowe identyfikatory, jedenaście pozostałych (e-mail, SWIFT, data, PESEL, REGON, KRS, numer KSeF…) |
| Cytat nadający się na wpis ogólny w broszurze | **nie istnieje** — jedyny kandydat to fragment nagłówka „Ogólne założenia dotyczące formatu pól: 1." |
| Cytat ze schematu, np. `targetNamespace="…13775/"` | **występuje dosłownie** w wendorowanym pliku, więc da się go weryfikować testem |
| Czy `test_zrodla.py` obsługuje źródło schematowe | **nie** — nazwa `schemat_FA(3)_v1-0E.xsd` zawiera `fa(3)`, więc wpadłaby do gałęzi broszury i test by padł |
| Parametr `klucze` (liczba mnoga) w `@tlumacz` | **istnieje** i obsługuje wiele kluczy na wpis |

Dwa wiersze są istotne szczególnie. Poprawka D została **wykonana i przetestowana**, nie
założona. A defekt B okazał się szerszy, niż wyglądał przy pierwszym przeglądzie — dlatego
sekcja 2 została przepisana i **pierwsza wersja proponowanej tam poprawki była błędna**:
kazała użyć cytatów pkt 5 i pkt 10, które są już zajęte przez istniejące wpisy.

---

## 1. Defekt A — CI świeci czerwono na `main`

**Priorytet: pilny.** Cztery ostatnie przebiegi `ci` mają `conclusion: failure`. Udane są tylko
wdrożenia GitHub Pages.

**Dowód i przyczyna.** Jedyny padający krok to `ruff check .`:

```
tests/test_reguly.py:3:1:       I001 Import block is un-sorted or un-formatted
tests/test_tec005_dowod.py:3:1: I001 Import block is un-sorted or un-formatted
```

Pozostałe kroki przechodzą lokalnie: `ruff format --check`, `mypy`, `pytest` (137), PROVENANCE (32).

**Poprawka.**

```
ruff check --fix .
ruff format .
```

**Kryterium odbioru.** Zielony przebieg `ci` na `main` we wszystkich trzech wersjach Pythona.

**Dlaczego pilny.** Dla repozytorium portfolio czerwone Actions są sygnałem gorszym niż brak CI —
pokazują, że autor nie patrzy. Kosztem trzydziestu sekund kasujesz jedyny naprawdę zły sygnał
w całym repo.

---

## 2. Defekt B — mylące i zdublowane zastrzeżenie na polach kwotowych

**Priorytet: wysoki.** To defekt merytoryczny, uderzający w samo sedno obietnicy projektu.

### 2.1 Dowody — dwa niezależne wystąpienia, oba potwierdzone uruchomieniem

**Wystąpienie pierwsze: kwota z trzema miejscami daje dwa zastrzeżenia, drugie mylące.**

```
P_11 = 1234.567   →   2 zastrzeżenia wagi BLAD

XSD-kwota-precyzja   CO: W polu P_11 wpisano 1234.567, a dopuszczalne jest
                         co najwyżej 2 miejsc po kropce (typ TKwotowy).     ← poprawne
XSD-wzorzec          CO: Wartość „1234.567" w polu P_11 nie pasuje do
                         wymaganego wzorca zapisu.
                DLACZEGO: …schemat wymusza dokładny format identyfikatora
                         bez separatorów.                                    ← BŁĄD
                   CYTAT: „Numery identyfikacji podatkowej ujęte…"           ← BŁĄD
```

**Wystąpienie drugie, nieopisane w pierwszej wersji tego specu: tłumaczenie kwotowe odpala się
na polu daty.**

```
P_1 = 2026-13-45   →   XSD-kwota-zapis
   CO: W polu P_1 wartość „2026-13-45" nie jest poprawną liczbą —
       najczęściej przez spację tysięcy albo przecinek zamiast kropki.       ← BŁĄD

P_1 = wczoraj      →   XSD-kwota-zapis, ta sama treść                        ← BŁĄD
```

`P_1` jest datą typu `TDataT`. Wyjaśnienie mówi o separatorze tysięcy.

### 2.2 Przyczyna — jedna, wspólna dla obu wystąpień

Nie jest to błąd dopasowania. `_score` działa poprawnie. Przyczyna jest w kluczach i w tym, że
**`Zrodlo` jest niemutowalne i przypisane do wpisu**:

| Wpis | Klucz dziś | Treść założona | Skutek |
|---|---|---|---|
| `XSD-kwota-zapis` | `typ_lxml=SCHEMAV_CVC_DATATYPE_VALID_1_2_1`, **bez `typ_xsd`** | pole kwotowe | odpala się na każdym typowanym polu, w tym na datach |
| `XSD-wzorzec` | `typ_lxml=SCHEMAV_CVC_PATTERN_VALID`, **bez `typ_xsd`** | identyfikator podatkowy | odpala się na kwotach, e-mailach, SWIFT-ach, datach |

Kod `DATATYPE_VALID_1_2_1` powstaje dla **dowolnego** pola o zadeklarowanym typie, a
`PATTERN_VALID` dla **każdego** typu z facetem `pattern`. Sprawdzone: takich typów jest
siedemnaście, a nie dwa.

**[błąd specu]** Spec z 11 sierpnia mówił „reguła sprawdza jedną rzecz", ale nie powiedział tego
o tłumaczeniach. Brakująca zasada, do dopisania do `.cursor/rules/10-reguly.mdc`:

> **Tłumaczenie, którego treść zakłada rodzinę pól, musi być zawężone przez `typ_xsd`.**
> Jeden wpis = jedno `Zrodlo` = jedna rodzina pól. Klucz po samym `typ_lxml` jest dozwolony
> wyłącznie dla wpisu ogólnego, którego treść nie zakłada niczego o rodzaju pola.

### 2.3 Zweryfikowane fakty potrzebne do poprawki

Odczytane z `korpus/schema/`, nie z pamięci. **Nie zgaduj tej listy ponownie — jest sprawdzona.**

Typy z facetem `pattern`, pogrupowane:

| Rodzina | Typy | Elementy (przykłady) |
|---|---|---|
| kwotowe i ilościowe (baza `decimal`) | `TKwotowy` (39 elementów), `TKwotowy2` (4), `TIlosci` (7) | `P_11`, `P_9A`, `KursWaluty`, `P_8B` |
| podatkowe identyfikatory | `TNrNIP`, `TNIPIdWew`, `TNrVatUE` | `NIP`, `IDWew`, `NrVatUE` |
| pozostałe — **nie są identyfikatorami podatkowymi** | `TAdresEmail`, `SWIFT_Type`, `TData`, `TNrPESEL`, `TNrREGON`, `TNrKRS`, `TNumerKSeF`, `TKodKrajuUrodzenia`, `TKodKrajuWydania`, `TNrAKC`, `TNrDokumentu` | `Email`, `SWIFT`, `Termin`, `PESEL`, `REGON`, `KRS`, `NrKSeFFaKorygowanej` |

Typy **bez** `pattern`, więc bez sensu jako klucz: `TKwotowy3`, `TZnakowy`, `TZnakowy512`,
`TDataT`.

Zajęte cytaty — pkt 3, 5, 6, 8, 10 oraz dwa razy „Wzór faktury ustrukturyzowanej" (s. 3). Nowy
wpis nie może użyć zajętego cytatu, bo `/audyt-zrodel` zgłasza dwa wpisy z identycznym cytatem
jako defekt.

**W broszurze nie istnieje cytat nadający się na wpis ogólny.** Sprawdzone: jedyny kandydat to
fragment nagłówka „Ogólne założenia dotyczące formatu pól: 1.", co nie jest regułą. Dlatego wpis
ogólny cytuje **schemat**, a nie broszurę — patrz punkt 3 poprawki.

### 2.4 Poprawka — trzy zmiany, nie trzy nowe wpisy

Pierwsza wersja tego specu proponowała rozbicie na trzy nowe wpisy z cytatami pkt 5 i pkt 10.
To byłoby błędem: te cytaty są **już zajęte**, a nowe wpisy powielałyby regułę, którą istniejące
wpisy już opisują. Właściwe rozwiązanie jest mniejsze.

**Zmiana 1 — zawęź `XSD-kwota-zapis` i dodaj mu drugi kod błędu.**

Użyj parametru `klucze` (liczba mnoga, istnieje w `@tlumacz`), po jednym kluczu na kombinację
kodu i typu — sześć kluczy:

```python
klucze=(
    KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1", typ_xsd="TKwotowy"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1", typ_xsd="TKwotowy2"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1", typ_xsd="TIlosci"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID",        typ_xsd="TKwotowy"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID",        typ_xsd="TKwotowy2"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID",        typ_xsd="TIlosci"),
)
```

Cytat (pkt 5) i treść zostają bez zmian — są poprawne dla kwot. Zysk podwójny: wpis przestaje
odpalać się na datach, a jednocześnie przejmuje przypadek wzorca dla kwot, więc mylące
`XSD-wzorzec` już się tam nie pojawi.

**Zmiana 2 — zawęź `XSD-wzorzec` do identyfikatorów podatkowych.**

```python
klucze=(
    KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TNrNIP"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TNIPIdWew"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID", typ_xsd="TNrVatUE"),
)
```

Usuń z `co()` gałąź ogólną — po zawężeniu jest martwa. `dlaczego()` może zostać, bo teraz mówi
prawdę bezwarunkowo, a cytat pkt 10 staje się trafny dla wszystkich trzech typów.

`TNrPESEL`, `TNrREGON`, `TNrKRS` i `TNumerKSeF` **nie** wchodzą tutaj — nie są numerami
identyfikacji podatkowej, więc cytat pkt 10 byłby dla nich nadużyciem. Trafiają do wpisu ogólnego.

**Zmiana 3 — jeden nowy wpis ogólny, cytujący schemat.**

`tlumaczenia/xsd_typ_schemat/`, klucze bez `typ_xsd`, więc punktacja 1 i przegrywa z zawężonymi:

```python
klucze=(
    KluczBledu(typ_lxml="SCHEMAV_CVC_DATATYPE_VALID_1_2_1"),
    KluczBledu(typ_lxml="SCHEMAV_CVC_PATTERN_VALID"),
)
```

Źródłem jest schemat, bo w broszurze nie ma odpowiedniego zdania:

```python
Zrodlo(
    dokument="schemat_FA(3)_v1-0E.xsd",
    wersja="2026-06-25",
    sekcja="deklaracja schematu",
    cytat='targetNamespace="http://crd.gov.pl/wzor/2025/06/25/13775/"',
    url="https://crd.gov.pl/wzor/2025/06/25/13775/",
)
```

Ten cytat **występuje dosłownie** w wendorowanym pliku — sprawdzone.

Treść musi być neutralna: nazwa pola, wartość, nazwa typu z `blad.typ_xsd`, i zdanie, że wartość
nie spełnia ograniczenia zadeklarowanego dla tego typu w schemacie. **Bez** słów „liczba",
„separator tysięcy", „identyfikator", „data" — wpis obsługuje wszystkie pozostałe rodziny naraz
i nie wolno mu zakładać żadnej.

**Zmiana 3a — `test_zrodla.py` musi umieć sprawdzić cytat ze schematu.**

Obecnie rozstrzyga po nazwie dokumentu: `weryfikacja`/`ksef-docs` → `weryfikacja-faktury.md`,
`broszura`/`fa(3)` albo niepusta `strona` → broszura. Nazwa `schemat_FA(3)_v1-0E.xsd` zawiera
`fa(3)`, więc **wpadłaby do gałęzi broszury i test by padł**.

Dodaj gałąź **przed** istniejącymi, rozpoznającą po `.xsd` w nazwie dokumentu, sprawdzającą
dosłowność wobec połączonej treści plików z `korpus/schema/` po normalizacji białych znaków.
Wpisy ze źródłem schematowym mają `strona=None`.

**Zmiana 4, zalecana — odszumienie duplikatów.**

Po zmianach 1–3 kwota z trzema miejscami nadal daje dwa błędy schematu
(`FRACTIONDIGITS_VALID` → `XSD-kwota-precyzja`, `PATTERN_VALID` → `XSD-kwota-zapis`), więc dwa
zastrzeżenia. W `walidacja.py` scal zastrzeżenia o tym samym `(xpath, linia)`, zostawiając jedno
według jawnej kolejności szczegółowości kodu:

```
SCHEMAV_CVC_FRACTIONDIGITS_VALID  >  SCHEMAV_CVC_MAXLENGTH_VALID
>  SCHEMAV_CVC_MININCLUSIVE_VALID  >  SCHEMAV_CVC_PATTERN_VALID
>  SCHEMAV_CVC_DATATYPE_VALID_1_2_1
```

Identyfikatory odrzuconych wpisów dopisz do `diagnostyka` — nic nie znika bez śladu.

Uzasadnienie kolejności: facet nazwany wprost (`fractionDigits`, `maxLength`, `minInclusive`)
mówi użytkownikowi więcej niż ogólne „nie pasuje do wzorca", a to więcej niż „nie jest wartością
tego typu".

### 2.5 Kryteria odbioru — sprawdzalne wprost

| Wejście | Oczekiwanie |
|---|---|
| `P_11 = 1234.567` | **jedno** zastrzeżenie, `XSD-kwota-precyzja`, cytat s. 6 pkt 6 |
| `P_11 = 1 234.56` | jedno, `XSD-kwota-zapis`, cytat s. 6 pkt 5 |
| `P_11 = 1234,56` | jedno, `XSD-kwota-zapis` |
| `P_1 = 2026-13-45` | `XSD-typ-schemat`, **bez** słów „liczba", „separator", „przecinek" |
| `NIP = 123-456-78-90` | `XSD-wzorzec`, cytat s. 6 pkt 10 |
| `Email = niepoprawny` | `XSD-typ-schemat`, cytat ze schematu |
| złoty korpus, 26 faktur | bez zmian: zero `BLAD` |

Do tego:

- `test_zrodla.py` zielony, w tym nowa gałąź schematowa,
- 137 testów nadal przechodzi (plus nowe, które dopiszesz),
- **nowy test w `test_wyjasnienia.py`:** dla każdego tłumaczenia, którego treść zawiera słowo
  z listy rodzin (`liczb`, `kwot`, `separator`, `identyfikator`, `data`, `NIP`), wszystkie jego
  klucze muszą mieć niepuste `typ_xsd`. To mechaniczna bariera przed powtórzeniem tego defektu
  w trzecim miejscu.

---

## 3. Defekt C — osłabiony niezmiennik parsowania **[błąd specu]**

**Priorytet: średni.**

**Dowód.** `tests/test_niezmienniki.py`:

```python
dozwolone_import = frozenset({"safexml.py", "schema.py", "struktura.py"})
dozwolone_parse  = frozenset({"safexml.py", "schema.py", "struktura.py"})
```

Do listy wyjątków dopisano dokładnie te pliki, które regułę łamią, więc test nie może już zapłonąć.

**Przyczyna.** Spec z 11 sierpnia postawił niezmiennik zbyt absolutnie: *„`etree.parse` nie ma
prawa wystąpić nigdzie indziej"*. Nie rozróżnił **niezaufanego wejścia od zaufanych, wendorowanych
plików schematu**. `schema.py` i `struktura.py` parsują pliki z `korpus/schema/`, których SHA-256
jest sprawdzany w CI. To zachowanie jest poprawne — zła była reguła.

Osłabienie testu było pragmatyczną reakcją na złą regułę, ale skutek jest ten sam: niezmiennik
przestał być pilnowany, a w kodzie została niespójność. `schema.py:23` parsuje zahartowanym
parserem, a `schema.py:40` i `struktura.py:62` gołym.

**Poprawka. Zawęź niezmiennik, potem egzekwuj go bez wyjątków.**

Nowe brzmienie do `.cursor/rules/00-projekt.mdc` i `AGENTS.md`, w miejsce dotychczasowego
punktu o parsowaniu:

> **Niezaufane wejście parsuje wyłącznie `safexml.sparsuj()`.** Żaden inny moduł nie dotyka
> bajtów pochodzących od użytkownika.
>
> **Zaufane pliki schematu z `korpus/schema/` wolno parsować w `schema.py` i `struktura.py`**,
> ale **zawsze parserem zahartowanym**: `resolve_entities=False`, `no_network=True`,
> `load_dtd=False`. Ich integralność zabezpiecza SHA-256 w `PROVENANCE`, nie parser — ale parser
> jest darmowy, więc nie ma powodu go pomijać.

Potem:

1. dodaj brakujące flagi w `schema.py:40` i `struktura.py:62` — najlepiej przez jedną, wspólną
   funkcję `_parser_schematu()`, żeby nie dało się jej pominąć,
2. przepisz `test_niezmienniki.py` tak, żeby **nie miał listy wyjątków plików**, a sprawdzał
   regułę realną: każde wywołanie `etree.parse` / `etree.fromstring` poza `safexml.py` musi
   przekazywać argument `parser=`. Analiza AST wystarcza — sprawdź obecność słowa kluczowego
   w wywołaniu,
3. usuń `test_lxml_tylko_w_safexml()`, który jest jednolinijkowym opakowaniem na
   `test_lxml_parser_tylko_w_safexml()` i podwaja licznik testów bez dodawania sprawdzenia.

**Kryterium odbioru.** `test_niezmienniki.py` bez żadnej listy wyjątków plików. Test upada po
tymczasowym usunięciu `parser=` z dowolnego wywołania — udowodnij to i pokaż czerwony wynik.

---

## 4. Defekt D — `mypy --strict` nie obejmuje rejestrów **[błąd specu]**

**Priorytet: średni.** To najbardziej kosztowny z moich błędów: bez typowania zostało 21 wpisów
z większością logiki domenowej.

**Dowód.** `pyproject.toml`:

```toml
[tool.mypy]
exclude = [
    "^src/fa3check/tlumaczenia/.+/",
    "^src/fa3check/reguly/.+/",
]
```

`mypy --strict` sprawdza **14 plików** zamiast 35.

**Przyczyna.** Spec kazał nazywać katalog dokładnie identyfikatorem wpisu: `SEM-001`,
`XSD-kwota-precyzja`. To **nie są poprawne nazwy modułów Pythona** — myślnik jest niedozwolony.
Konsekwencje: ładowanie tylko przez `importlib.util.spec_from_file_location`, sanityzacja nazwy
(`katalog.name.replace("-", "_")` w `rejestr.py`) i brak możliwości sprawdzenia tych plików
przez `mypy`. Wykluczenie było jedynym wyjściem przy tej nazwie katalogów.

**Poprawka — wykonana i przetestowana.** Zmień nazwy katalogów na poprawne identyfikatory,
zachowując identyfikator wyświetlany w metadanych dekoratora.

```
src/fa3check/reguly/SEM-001/            →  src/fa3check/reguly/sem_001/
src/fa3check/tlumaczenia/XSD-kwota-precyzja/ →  .../tlumaczenia/xsd_kwota_precyzja/
```

Skrypt, który to robi w całości (21 katalogów), zachowując historię:

```python
import subprocess
from pathlib import Path

baza = Path("src/fa3check")
for rodzaj in ("reguly", "tlumaczenia"):
    for k in sorted((baza / rodzaj).iterdir()):
        if not k.is_dir() or k.name.startswith(("_", ".")):
            continue
        nowa = k.name.lower().replace("-", "_")
        if nowa != k.name:
            subprocess.run(["git", "mv", str(k), str(k.parent / nowa)], check=True)
```

Potem usuń blok `exclude` z `[tool.mypy]` oraz `--exclude '(^src/fa3check/(tlumaczenia|reguly)/.+)'`
z kroku `Mypy` w `.github/workflows/ci.yml`.

**Dlaczego to jest bezpieczne — sprawdzone, nie założone.** Identyfikator wpisu pochodzi
z dekoratora (`id="SEM-001"`), nie z nazwy katalogu. Fixture'y znajdowane są przez pole
`Regula.katalog` / `Tlumaczenie.katalog`, które trzyma `Path`. Nic w kodzie nie wyprowadza ID
z nazwy katalogu — sprawdziłem `rejestr.py`, `tests/helpers.py` i `web/app.py`.

Wynik próby na sklonowanym repozytorium: **137 testów zielonych, `mypy --strict src/` obejmuje
35 plików i przechodzi bez zastrzeżeń.** Zero zmian w kodzie poza nazwami katalogów
i konfiguracją.

**Zachowaj czytelność.** Skoro nazwa katalogu przestaje być identyfikatorem, dopisz do
`.cursor/rules/10-reguly.mdc`:

> Katalog nazywa się **identyfikatorem zapisanym małymi literami z podkreśleniami**
> (`sem_001`, `xsd_kwota_precyzja`), bo musi być poprawną nazwą modułu Pythona — inaczej wypada
> ze `mypy --strict`. Identyfikator wyświetlany (`SEM-001`) żyje w polu `id` dekoratora
> i tylko on trafia do raportu i na stronę.

**Kryterium odbioru.** `mypy --strict src/` bez wykluczeń, 35 plików, zero błędów. 137 testów
zielonych. Strona `/reguly` nadal pokazuje `SEM-001`, a nie `sem_001`.

---

## 5. Defekt E — szum na każdej poprawnej fakturze

**Priorytet: średni.** Problem użyteczności, nie poprawności.

**Dowód.** Walidacja wszystkich 26 faktur MF:

```
zastrzeżenia po wadze: {ostrzezenie: 26, informacja: 26}
po wpisie:             {TEC-006: 26, TEC-007: 26}
```

Zero `BLAD`, więc bramka złotego korpusu przechodzi. Ale **każda bezbłędna faktura daje dwie
pozycje na liście zastrzeżeń** — o dacie przyjęcia i o duplikacie, czyli o dwóch rzeczach, których
z jednego pliku nie da się rozstrzygnąć.

Użytkownik, który dostaje dwa komunikaty przy pliku bez błędów, po trzeciej fakturze przestaje
czytać listę. To dokładnie ten mechanizm, przed którym spec ostrzegał w innym miejscu:
„walidator, który krzyczy na poprawne faktury, uczy ludzi ignorować ostrzeżenia".

**Poprawka.** Wprowadź strukturalny znacznik zamiast rozpoznawania po treści.

1. W metadanych reguły nowe pole `rozstrzygalna_offline: bool = True`. `TEC-006` i `TEC-007`
   dostają `False`.
2. `Wynik` rozdziela wyniki na dwa krotki: `zastrzezenia` (rozstrzygnięte) i `uwagi_offline`
   (nierozstrzygalne).
3. Strona pokazuje `uwagi_offline` w **osobnym, zwiniętym panelu** „Czego nie sprawdzamy offline",
   nie na liście zastrzeżeń. Panel zostaje widoczny także wtedy, gdy faktura jest czysta — bo ta
   informacja jest wartościowa, tylko nie jest zastrzeżeniem.
4. `test_zloty_korpus.py` zyskuje mocniejsze kryterium: 26 faktur MF daje **zero zastrzeżeń
   w `zastrzezenia`**, niezależnie od wagi.

Punkt czwarty jest zyskiem ubocznym i wartym więcej niż samo odszumienie: bramka przestaje
przepuszczać ostrzeżenia i informacje, więc łapie klasę błędów, której dziś nie łapie.

**Kryterium odbioru.** Poprawna faktura MF: `zastrzezenia` puste, panel offline z dwiema pozycjami.

---

## 6. Defekt F — próg pokrycia bez egzekucji **[błąd specu]**

**Priorytet: niski.**

**Dowód.** Pokrycie 87%. Spec wymagał ≥ 90%. W `pyproject.toml` nie ma `fail_under`, a krok CI
to `pytest --cov=fa3check --cov-report=term-missing` bez progu. Próg nigdy nie był egzekwowany.

**Przyczyna.** Spec podał liczbę, nie podając mechanizmu. Próg bez egzekucji jest ozdobą.

**Poprawka — wybierz jedną z dwóch i zapisz decyzję.**

*Wariant pierwszy, zalecany:* dociągnij pokrycie do 90% i włącz egzekucję:

```toml
[tool.coverage.report]
fail_under = 90
exclude_also = ["if TYPE_CHECKING:", "raise NotImplementedError"]
```

Najtańsze punkty są tam, gdzie ich brakuje najbardziej: `walidacja.py` (80%), `schema.py` (83%),
`web/__main__.py` (0%).

*Wariant drugi:* obniż próg do faktycznych 87% i **napisz w specu, dlaczego** — na przykład że
`web/__main__.py` to punkt wejścia bez logiki. Uczciwy niższy próg jest lepszy od wysokiego
i pozornego.

**Kryterium odbioru.** CI pada, gdy pokrycie spadnie poniżej progu. Sprawdź to, obniżając próg
o dwa punkty i podnosząc z powrotem.

---

## 7. Drobne, przy okazji

- **Luka w numeracji `SEM`.** Zaimplementowane są `SEM-001`, `SEM-004`, `SEM-005`, `SEM-006`,
  a `docs/reguly-z-broszury.md` ma 16 kandydatów. Jeśli `SEM-002` i `SEM-003` są odłożone,
  napisz to w tabeli pokrycia w README. Luka bez wyjaśnienia wygląda na przeoczenie.
- **Odznaka CI w README.** Nie ma jej. Dodaj — ale **po** naprawieniu defektu A, nie przed.
- **Słowo „Demo" w README profilu** (`Iakirmon/Iakirmon`) prowadzi do strony ze zrzutami ekranu,
  a nie do działającego narzędzia. Sama strona mówi uczciwie, że walidator uruchamia się lokalnie.
  Zmień na „opis i zrzuty ekranu" albo postaw prawdziwe demo (sekcja 9, pozycja D).
  To mały wyciek wiarygodności dokładnie w projekcie, którego zaletą jest uczciwość.

---

## 8. Kolejność realizacji

| # | Zakres | Nakład | Ryzyko |
|---|---|---|---|
| 1 | Defekt A — `ruff check --fix`, zielone CI | minuty | zerowe |
| 2 | Defekt D — zmiana nazw katalogów, `mypy` bez wykluczeń | ~30 min | niskie, poprawka przetestowana |
| 3 | Defekt B — zawężenie dwóch wpisów, jeden nowy, gałąź schematowa w `test_zrodla`, odszumienie | 2–3 h | średnie, dotyka tłumaczeń i testu źródeł |
| 4 | Defekt C — zawężenie niezmiennika, przepisanie testu | ~1 h | niskie |
| 5 | Defekt E — znacznik offline, panel na stronie | 1–2 h | niskie |
| 6 | Defekt F — próg pokrycia | ~1 h | zerowe |
| 7 | Sekcja 7 — drobne | ~20 min | zerowe |

Po każdym punkcie: `ruff check . ; if ($?) { mypy --strict src/ } ; if ($?) { pytest -q }`
i commit. Defekt A jako pierwszy, żeby od razu mieć zieloną bazę do porównania.

---

## 9. Co jeszcze — rozszerzenia, nie poprawki

Wszystko poniżej jest **opcjonalne** i nie ma nic wspólnego z defektami. Kolejność według stosunku
wartości do nakładu.

### A. Walidacja wsadowa, która odblokowuje `TEC-007`

Największy zysk architektoniczny w tej liście, bo nie dodaje warstwy, a **uruchamia regułę, która
dziś nie może działać**.

`TEC-007` sprawdza unikalność faktury po trójce: NIP sprzedawcy, rodzaj faktury, numer. Z jednego
pliku jest nierozstrzygalna, więc dziś jest `INFORMACJA`. Ale w **zestawie** wgranym przez
użytkownika jest w pełni rozstrzygalna: duplikat wewnątrz paczki to prawdziwy błąd.

Zakres: wgrywanie wielu plików, wynik zbiorczy z podsumowaniem, `TEC-007` awansowana do `BLAD`
w obrębie zestawu (z jasnym zaznaczeniem, że dotyczy paczki, nie systemu KSeF).

To jest też realna potrzeba księgowego, który dostaje z systemu paczkę stu faktur, a nie jedną.

### B. Wyjście JSON i kody wyjścia dla CLI

`python -m fa3check waliduj faktura.xml --json` zwracające zastrzeżenia w postaci maszynowej,
plus kod wyjścia (0 czysto, 1 zastrzeżenia, 2 błąd wejścia).

Dla odbiorcy, którego nazywa README — integratora ERP — to różnica między demonstracją
a narzędziem, które wchodzi do potoku CI albo do skryptu przed wysyłką. Koszt niewielki, cała
logika już jest.

### C. Proweniencja schematu widoczna na stronie

W stopce: wobec którego pliku walidowano, jego SHA-256 w skrócie, data wersji broszury. Dziesięć
linii kodu, a domyka obietnicę audytowalności — dziś użytkownik wie, **że** cytat jest prawdziwy,
ale nie wie, **wobec czego** go sprawdzono.

### D. Prawdziwe demo online

FastAPI już działa, hartowanie jest zrobione, korpus złośliwych plików istnieje. Darmowy hosting
zamienia stronę informacyjną w narzędzie, którego ktoś użyje bez klonowania repo.

Warunki wstępne, wszystkie już spełnione poza ostatnim: limity rozmiaru i czasu, ogranicznik
żądań, brak logowania treści, widoczna informacja o prywatności, **oraz** zdanie na stronie, że
instancja jest demonstracyjna i nie należy wysyłać do niej faktur produkcyjnych.

### E. Porównanie różnicowe z `ksefuj`

Skrypt deweloperski: przepuść złoty korpus i wszystkie fixture'y przez oba walidatory, wypisz
rozbieżności. Trzy zyski: łapiesz własne fałszywe alarmy, dostajesz materiał do zgłoszeń
w cudzym repozytorium, a README zyskuje sekcję z prawdziwymi liczbami zamiast deklaracji.

Nie jest to konkurowanie — `ksefuj` jest na Apache 2.0 i ma CLI, więc porównanie jest tanie,
a zgłoszony przez Ciebie reprodukowalny przypadek jest wkładem, nie atakiem.

### F. Reszta, gdyby zostało czasu

Odznaka pokrycia po włączeniu progu. Interfejs po angielsku — README jest już dwujęzyczne, więc
strona jest niespójna. Podstawy dostępności strony: kontrast, nawigacja klawiaturą, `aria-live`
na wyniku wstawianym przez HTMX.

---

## 10. Czego nie robić

- **Nie przepisuj tego, co działa.** 137 testów przechodzi, złoty korpus jest czysty, wyjaśnienia
  są dobre. To lista poprawek, nie refaktoryzacja.
- **Nie osłabiaj testów, żeby przeszły.** Defekt C powstał właśnie tak. Jeśli test przeszkadza,
  zepsuta jest reguła albo kod — rozstrzygnij które i napraw właściwą rzecz.
- **Nie dodawaj reguł duplikujących XSD.** Pytanie kwalifikujące z sekcji 9.3 specu głównego
  obowiązuje nadal.
- **Nie zmyślaj cytatów ani nazw typów.** `test_zrodla.py` sprawdza dosłowność wobec wyciągu
  broszury, a nazwy typów czyta się z `korpus/schema/`. Nowe wpisy z defektu B potrzebują
  prawdziwych cytatów ze stron 5–6.
- **Nie ruszaj rzeczy z sekcji 9**, dopóki wszystkie defekty z sekcji 8 nie są zamknięte.
