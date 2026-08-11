# fa3-check — prompty dla Cursora

**Wersja 2** — zgodna ze specem po weryfikacji eksperymentalnej. Numeracja etapów zmieniła się
względem wersji 1: korpus jest teraz etapem zerowym.

Każdy etap to jeden nowy czat. Prompty są też dostępne jako skille — `/etap 3` robi to samo,
co wklejenie promptu etapu 3.

---

## Jak to prowadzić

**Nowy czat na każdy etap.** Kontekst się zapycha, a pierwszym objawem jest to, że agent
przestaje wypełniać `Zrodlo.cytat`.

**Do każdego promptu dołącz spec:** `@docs/spec/2026-08-11-fa3-check-design.md`

**Przeczytaj sekcję 3 specu, zanim zaczniesz cokolwiek.** Zawiera dwanaście faktów sprawdzonych
eksperymentalnie, z których trzy przewracają rzeczy „oczywiste". Agent, który ich nie zna,
popełni te same błędy.

**Po każdym etapie sam uruchom weryfikację:**

```
ruff check . ; if ($?) { mypy --strict src/ } ; if ($?) { pytest -q }
```

**Trzy pytania kontrolne, które warto zadawać często:**

*„Czy XSD już to łapie?"* — chroni przed rejestrem duplikującym `lxml`.

*„Skąd wiesz, że ta reguła tak brzmi — podaj cytat i stronę."* — jeśli odpowiedź jest parafrazą,
wpis jest wymyślony. Od etapu 1 pilnuje tego `test_zrodla.py`.

*„Skąd wziąłeś tę nazwę typu XSD?"* — musi być odczytana z `korpus/schema/`. Ja sam wpisałem
w wersji 1 specu `TKwota2` i `TData`, a FA(3) używa `TKwotowy` i `TDataT`.

---

## Etap 0 — korpus i środowisko

```
Przeczytaj @docs/spec/2026-08-11-fa3-check-design.md, szczególnie sekcje 2 i 3.
Realizujemy etap 0 z sekcji 16. W tym etapie NIE piszemy kodu walidatora.

1. pyproject.toml — pakiet fa3check, layout src/, Python >=3.12. Zależności produkcyjne:
   lxml (wersja PRZYPIĘTA DOKŁADNIE, nie zakresem), fastapi, uvicorn, jinja2,
   python-multipart. Deweloperskie: pytest, pytest-cov, hypothesis, httpx, ruff, mypy,
   lxml-stubs.

   lxml-stubs jest obowiązkowy — bez niego mypy --strict nie przejdzie, bo lxml nie ma
   typów wbudowanych. To błąd, który zablokuje CI w pierwszej godzinie.

2. LICENSE (MIT), .gitignore, .gitattributes zgodnie z sekcją 13.1 specu.

   .gitattributes nie jest kosmetyką: reguły TEC-001 i TEC-002 działają na bajtach, więc
   normalizacja końców linii w fixture'ach dałaby inny wynik na Windowsie i w CI.

3. .github/workflows/ci.yml zgodnie z sekcją 15 — macierz 3.12, 3.13, 3.14.

4. scripts/pobierz_korpus.py. Pobiera do korpus/:
   - schemat_FA(3)_v1-0E.xsd oraz bazowe/ElementarneTypyDanych, KodyKrajow, StrukturyDanych
     (zachowaj strukturę katalogów, bo schemat importuje je ścieżkami relatywnymi),
   - archiwum z 26 przykładowymi fakturami,
   - broszurę informacyjną FA(3) (PDF),
   - faktury/weryfikacja-faktury.md z repozytorium CIRFMF/ksef-docs do korpus/zrodla/.
   URL-e są w @docs/zrodla.md. Nie wymyślaj ich.

   Ostatni plik jest potrzebny, bo test_zrodla.py sprawdza dosłowność cytatu wobec pliku
   źródłowego. Bez wendorowania reguły TECHNICZNA wymykałyby się temu sprawdzeniu, a to
   właśnie one dotyczą rzeczy, które łatwo wpisać z pamięci.

   PUŁAPKA, sprawdzona: numer przykładu jest na KOŃCU nazwy pliku, a nazwa zawiera cyfrę
   wcześniej — FA_3_Przykład_12.xml. Naiwne re.search(r"(\d+)", stem) łapie 3 z FA_3
   i wszystkie 26 plików nadpisuje się na jeden. Użyj re.search(r"(\d+)\s*$", stem).
   Dodatkowo wielkość liter jest niespójna: w archiwum są i FA_3, i Fa_3.
   Normalizuj do fa3-przyklad-01.xml … fa3-przyklad-26.xml.

   Broszura: pdftotext -layout -enc UTF-8 wejscie.pdf korpus/broszura/broszura-fa3.txt
   Flaga -enc UTF-8 jest OBOWIĄZKOWA — bez niej polskie znaki są zepsute i test_zrodla
   nigdy nie znajdzie żadnego cytatu. Potem podmień znak wysuwu strony (\f) na wiersz
   "=== strona N ===", numerując fizycznie od 1. Numer fizyczny równa się nadrukowanemu —
   sprawdzone na 172 stopkach, nie kombinuj z przesunięciem.

   PDF nie jest commitowany (3,3 MB) — do .gitignore. Wyciąg tekstowy JEST commitowany.

5. korpus/PROVENANCE.md — dla każdego pliku: URL, data pobrania, nazwa pierwotna, SHA-256.
   Dla broszury dodatkowo dokładne polecenie konwersji.

Na koniec pokaż mi:
- listę 26 plików po normalizacji,
- wynik `grep -c "=== strona" korpus/broszura/broszura-fa3.txt`,
- wynik `grep -A 3 "=== strona 6 ===" | head -20` — chcę zobaczyć polskie znaki na własne oczy,
- czy w wyciągu występuje dosłownie fraza "Kwoty podawane są co do zasady z dokładnością do
  2 miejsc po kropce". Jeśli nie występuje, konwersja jest zepsuta i nie idziemy dalej.
```

**Ukończone, gdy:** 26 plików, wyciąg z polskimi znakami, cytat ze strony 6 odnaleziony.

---

## Etap 1 — szkielet, rejestry, pierwsza reguła

```
Etap 1 z sekcji 16 specu.

1. src/fa3check/typy.py zgodnie z sekcją 8.1 — Poziom, Waga, Zrodlo, BladSchematu, KluczBledu,
   Zastrzezenie, Wynik (z polem czesciowy), hierarchia Fa3Error.

2. src/fa3check/rejestr.py zgodnie z 8.2. Rejestracja MUSI podnieść WpisBezZrodla przy:
   duplikacie ID, braku zrodlo, pustym zrodlo.cytat, braku wymaganego fixture'a.

3. src/fa3check/safexml.py zgodnie z 8.3. Kolejność sprawdzeń ma znaczenie:
   rozmiar (3 MB) PRZED parsowaniem, potem BOM i kodowanie, potem DOCTYPE, potem instrukcje
   przetwarzania, na końcu parser z flagami ze specu.

   DOCTYPE odrzucamy wprost i to jest decyzja z uzasadnieniem: sprawdziłem, że przy
   resolve_entities=False XXE nie wycieka, ALE dokument przechodzi walidację bez błędu.
   Faktura KSeF nie ma powodu mieć DOCTYPE, więc odrzucenie czyni XXE niemożliwym
   strukturalnie, zamiast tylko nieszkodliwym.

   Wykrywaj przez drzewo.docinfo.doctype — sprawdziłem, zwraca '<!DOCTYPE Faktura>'.
   Parsowanie przed tym sprawdzeniem jest bezpieczne, bo encje nie są rozwijane, więc nie
   kombinuj z wyszukiwaniem w surowych bajtach.

   Własnego limitu głębokości NIE dodawaj — libxml2 odrzuca przy 256 poziomach.

4. src/fa3check/faktura.py zgodnie z 8.7. dec() zwraca None przy wartości nieparsowalnej
   i NIGDY nie podnosi wyjątku.

5. src/fa3check/reguly/SEM-001/ — pierwsza reguła. Pełny cytat i uzasadnienie w sekcji 9.2
   specu, wzorzec w .cursor/rules/10-reguly.mdc. Fixture'y zbuduj na prawdziwej fakturze
   z korpus/zloty/, jedną zmianą: przenieś NIP nabywcy z pola NIP do NrVatUE.

6. Testy: test_rejestr.py, test_reguly.py, test_wyjasnienia.py, test_safexml.py oraz dwa
   nowe, które niosą ten projekt:

   test_zrodla.py — dla każdego wpisu, którego źródłem jest broszura, sprawdza że
   zrodlo.cytat WYSTĘPUJE DOSŁOWNIE w korpus/broszura/broszura-fa3.txt po normalizacji
   białych znaków (re.sub(r"\s+", " ")) ORAZ że zrodlo.strona wskazuje stronę, na której
   cytat się znajduje. Sprawdziłem wykonalność: 6 z 6 cytatów odnalezione na oczekiwanych
   stronach, więc jeśli u Ciebie nie działa, zepsuty jest wyciąg albo cytat.

   test_niezmienniki.py — analizą AST (moduł ast, bez zewnętrznych zależności):
   - lxml importowany WYŁĄCZNIE w safexml.py,
   - reguly/ i tlumaczenia/ nie importują web, schema, walidacja, safexml,
   - brak float w adnotacjach w reguly/,
   - brak open(, requests, httpx, datetime.now, time.time, random w obu rejestrach.

   test_reguly.py sprawdza RÓŻNICOWO: zbiór zastrzeżeń z lamie.xml minus zbiór
   z przechodzi.xml równa się dokładnie tej jednej regule. Nie "dokładnie jedno
   zastrzeżenie" — to by wymuszało sztuczne fixture'y i przestałoby działać przy 40 regułach.

TDD: najpierw testy, uruchom, pokaż mi czerwone, potem implementacja.

Nie pisz jeszcze schema.py, struktura.py, tlumaczenia.py, walidacja.py ani web/.
```

**Ukończone, gdy:** CI zielone, rejestr odrzuca wpis bez cytatu, `test_zrodla.py` potwierdza
cytat `SEM-001` na stronie 6.

---

## Etap 2 — schemat, mapa typów, walidacja

```
Etap 2 z sekcji 16 specu: src/fa3check/schema.py, walidacja.py, test_zloty_korpus.py.

Sedno tego etapu jest w sekcji 8.4 i jest nieoczywiste. error.path z lxml NIE zawiera nazw
elementów — zwraca ścieżkę pozycyjną, np. /*/*[4]/*[15]/*[7]. Nazwa elementu jest tylko
w treści komunikatu, czyli tam, gdzie zaglądać nie wolno.

Mechanizm, który to obchodzi i który sprawdziłem na 8 klasach błędów:
1. error.path jest poprawnym wyrażeniem XPath,
2. wykonaj je na dokumencie -> węzeł,
3. etree.QName(wezel).localname -> nazwa elementu,
4. mapa_typow()[nazwa] -> nazwa typu XSD.

mapa_typow() buduj ze WSZYSTKICH plików w korpus/schema/, po atrybucie type deklaracji
xsd:element. Wyjdzie około 250 wpisów, z czego 7 niejednoznacznych — wszystkie to typy
złożone (DaneIdentyfikacyjne, OsobaFizyczna, AdresPol...), więc dla błędów wartości mapa
jest jednoznaczna. Przy niejednoznaczności zostaw typ_xsd = None.

Wypisz mi tę mapę dla P_15, P_11, P_9A, P_1, NIP, Nazwa, KursWaluty. Spodziewam się
TKwotowy, TKwotowy, TKwotowy2, TDataT, TNrNIP, TZnakowy512, TIlosci. Jeśli wyjdzie inaczej,
schemat się zmienił i trzeba to zgłosić, a nie obejść.

walidacja.py zgodnie z 8.8. Pierwsze i zwarciowe jest SPRAWDZENIE KORZENIA: gdy korzeń nie
jest Faktura w przestrzeni .../13775/, zwracamy jedno czytelne zastrzeżenie i kończymy, bez
uruchamiania schematu i reguł.

Sprawdziłem, dlaczego to konieczne: wklejenie strony HTML albo faktury bez atrybutu xmlns daje
jeden błąd SCHEMAV_CVC_ELT_1 z komunikatem "No matching global declaration available for the
validation root", który dla użytkownika nie znaczy nic. A to najczęstszy błąd początkujących —
bez tego sprawdzenia dajemy w najczęstszym przypadku najgorszy możliwy komunikat.

UWAGA na drugą zmianę względem intuicji: XSD NIE jest bramką.
Reguły semantyczne i arytmetyczne lecą także wtedy, gdy schemat odrzucił dokument —
ustawiamy tylko Wynik.czesciowy = True. Powód: użytkownik z jednym błędem formatu
i pięcioma semantycznymi ma prawo zobaczyć sześć, nie jeden.

Sortowanie zastrzeżeń deterministyczne: waga, linia, identyfikator wpisu.

test_zloty_korpus.py — parametryzowany po 26 plikach. Sprawdziłem: wszystkie 26 przechodzą
XSD, więc jeśli któryś nie przechodzi, zepsuty jest kod, nie faktura. Pokaż mi wynik plik
po pliku.
```

**Ukończone, gdy:** 26/26 zgodnych z XSD i zero zastrzeżeń `BLAD`; element i typ ustalane bez
czytania komunikatu.

---

## Etap 3 — struktura i słownik tłumaczeń

```
Etap 3 z sekcji 16 specu: struktura.py, tlumaczenia.py, siedem wpisów z tabeli 9.1.

Najpierw struktura.py (sekcja 8.6), bo od niego zależy najtrudniejsze tłumaczenie. Przeczytaj
tę sekcję dokładnie — jest tam ostrzeżenie opłacone nieudaną próbą.

Sprawdziłem, że SCHEMAV_ELEMENT_CONTENT obsługuje TRZY różne problemy — brak wymaganego
elementu, element nadmiarowy i zaburzoną kolejność — a error.path wskazuje SĄSIADA, nie
winowajcę: po usunięciu P_2 ścieżka wskazała P_6.

PUŁAPKA, w którą sam wpadłem: naiwne complexType.iter(xsd:element) zwraca dla Fa 222
deklaracje, bo schodzi przez całe zagnieżdżone drzewo, a prawdziwa Fa ma 19 dzieci. Na takiej
liście "brakujące" wskazałoby dwieście pól. Musisz przejść WYŁĄCZNIE bezpośrednie cząstki
typu złożonego: dzieci xsd:sequence i xsd:choice na pierwszym poziomie, czytając minOccurs,
bez wchodzenia w zagnieżdżone typy.

DRUGA PUŁAPKA, też sprawdzona: element jest wymagany tylko wtedy, gdy on I KAŻDA GRUPA NAD NIM
ma minOccurs>=1. Bez propagacji opcjonalności grup Fa daje 7 fałszywych "brakujących"
(P_13_2, P_14_2, P_13_4, P_14_4, P_13_5, DaneFaKorygowanej, P_15ZK) — wszystkie mają domyślne
minOccurs=1, ale leżą w zagnieżdżonych grupach opcjonalnych.

KRYTERIUM AKCEPTACJI jest mechaniczne: brakujace MUSI być puste dla wszystkich 26 faktur
złotego korpusu i każdego typu w nich występującego. To jest test, który wyłapał tamte siedem.

Kolejność: orzekaj dla elementów spoza gałęzi choice. NIE wyciszaj kolejności tylko dlatego,
że typ zawiera choice — sprawdziłem, Fa ma choice, a kolejność wykrywa się poprawnie.

Jeśli propagacja opcjonalności okaże się trudniejsza, niż wygląda, wypuść struktura.py BEZ
brakujace — nadmiarowe i przestawione są sprawdzone i już wystarczą. Powiedz mi, jeśli
z tego korzystasz.

Potem tlumaczenia.py (8.5). Dopasowanie po KluczBledu, po szczegółowości:
element bije typ_xsd, typ_xsd bije typ_lxml. NIGDY po treści komunikatu.

Osiem wpisów z tabeli 9.1. Kody typ_lxml w tej tabeli wywołałem eksperymentalnie, są
prawdziwe. Trzy rzeczy, które zaskakują i są w tabeli:
- XSD-korzen (SCHEMAV_CVC_ELT_1) wygląda banalnie, a jest najwartościowszy: zgubiony xmlns
  to najczęstszy błąd początkujących. W większości przypadków wyprzedzi go sprawdzenie
  korzenia z etapu 2, ale tłumaczenie musi istnieć dla niezgodności leżących głębiej,
- kwota ze spacją tysięcy daje SCHEMAV_CVC_DATATYPE_VALID_1_2_1, NIE PATTERN_VALID, bo ze
  spacją nie jest nawet liczbą i odpada na typie bazowym,
- ten sam typ pola ma różne limity precyzji: TKwotowy 2 miejsca, TIlosci 6, TKwotowy2 8.
  W wyjaśnieniu podaj limit właściwy dla typu, nie ogólny.

Granice bierz ZE SCHEMATU w korpus/schema/. TDataT ma zakres 2006-01-01 do 2050-01-01 —
to niespodzianka warta nazwania wprost w wyjaśnieniu.

Tłumaczenia mają zawsze wagę BLAD, więc nie dodawaj pola waga do ich metadanych.

test_tlumaczenia.py:
- każdy fixture wywoluje.xml produkuje dopasowany błąd,
- PO WYZEROWANIU pola komunikat we wszystkich błędach dopasowanie NADAL DZIAŁA — uruchom
  ten test i pokaż wynik, to on pilnuje niezmiennika,
- żaden błąd z fixture'ów ani ze złotego korpusu nie wpada w XSD-zapasowe.

test_struktura.py — wzorce policzone ręcznie dla czterech przypadków: brak wymaganego,
element nadmiarowy, przestawiona kolejność, kombinacja dwóch.

Na koniec pokaż mi wynik dla faktury z trzema różnymi błędami XSD — chcę trzy sensowne
wyjaśnienia obok siebie.
```

**Ukończone, gdy:** test z wyzerowanym komunikatem zielony, zero trafień w `XSD-zapasowe`,
`struktura.porownaj()` poprawnie wskazuje brakujące i przestawione pola.

---

## Etap 4 — reguły techniczne

```
Etap 4 z sekcji 16 specu: reguły TEC-001 do TEC-007 z tabeli 9.2.
Źródło: faktury/weryfikacja-faktury.md, odnośnik w @docs/zrodla.md.

TEC-001 do TEC-004 działają na surowych bajtach — używaj f.surowe_bajty(); w regułach innych
poziomów to wywołanie jest zabronione.

TEC-004 sam rozstrzyga, który limit stosuje: 1 MB bez załącznika, 3 MB gdy w dokumencie jest
element Zalacznik. Nie hardkoduj jednego.

TEC-005 to dowód sensu drugiego rejestru. Napisz fixture, w którym NIP ma POPRAWNY wzorzec
TNrNIP i BŁĘDNĄ sumę kontrolną — i pokaż mi, że XSD go przyjmuje, a TEC-005 odrzuca.
Bez tego dowodu etap nie jest ukończony.

Waga BLAD jest tu bezpieczna, bo sprawdziłem: w 26 fakturach MF jest 64 NIP-y i każdy ma
poprawną sumę kontrolną. Gdyby choć jeden był fikcyjny, ta reguła łamałaby bramkę złotego
korpusu i trzeba by ją zdegradować do OSTRZEZENIE. Jeśli u Ciebie złoty korpus zapłonie na
TEC-005, to zepsuta jest implementacja sumy kontrolnej, nie korpus.

Wagi: TEC-006 to OSTRZEZENIE, TEC-007 to INFORMACJA. Nie podnoś ich do BLAD — powody
są w sekcji 11 specu. Reguła nierozstrzygalna offline nie może krzyczeć, ale nie może
też zniknąć.

Rób po jednej: test czerwony, implementacja, zielony, złoty korpus, następna.
```

**Ukończone, gdy:** złoty korpus czysty, `TEC-005` udowodniony przypadkiem, który XSD
przepuszcza.

---

## Etap 5 — warstwa webowa i hartowanie

```
Etap 5 z sekcji 16 specu: web/, korpus/zlosliwe/, hartowanie, test_web.py, test_fuzz.py.

Web i hartowanie są w jednym etapie celowo — rozdzielenie dawało okno, w którym istnieje
strona bez limitów, a wystawić jej i tak nie wolno przed hartowaniem.

FastAPI + Jinja2 + HTMX, htmx.min.js wendorowany do static/, nie z CDN.
Trasy: GET /, POST /waliduj, GET /reguly, GET /zdrowie.

Wynik: przy Wynik.czesciowy WYRAŹNIE powiedz użytkownikowi, że schemat odrzucił dokument
i część sprawdzeń mogła nie mieć danych. Zastrzeżenia pogrupowane po wadze, zwinięte
do wiersza, rozwijalne do pięciu części z cytatem. Surowy komunikat lxml tylko
pod "szczegółami technicznymi".

GET /reguly — reguły ORAZ tłumaczenia, ze źródłami, cytatami i stronami, z filtrowaniem
po poziomie. Ta strona pozwala sprawdzić nas bez czytania kodu.

Zasady z sekcji 13 od pierwszej linii kodu:
- limit ciała 3 MB (NIE 1 MB — inaczej odrzucasz legalną fakturę z załącznikiem),
- w logach tylko znacznik czasu, rozmiar, liczba zastrzeżeń, czas. Nigdy NIP, numer faktury
  ani fragment XML-a — dotyczy to też logger.exception, bo wyjątki lxml noszą treść węzła,
- autoescape Jinja2 włączony, |safe zakazane w szablonach wyniku,
- nagłówki: CSP bez unsafe-inline dla skryptów, nosniff, no-referrer,
- ogranicznik liczby żądań pisany ręcznie, bez nowej zależności.

korpus/zlosliwe/ i test_safexml.py — UWAGA, oczekiwanie RÓŻNI SIĘ między wektorami
i tabela jest w sekcji 13 specu. Sprawdziłem to i naiwny test "każdy atak rzuca wyjątek"
NIE PRZEJDZIE:
- bomba entyfikacyjna: wyjątek (libxml2 zgłasza przekroczenie amplifikacji),
- zagnieżdżenie 10 000 poziomów: wyjątek (limit 256 w libxml2),
- XXE: wyjątek z powodu zakazu DOCTYPE. Dopisz DRUGI test, który tymczasowo zdejmuje ten
  zakaz i sprawdza, że treść pliku lokalnego i tak nie wycieka do tekstu dokumentu —
  to udowadnia, że mamy dwie niezależne warstwy obrony, nie jedną.

test_web.py:
- żądanie ponad limit odrzucone PRZED parsowaniem,
- test logów: faktura z rozpoznawalnym NIP-em, przechwyć logi, poszukaj NIP-u. Potem
  UDOWODNIJ, że test działa: dopisz tymczasowo logger.exception z surowym wyjątkiem lxml,
  pokaż mi czerwony test, usuń,
- test XSS: wstaw <script>alert(1)</script> w pole tekstowe faktury i sprawdź, że
  w odpowiedzi nie ma nieescapowanego znacznika,
- ta sama odpowiedź przy powtórzeniu tego samego wejścia,
- walidacja całego złotego korpusu w budżecie czasu.

test_fuzz.py (Hypothesis):
- sparsuj() na losowych bajtach i na zmutowanych bajtach złotego korpusu nigdy nie podnosi
  nic poza Fa3Error i mieści się w limicie czasu,
- zwaliduj() zawsze zwraca Wynik i nigdy nie rzuca — to jedyny niezmiennik, który naprawdę
  ma znaczenie dla publicznego punktu wejścia.
```

**Ukończone, gdy:** strona działa, każdy wektor zachowuje się zgodnie z tabelą, test logów
udowodniony jako czerwony, fuzz zielony.

---

## Etap 6 — wyciąg reguł z broszury

```
Etap 6 z sekcji 16 specu. Etap DOKUMENTACYJNY, nie piszesz kodu.

Powstaje docs/reguly-z-broszury.md. Pracujesz na korpus/broszura/broszura-fa3.txt ze
znacznikami "=== strona N ===". Cytat bierzesz z pliku, numer strony z najbliższego
znacznika powyżej. Podział rozdziałów jest w @docs/zrodla.md.

Dla każdego kandydata:
- proponowany identyfikator (SEM-nnn albo ARY-nnn),
- jednozdaniowe brzmienie,
- DOSŁOWNY cytat, w cudzysłowie, skopiowany z pliku,
- numer strony,
- pola FA(3), których dotyczy,
- proponowaną wagę z uzasadnieniem według sekcji 10,
- czy rozstrzygalna offline,
- ODPOWIEDŹ NA PYTANIE KWALIFIKUJĄCE: czy XSD już to łapie?

Pytanie kwalifikujące wymaga zajrzenia do korpus/schema/. Jeśli schemat wymusza regułę
facetem — fractionDigits, maxLength, pattern, minInclusive, minOccurs, kolejność w sequence —
to NIE jest kandydat na regułę. Zapisz jako kandydata na TŁUMACZENIE i idź dalej.
Spodziewam się, że tak wypadnie większość rozdziału "Formaty pól" i to jest zamierzone.

Kolejność rozdziałów: Fa (42-85), FaWiersz (86-103), Platnosc (107-119), Podmiot1 (10-15),
Podmiot2 (16-24), Podmiot3 (25-36), reszta.

Czego nie wolno:
1. Nie wpisuj reguły bez cytatu. Od etapu 1 test_zrodla.py i tak ją odrzuci, więc oszczędź
   sobie pracy.
2. Nie orzekaj o obowiązkach ustawowych. Broszura mówi o polach "opcjonalny", że ich
   wypełnienie "nie jest wymagane dla poprawności semantycznej pliku" (s. 4).
3. Nie zaglądaj do listy reguł ksefuj po pomysły — wyciąg ma być niezależny, żeby
   porównanie pokrycia w etapie 8 coś znaczyło.

Po każdym rozdziale zatrzymaj się i pokaż wynik, z podziałem na kandydatów na reguły
i kandydatów na tłumaczenia. Nie rób 170 stron w jednym przebiegu.
```

**Ukończone, gdy:** kandydaci z rozdziałów `Fa` i `FaWiersz`, każdy z cytatem, stroną
i odpowiedzią na pytanie kwalifikujące.

---

## Etap 7 — reguły semantyczne i arytmetyczne

```
Etap 7 z sekcji 16 specu. Implementujemy JEDNĄ partię z docs/reguly-z-broszury.md.
Powiedz, którą bierzesz, i czekaj na potwierdzenie.

Dla każdej reguły: nowy katalog, dekorator, zrodlo.md, dwa fixture'y.

Cytat przenieś z docs/reguly-z-broszury.md — jest tam dosłowny. Nie przepisuj z pamięci
i nie skracaj, bo test_zrodla.py porównuje go z plikiem źródłowym.

Fixture lamie.xml MUSI przechodzić walidację XSD. Sprawdzaj to za każdym razem — to granica
między dwoma rejestrami. Jeśli nie przechodzi, sprawa należy do tlumaczenia/.

Reguły arytmetyczne: kwoty wyłącznie Decimal. Gdy dec() zwraca None, reguła MILCZY.

W zrodlo.md dopisz jedno zdanie: dlaczego XSD tego nie łapie. To pierwsza rzecz, którą
sprawdzi /audyt-zrodel.

Po każdej regule pytest, w tym złoty korpus. Po partii pokaż liczbę wpisów w rejestrach
z podziałem na poziomy.
```

**Ukończone, gdy:** partia gotowa, złoty korpus czysty, CI zielony. Powtarzasz dla kolejnych.

---

## Etap 8 — dopracowanie wyjaśnień

```
Etap 8 z sekcji 16 specu.

1. Przejdź WSZYSTKIE wpisy w obu rejestrach i przeczytaj co / dlaczego / jak_naprawic jak
   księgowy, który nie wie, co to XSD. Wypisz listę ogólnikowych. Nie poprawiaj jeszcze.

2. Osobno wypisz te, w których dlaczego PRZEWIDUJE reakcję KSeF. Zdania w rodzaju "KSeF
   odrzuci fakturę, bo sumy się nie zgadzają" są nieprawdziwe — system nie weryfikuje
   rachunkowej treści faktury.

3. Osobno wypisz te, w których do treści widzianej przez użytkownika przeciekł żargon:
   "atomic type", "facet", "XSD", "schema validation".

4. Rozszerz listę zwrotów zakazanych w tests/test_wyjasnienia.py o wszystko, co znalazłeś.

5. Popraw wyjaśnienia. Pole co musi zawierać liczby z konkretnej faktury. jak_naprawic musi
   mówić, co zrobić, i wskazać właściwe pole alternatywne, jeśli istnieje.

6. Tabela pokrycia do README: liczba wpisów w każdym rejestrze po poziomach, ile ma numer
   strony, ile rozstrzygalnych offline. Generowana z rejestrów, nie wpisana z ręki.

Na koniec porównaj pokrycie z listą kategorii ksefuj z @docs/zrodla.md — jako listę
kontrolną. Wypisz kategorie bez ani jednego wpisu i powiedz, czy to luka, czy świadomy brak
wynikający z tego, że XSD już to łapie.
```

**Ukończone, gdy:** lista zwrotów zakazanych urosła, tabela pokrycia generuje się z rejestrów.

---

## Etap 9 — README

```
Etap 9 z sekcji 16 specu: README.md po polsku.

1. Jedno zdanie czym to jest, potem PRZYKŁAD jednego pełnego wyjaśnienia — pięć części
   z cytatem. Weź SEM-001: faktura przejdzie KSeF, dostanie numer, a nabywca jej nie
   zobaczy. To wizytówka.
2. Tabela pokrycia z etapu 8, z podziałem na tłumaczenia i reguły.
3. Dlaczego dwa rejestry — sekcja 2 specu skrótowo. Że FA(3) to XML Schema 1.0 z pełnym
   zestawem facetów, więc formaty łapie sam, a poza nim zostaje arytmetyka, zależności
   między polami i sumy kontrolne.
4. Jak to jest sprawdzane — krótko o test_zrodla.py. Że cytat przy każdym wpisie jest
   weryfikowany maszynowo wobec wyciągu broszury, razem z numerem strony. To jest rzecz,
   której nie ma nikt inny, i warto powiedzieć wprost, że to bramka CI, nie obietnica.
5. Stan sztuki — sekcja 5 specu, uczciwie, razem z tym, w czym ksefuj jest lepszy:
   waliduje w przeglądarce, więc XML nigdy nie opuszcza komputera użytkownika.
6. Ograniczenia w dwie strony: zielony wynik NIE jest gwarancją przyjęcia przez KSeF
   (trzy reguły z sekcji 11), a przyjęcie przez KSeF NIE jest gwarancją poprawności faktury.
7. Prywatność i korpus złośliwych XML-i.
8. Uruchomienie: dwie komendy.
9. Jak dodać wpis — pytanie kwalifikujące, katalog, dekorator, fixture'y, cytat.
10. Źródła — odnośnik do docs/zrodla.md.

Punkty 4 i 6 są nieoczywiste i dlatego cenne: pierwszy pokazuje, że audytowalność jest
zmierzona, drugi że autor wie, gdzie jego narzędzie się kończy.

Bez emoji. Bez odznak poza CI i licencją. Bez "błyskawicznie szybki".
```

**Ukończone, gdy:** README otwiera się przykładem wyjaśnienia, a nie listą funkcji.

---

## Prompt kontrolny — po całości

```
Przejrzyj repo pod kątem niezmienników z .cursor/rules/00-projekt.mdc. Dla każdego podaj
konkretny dowód albo wskaż miejsce złamania.

Pokaż wynik grepa, nie deklarację:
1. czy reguly/ i tlumaczenia/ nie importują web, schema, walidacja, safexml,
2. czy lxml jest importowany wyłącznie w safexml.py,
3. czy dopasowanie tłumaczeń nigdzie nie opiera się na blad.komunikat,
4. czy nigdzie w kodzie liczącym kwoty nie ma float,
5. czy każdy wpis ma niepuste zrodlo.cytat i plik zrodlo.md,
6. czy w web/ nie ma logowania treści faktury, w tym logger.exception z surowym wyjątkiem,
7. czy w szablonach wyniku nie ma |safe,
8. czy nazwy typów XSD w tłumaczeniach zgadzają się z korpus/schema/ — sprawdź w pliku.

Punkty 2, 3 i 8 są najważniejsze: pierwszy to mechanizm bezpieczeństwa, drugi decyduje,
czy projekt przeżyje aktualizację lxml, trzeci wyłapie nazwy typów wpisane z pamięci.
Uwaga: test_niezmienniki.py sprawdza punkty 1-4 automatycznie — jeśli jest zielony,
a grep pokazuje naruszenie, to test jest zepsuty i to jest gorsza wiadomość.

Potem wypisz wszystko, co jest w repo, a nie ma uzasadnienia w specu. Szczególnie poszukaj
reguł duplikujących to, co łapie XSD.
```

Warto puścić też po etapach 5 i 7.
