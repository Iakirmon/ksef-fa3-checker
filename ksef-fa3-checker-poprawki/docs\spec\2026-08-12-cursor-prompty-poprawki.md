# ksef-fa3-checker — prompty poprawek

Jeden nowy czat na defekt. Do każdego promptu dołącz spec poprawek:
`@docs/spec/2026-08-12-poprawki-design.md`

Po każdym defekcie weryfikacja i commit:

```
ruff check . ; if ($?) { mypy --strict src/ } ; if ($?) { pytest -q }
```

Punktem odniesienia jest stan zmierzony 12 sierpnia: **137 testów zielonych**, złoty korpus bez
`BLAD`, `ruff check` z dwoma błędami. Jeśli po Twojej zmianie testów jest mniej niż 137 albo
któryś pada — cofnij się, zanim pójdziesz dalej.

---

## Defekt A — zielone CI

```
Przeczytaj @docs/spec/2026-08-12-poprawki-design.md, sekcja 1.

CI na main świeci czerwono. Jedyny padający krok to `ruff check .` z dwoma błędami I001
(sortowanie importów) w tests/test_reguly.py i tests/test_tec005_dowod.py. Wszystkie pozostałe
kroki przechodzą.

1. ruff check --fix .
2. ruff format .
3. Uruchom pełną weryfikację i pokaż mi wynik: ruff check, ruff format --check,
   mypy --strict src/, pytest -q, python scripts/sprawdz_provenance.py.
4. Commit.

Nic więcej w tym czacie. Nie poprawiaj innych rzeczy „przy okazji" — reszta ma własne etapy
i własne kryteria odbioru.
```

**Ukończone, gdy:** wszystkie pięć kroków lokalnie zielone i commit gotowy do wypchnięcia.

---

## Defekt D — zmiana nazw katalogów, `mypy` bez wykluczeń

Robiony jako drugi, przed defektem B, bo B dodaje nowe katalogi tłumaczeń — lepiej, żeby od razu
powstały z poprawną nazwą.

```
Sekcja 4 specu poprawek.

mypy --strict sprawdza 14 plików zamiast 35, bo pyproject.toml wyklucza reguly/ i tlumaczenia/.
Przyczyną jest nazwa katalogu równa identyfikatorowi wpisu — SEM-001 i XSD-kwota-precyzja nie są
poprawnymi nazwami modułów Pythona. To błąd specu z 11 sierpnia, nie Twojej implementacji.

Ta poprawka została WYKONANA I PRZETESTOWANA na klonie repozytorium: 137 testów zielonych,
mypy --strict src/ obejmuje 35 plików i przechodzi bez zastrzeżeń, zero zmian w kodzie poza
nazwami katalogów i konfiguracją. Skrypt jest w sekcji 4 specu.

1. Zmień nazwy 21 katalogów w reguly/ i tlumaczenia/ na małe litery z podkreśleniami,
   przez `git mv`, żeby zachować historię. Użyj skryptu ze specu.
2. Usuń blok exclude z [tool.mypy] w pyproject.toml.
3. Usuń --exclude z kroku Mypy w .github/workflows/ci.yml.
4. Dopisz do .cursor/rules/10-reguly.mdc zasadę nazewnictwa katalogów — brzmienie w sekcji 4 specu.
5. Sprawdź, że strona /reguly nadal pokazuje SEM-001, a nie sem_001. Identyfikator wyświetlany
   pochodzi z pola id dekoratora i nie powinien się zmienić — ale zobacz to na własne oczy,
   podnosząc stronę.

Pokaż mi liczbę plików w wyniku mypy. Musi być 35, nie 14.
```

**Ukończone, gdy:** `mypy --strict src/` bez wykluczeń, 35 plików, zero błędów; 137 testów;
`/reguly` pokazuje identyfikatory wyświetlane.

---

## Defekt B — mylące zastrzeżenie na kwotach

Najtrudniejszy defekt w tej liście. Jedyny, który dotyka poprawności merytorycznej.

```
Przeczytaj CAŁĄ sekcję 2 @docs/spec/2026-08-12-poprawki-design.md — dowody, przyczynę,
zweryfikowane listy typów i cztery zmiany. Wszystkie listy w sekcji 2.3 są sprawdzone
w korpus/schema/; NIE zgaduj ich ponownie i nie skracaj.

KROK 0 — zobacz defekt na własne oczy, zanim cokolwiek zmienisz.

Napisz jednorazowy skrypt, który bierze korpus/zloty/fa3-przyklad-01.xml, podmienia pole
i woła fa3check.walidacja.zwaliduj, wypisując wpis + co + dlaczego + cytat. Uruchom dla:
  P_11 = 1234.567     (oczekiwane dziś: DWA zastrzeżenia, drugie o „identyfikatorze")
  P_1  = 2026-13-45   (oczekiwane dziś: XSD-kwota-zapis o „separatorze tysięcy" — na DACIE)
Pokaż mi oba wyniki. To jest stan wyjściowy i punkt odniesienia.

KROK 1 — zawęź XSD-kwota-zapis i dodaj mu drugi kod błędu.

W tlumaczenia/XSD-kwota-zapis/tlumaczenie.py zamień `klucz=` na `klucze=` z SZEŚCIU kluczy:
dwa kody błędu (SCHEMAV_CVC_DATATYPE_VALID_1_2_1 i SCHEMAV_CVC_PATTERN_VALID) razy trzy typy
kwotowe (TKwotowy, TKwotowy2, TIlosci). Gotowy blok jest w sekcji 2.4, zmiana 1 — przepisz go.

Cytat i treść ZOSTAWIAMY bez zmian — są poprawne dla kwot.

Uruchom test z KROKU 0. Oczekiwane: P_1 = 2026-13-45 przestaje trafiać do XSD-kwota-zapis.

KROK 2 — zawęź XSD-wzorzec do identyfikatorów podatkowych.

Trzy klucze: SCHEMAV_CVC_PATTERN_VALID razy TNrNIP, TNIPIdWew, TNrVatUE. Blok w sekcji 2.4,
zmiana 2.

Usuń z co() gałąź ogólną — po zawężeniu jest martwa. dlaczego() zostaje, bo teraz mówi prawdę
bezwarunkowo. Cytat pkt 10 zostaje, bo jest trafny dla wszystkich trzech typów.

UWAGA: TNrPESEL, TNrREGON, TNrKRS i TNumerKSeF NIE wchodzą tutaj — nie są numerami
identyfikacji podatkowej, więc cytat pkt 10 byłby dla nich nadużyciem.

KROK 3 — dodaj gałąź schematową do test_zrodla.py. ZRÓB TO PRZED KROKIEM 4.

test_zrodla.py rozstrzyga źródło po nazwie dokumentu. Nazwa „schemat_FA(3)_v1-0E.xsd" zawiera
„fa(3)", więc wpadłaby do gałęzi broszury i test by PADŁ. Dodaj gałąź PRZED istniejącymi:
jeśli dokument kończy się na .xsd, sprawdzaj dosłowność wobec połączonej treści plików
z korpus/schema/ po normalizacji białych znaków; strona jest wtedy None.

KROK 4 — nowy wpis ogólny tlumaczenia/xsd_typ_schemat/.

Dwa klucze BEZ typ_xsd: DATATYPE_VALID_1_2_1 i PATTERN_VALID. Dzięki temu punktacja wynosi 1
i wpis przegrywa z zawężonymi z kroków 1 i 2 — to jest zamierzone.

Zrodlo cytuje SCHEMAT, nie broszurę, bo w broszurze nie ma odpowiedniego zdania (sprawdzone).
Gotowy blok Zrodlo w sekcji 2.4, zmiana 3. Cytat targetNamespace występuje w pliku dosłownie.

Treść MUSI być neutralna: nazwa pola, wartość, nazwa typu z blad.typ_xsd i zdanie, że wartość
nie spełnia ograniczenia zadeklarowanego dla tego typu w schemacie. Zakazane słowa: „liczba",
„separator", „tysięcy", „przecinek", „identyfikator", „data". Wpis obsługuje jedenaście rodzin
naraz i nie wolno mu zakładać żadnej.

Nie zapomnij o fixtures/wywoluje.xml — rejestracja bez niego podnosi WpisBezZrodla. Użyj pola
Email z niepoprawną wartością.

KROK 5 — odszumienie duplikatów w walidacja.py.

Scal zastrzeżenia o tym samym (xpath, linia), zostawiając jedno według jawnej kolejności
szczegółowości kodu podanej w sekcji 2.4, zmiana 4. Identyfikatory odrzuconych dopisz
do diagnostyka.

KROK 6 — bariera przed powtórzeniem defektu.

Dopisz do test_wyjasnienia.py: dla każdego tłumaczenia, którego treść zawiera słowo z listy
rodzin (liczb, kwot, separator, identyfikator, data, NIP), WSZYSTKIE jego klucze muszą mieć
niepuste typ_xsd. To mechaniczna bariera; bez niej ten defekt wróci w trzecim miejscu.

Dopisz też zasadę do .cursor/rules/10-reguly.mdc — brzmienie w sekcji 2.2 specu.

KROK 7 — odbiór.

Uruchom tabelę z sekcji 2.5 punkt po punkcie i pokaż mi wynik dla KAŻDEGO wiersza: siedem
przypadków wejściowych plus złoty korpus. Potem pełna weryfikacja: ruff, mypy --strict,
pytest -q (co najmniej 137 zielonych).

Na koniec odpowiedz wprost: czy osłabiłeś jakikolwiek test albo dopisałeś jakikolwiek wyjątek
do listy dozwolonych, żeby coś przeszło?
```

**Ukończone, gdy:** `P_11 = 1234.567` daje dokładnie jedno zastrzeżenie o precyzji; żadne
zastrzeżenie dla kwoty nie zawiera słowa „identyfikator"; `test_zrodla.py` zielony dla nowych wpisów.

---

## Defekt C — zawężenie niezmiennika parsowania

```
Sekcja 3 specu poprawek.

test_niezmienniki.py ma dozwolone_parse = {"safexml.py", "schema.py", "struktura.py"} — do listy
wyjątków dopisano pliki, które regułę łamią, więc test nie może zapłonąć. To osłabienie testu,
ale przyczyną był zbyt absolutny niezmiennik w specu z 11 sierpnia: nie rozróżniał niezaufanego
wejścia od zaufanych, wendorowanych plików schematu.

1. Zmień brzmienie niezmiennika w .cursor/rules/00-projekt.mdc i AGENTS.md na wersję ze sekcji 3
   specu poprawek: niezaufane wejście wyłącznie przez safexml.sparsuj(); pliki z korpus/schema/
   wolno parsować w schema.py i struktura.py, ale zawsze parserem zahartowanym.

2. Dodaj wspólną funkcję _parser_schematu() i użyj jej we WSZYSTKICH wywołaniach parsujących
   schemat — obecnie schema.py:23 ma flagi, a schema.py:40 i struktura.py:62 parsują gołym
   parserem. Jedna funkcja, żeby nie dało się jej pominąć.

3. Przepisz test_niezmienniki.py: BEZ listy wyjątków plików. Sprawdzaj regułę realną — każde
   wywołanie etree.parse / etree.fromstring poza safexml.py musi przekazywać argument parser=.
   Analiza AST, sprawdzenie obecności słowa kluczowego w wywołaniu.

4. Usuń test_lxml_tylko_w_safexml() — to jednolinijkowe opakowanie na inny test, które podwaja
   licznik bez dodawania sprawdzenia.

5. UDOWODNIJ, że nowy test działa: usuń tymczasowo parser= z jednego wywołania, pokaż mi czerwony
   test, przywróć. Test, którego nie widziałeś czerwonego, nie jest testem.
```

**Ukończone, gdy:** `test_niezmienniki.py` bez listy wyjątków plików, udowodniony jako czerwony
po usunięciu `parser=`.

---

## Defekt E — koniec szumu na poprawnych fakturach

```
Sekcja 5 specu poprawek.

Wszystkie 26 faktur MF dają dokładnie dwa zastrzeżenia: TEC-006 (ostrzeżenie) i TEC-007
(informacja) — o dwóch rzeczach, których z jednego pliku nie da się rozstrzygnąć. Zero BLAD,
więc bramka przechodzi, ale użytkownik z bezbłędną fakturą zawsze widzi dwie pozycje. Po trzeciej
fakturze przestaje czytać listę.

1. Dodaj do metadanych reguły pole rozstrzygalna_offline: bool = True. TEC-006 i TEC-007 dostają
   False. Znacznik strukturalny, nie rozpoznawanie po treści.

2. Wynik rozdziela wyniki: zastrzezenia (rozstrzygnięte) i uwagi_offline (nierozstrzygalne).

3. Strona pokazuje uwagi_offline w osobnym, ZWINIĘTYM panelu „Czego nie sprawdzamy offline" —
   nie na liście zastrzeżeń. Panel zostaje widoczny także przy czystej fakturze, bo ta informacja
   jest wartościowa; nie jest tylko zastrzeżeniem.

4. Zaostrz test_zloty_korpus.py: 26 faktur MF daje ZERO pozycji w zastrzezenia, niezależnie
   od wagi. To zysk uboczny wart więcej niż samo odszumienie — bramka przestaje przepuszczać
   ostrzeżenia i informacje.

Podnieś stronę i pokaż mi wynik dla poprawnej faktury MF. Chcę zobaczyć puste zastrzeżenia
i panel offline z dwiema pozycjami.
```

**Ukończone, gdy:** poprawna faktura MF daje puste `zastrzezenia`; zaostrzony test złotego korpusu
przechodzi.

---

## Defekt F — próg pokrycia z egzekucją

```
Sekcja 6 specu poprawek.

Pokrycie jest 87%, spec wymagał 90%, a fail_under nie jest ustawione — próg nigdy nie był
egzekwowany. To błąd specu: podał liczbę bez mechanizmu.

Wybierz jeden wariant i UZASADNIJ wybór:

Wariant 1 (zalecany): dociągnij pokrycie do 90% i włącz fail_under = 90 w [tool.coverage.report].
Najtańsze punkty: walidacja.py (80%), schema.py (83%), web/__main__.py (0%).

Wariant 2: obniż próg do faktycznych 87% i dopisz do specu, dlaczego — na przykład że
web/__main__.py to punkt wejścia bez logiki. Uczciwy niższy próg jest lepszy od wysokiego
i pozornego.

Potem UDOWODNIJ, że próg działa: obniż go o dwa punkty, pokaż mi że CI przechodzi, podnieś
z powrotem, pokaż że pada przy niższym pokryciu.
```

**Ukończone, gdy:** CI pada przy pokryciu poniżej progu, udowodnione eksperymentem.

---

## Drobne — jednym czatem

```
Sekcja 7 specu poprawek.

1. docs/reguly-z-broszury.md ma 16 kandydatów SEM, a zaimplementowane są SEM-001, SEM-004,
   SEM-005, SEM-006. Jeśli SEM-002 i SEM-003 są odłożone, napisz to wprost w tabeli pokrycia
   w README — luka bez wyjaśnienia wygląda na przeoczenie. Jeśli zostały porzucone z powodu
   pytania kwalifikującego (XSD to łapie), napisz i to.

2. Dodaj odznakę CI do README — dopiero teraz, po naprawieniu defektu A.

3. W repozytorium profilu (Iakirmon/Iakirmon) słowo „Demo" prowadzi do strony ze zrzutami ekranu,
   nie do działającego narzędzia. Zmień na „opis i zrzuty ekranu". To osobne repo, więc zrób to
   ręcznie albo powiedz mi, że mam przygotować treść.
```

---

## Prompt kontrolny — po wszystkich defektach

```
Przejrzyj repozytorium pod kątem defektów z @docs/spec/2026-08-12-poprawki-design.md.
Dla każdego z sześciu podaj dowód, że jest zamknięty — wynik polecenia, nie deklarację:

A. ruff check . oraz ruff format --check . — czysto
B. walidacja kwoty z trzema miejscami po kropce — dokładnie jedno zastrzeżenie, bez słowa
   „identyfikator"; wypisz wszystkie trzy nowe wpisy z ich cytatami i stronami
C. grep na etree.parse i etree.fromstring w src/ — każde wywołanie poza safexml.py z parser=;
   test_niezmienniki.py bez listy wyjątków plików
D. mypy --strict src/ — liczba plików (musi być 35) i zero błędów
E. walidacja poprawnej faktury MF — puste zastrzezenia, dwie pozycje w uwagi_offline
F. pokrycie i fail_under w pyproject.toml

Potem uruchom /audyt-zrodel i pokaż wynik dziesięciu punktów.

Na koniec: czy w trakcie tych poprawek osłabiłeś jakikolwiek test albo dopisałeś jakikolwiek
wyjątek do listy dozwolonych? Jeśli tak, wymień to wprost — defekt C powstał dokładnie tak
i nie chcę go powtórzyć w innym miejscu.
```

Ostatnie pytanie jest najważniejsze w tym prompcie. Zadaj je także po defektach B i C.
