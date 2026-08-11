# Źródła

Bibliografia dokumentów, na których stoi ten projekt. **Reguła walidacyjna, której nie da się
zaczepić w jednym z tych dokumentów, nie wchodzi do rejestru.**

Stan na 2026-08-11. Przy każdym dokumencie podana jest data wersji — ta sama, która trafia do
pola `Zrodlo.wersja` przy regule. Gdy MF wyda nowszą wersję, stare reguły nie stają się
automatycznie błędne, ale przestają być aktualne i to musi być widoczne.

---

## Rozstrzygające

### Schemat FA(3)

| | |
|---|---|
| Plik | `schemat_FA(3)_v1-0E.xsd` |
| Namespace | `http://crd.gov.pl/wzor/2025/06/25/13775/` |
| Wzór produkcyjny | <https://crd.gov.pl/wzor/2025/06/25/13775/> |
| Kopia z repozytorium MF | <https://github.com/CIRFMF/ksef-docs/blob/main/faktury/schemy/FA/schemat_FA(3)_v1-0E.xsd> |
| Schematy bazowe | `ElementarneTypyDanych_v10-0E.xsd`, `KodyKrajow_v10-0E.xsd`, `StrukturyDanych_v10-0E.xsd` |
| Obowiązuje | od 1 lutego 2026 r. dla wszystkich faktur ustrukturyzowanych |

Rzecz techniczna o konsekwencjach dla całej architektury, sprawdzona w plikach, nie założona.

To jest **XML Schema 1.0**: brak `xs:assert`, brak `xs:key`, `xs:keyref` i `xs:unique`. Schemat
nie ma czym wyrazić ani arytmetyki między polami, ani warunku „jeśli pole A wypełnione, to B jest
wymagane".

Ale **facetów używa w pełni**. Z `ElementarneTypyDanych_v10-0E.xsd`:

Typy, których FA(3) **faktycznie używa** — odczytane z plików, nie z pamięci:

| Typ | Facety | Używany m.in. w |
|---|---|---|
| `TKwotowy` | `decimal`, `totalDigits=18`, `fractionDigits=2` | `P_15`, `P_11` |
| `TKwotowy2` | `decimal`, `totalDigits=22`, `fractionDigits=8` | `P_9A`, `P_9B` |
| `TIlosci` | `decimal`, `totalDigits=22`, `fractionDigits=6` | `KursWaluty` |
| `TDataT` | `etd:TData`, `minInclusive=2006-01-01`, `maxInclusive=2050-01-01` | `P_1`, `P_6` |
| `TZnakowy512` | `token`, `minLength=1`, `maxLength=512` | `Nazwa` |
| `TNrNIP` | `string`, `pattern=[1-9]((\d[1-9])\|([1-9]\d))\d{7}` | `NIP` |

**Ostrzeżenie, opłacone błędem.** W schemacie bazowym istnieją też typy `TKwota2`
(`totalDigits=16`, `fractionDigits=2`) i `TData` (zakres 1900-01-01 … 2050-12-31), ale FA(3)
**nie używa ich do tych pól**. Pierwsza wersja specu wpisała je z pamięci i cała tabela
tłumaczeń miała błędne klucze oraz błędne granice w wyjaśnieniach. Nazwę typu zawsze czytaj
z `korpus/schema/`.

Obecne facety: `fractionDigits`, `totalDigits`, `maxLength`, `minLength`, `pattern`,
`minInclusive`, `maxInclusive`.

Z tego wynika najważniejsza decyzja projektu: **rozdział „Formaty pól (danych)" broszury (s. 4–6)
opisuje to, co schemat już wymusza.** Precyzja kwot, format daty, maksymalne długości pól, NIP
bez separatorów — wszystko to łapie `lxml` bez ani jednej linii naszego kodu. Dlatego reguła,
którą łapie XSD, nie jest u nas regułą, a tłumaczeniem: wartością nie jest wykrycie takiego
błędu, a zamiana komunikatu o „atomic type TKwotowy" w zdanie zrozumiałe dla księgowego.

Warto zauważyć, czego `TNrNIP` **nie** sprawdza: wzorzec weryfikuje kształt numeru — dziesięć
cyfr, pierwsza niezerowa, druga i trzecia nie obie zerowe — ale **nie sumę kontrolną**.
Wyrażenie regularne nie policzy modulo. To jest najczystszy przykład tego, po co istnieje drugi
rejestr, i dlatego reguła `TEC-005` ma powód istnienia, a reguła sprawdzająca liczbę cyfr — nie.

Plik `ElementarneTypyDanych_v10-0E.xsd` jest więc dokumentem, do którego wraca się przy każdym
nowym wpisie, żeby odpowiedzieć na pytanie kwalifikujące: *czy XSD już to łapie?*

### Broszura informacyjna FA(3)

| | |
|---|---|
| Tytuł | Faktura ustrukturyzowana. Broszura informacyjna dotycząca struktury logicznej FA(3) |
| Wydawca | Ministerstwo Finansów, Warszawa, marzec 2026 r. |
| Wersja | 2026-03-04 |
| Objętość | 170 stron |
| URL | <https://ksef.podatki.gov.pl/media/jknpcymf/broszura-informacyjna-dotyczaca-struktury-logicznej-fa-3-04032026.pdf> |
| Wersja angielska | <https://ksef.podatki.gov.pl/media/gtjhkeek/information-sheet-on-the-fa-3-logical-structure-04032026.pdf> |

Główne źródło **tłumaczeń** komunikatów XSD oraz reguł `SEMANTYCZNA` i `ARYTMETYCZNA`.

**Kopia robocza:** `korpus/broszura/broszura-fa3.txt` — wyciąg przez `pdftotext -layout`, ze
znacznikami `=== strona N ===` w miejsce znaków wysuwu strony. Cytaty bierze się z tego pliku,
a numer strony z najbliższego znacznika powyżej. Sam PDF nie jest commitowany; jego SHA-256
i polecenie konwersji zapisuje `korpus/PROVENANCE.md`.

Ten wyciąg jest warunkiem wykonalności wymogu dosłownego cytatu. Bez niego nikt — człowiek ani
agent — nie przepisze zdania ze strony 107 pliku PDF, a wymóg zamieni się w zachętę do zmyślania.

Podział na rozdziały ze stronami:

| Rozdział | Strony |
|---|---|
| Wstęp, definicja, wzór, jak wystawić | 3–4 |
| **Formaty pól (danych) pliku faktury ustrukturyzowanej** | 4–6 |
| Struktura i opis schematu głównego | 7–8 |
| `Naglowek` | 9 |
| `Podmiot1` | 10–15 |
| `Podmiot2` | 16–24 |
| `Podmiot3` | 25–36 |
| `PodmiotUpowazniony` | 37–41 |
| `Fa` | 42–85 |
| `FaWiersz` | 86–103 |
| `Rozliczenie` | 104–106 |
| `Platnosc` | 107–119 |
| `WarunkiTransakcji` (z `Transport` od 125) | 120–133 |
| `Zamowienie` | 134–145 |
| `Stopka` | 146–148 |
| `Zalacznik` | 149–165 |
| Spis przykładów / schematów / tabel | 166–170 |

Rozdział „Formaty pól" na stronach 4–6 jest najgęstszy w projekcie, ale **nie produkuje reguł** —
produkuje tłumaczenia. Opisuje precyzję kwot, formaty dat, długości pól i zapis identyfikatorów
podatkowych, czyli dokładnie to, co schemat wymusza facetami. Z tych sześciu stron pochodzą cytaty
do wpisów `XSD-kwota-precyzja`, `XSD-kwota-zapis`, `XSD-wzorzec`, `XSD-data-zakres`
i `XSD-dlugosc`.

Jedyny wyjątek z tego rozdziału, który jest regułą, a nie tłumaczeniem, to ramka WAŻNE ze
strony 6 o NIP-ie nabywcy — reguła `SEM-001`. Schemat nie ma czym wyrazić „ten numer jest
w niewłaściwym z trzech dopuszczalnych pól".

### Weryfikacja faktury po stronie KSeF

| | |
|---|---|
| Plik | `faktury/weryfikacja-faktury.md` |
| Repozytorium | `CIRFMF/ksef-docs`, licencja MIT |
| URL | <https://github.com/CIRFMF/ksef-docs/blob/main/faktury/weryfikacja-faktury.md> |

Źródło reguł `TECHNICZNA`. Wylicza, co KSeF sprawdza przy przyjęciu faktury: poprawność XML
1.0, kodowanie UTF-8 bez BOM, zgodność ze schematem, brak instrukcji przetwarzania XML, brak
niedozwolonych znaków Unicode, unikalność faktury (NIP sprzedawcy, rodzaj faktury, numer
faktury — kod `440` „Duplikat faktury"), datę wystawienia nie późniejszą niż data przyjęcia,
sumę kontrolną NIP, NIP w identyfikatorze wewnętrznym `Podmiot3`, rozmiar pliku (1 MB bez
załączników, 3 MB z załącznikami), limit 10 000 faktur w sesji, poprawność szyfrowania
AES-256-CBC z RSAES-OAEP oraz zgodność skrótów i rozmiarów z metadanymi.

Czego na tej liście **nie ma**: weryfikacji rachunkowej i semantycznej treści faktury. To jest
fakt, który README musi podać wprost, bo z niego wynika, dlaczego zielony wynik walidatora nie
jest gwarancją poprawności faktury — ani odwrotnie, przyjęcie przez KSeF nie jest gwarancją,
że faktura jest dobra.

Trzy reguły z tej listy są nierozstrzygalne po jednym pliku (duplikat, data przyjęcia, limit
sesji). Zostają w rejestrze z odpowiednio obniżoną wagą — patrz sekcja 10 specu.

### Złoty korpus — przykładowe faktury MF

| | |
|---|---|
| Plik | `przykladowe-pliki-dla-struktury-logicznej-e-faktury-fa-3.zip` (195,81 KB) |
| URL | <https://ksef.podatki.gov.pl/media/e5cia0ey/przykladowe-pliki-dla-struktury-logicznej-e-faktury-fa-3.zip> |
| Zawartość | 26 faktur, `Przykład_1` … `Przykład_26` |

To jest prawda odniesienia dla braku fałszywych alarmów. Walidator, który odrzuca fakturę
przykładową Ministerstwa Finansów, jest zepsuty — nie faktura.

**Dwie pułapki przy pobieraniu, obie realne:**

Nazwy plików w archiwum mają **niespójną wielkość liter** — część to `FA_3_Przykład_*.xml`,
a część `Fa_3_Przykład_*.xml`. Na Windowsie to niewidoczne, na Linuksie w CI wywali skrypt
zakładający jeden wzorzec. Skrypt pobierania musi dopasowywać nazwy bez uwzględniania
wielkości liter.

Nazwy zawierają polskie znaki (`Przykład`). Przy rozpakowaniu normalizujemy je do
`fa3-przyklad-01.xml` … `fa3-przyklad-26.xml`, a nazwę pierwotną zapisujemy w `PROVENANCE.md`.
Kodowanie nazw plików w archiwach ZIP jest źródłem problemów międzysystemowych i nie chcemy
ich w CI.

---

## Pomocnicze

| Dokument | Do czego | URL |
|---|---|---|
| Struktura numeru KSeF | 35 znaków, `NIP-RRRRMMDD-12HEX-CRC8`, CRC-8 z polinomem `0x07` i wartością początkową `0x00` | <https://github.com/CIRFMF/ksef-docs/blob/main/faktury/numer-ksef.md> |
| Przewodnik dla integratorów KSeF 2.0 | kontekst systemowy, sesje, kody błędów | <https://github.com/CIRFMF/ksef-docs> |
| Środowiska KSeF | adresy `api-test`, `api-demo`, `api`; zasady środowiska testowego | <https://github.com/CIRFMF/ksef-docs/blob/main/srodowiska.md> |
| Podręcznik KSeF 2.0, cz. II — wystawianie i otrzymywanie faktur | kontekst dla wyjaśnień pisanych do księgowego | <https://ksef.podatki.gov.pl/media/rronoxyt/podrecznik-ksef-20-cz-ii-wystawianie-i-otrzymywanie-faktur-w-ksef-06082026.pdf> |
| Tabela trybów wystawiania faktur, wersja 1.3 | tryby online, offline24, awaria | <https://ksef.podatki.gov.pl/media/xp2dhszg/tabela-tryby-wystawiania-faktur-24022026.pdf> |
| Strona z plikami do pobrania KSeF 2.0 | punkt wejścia do wszystkich dokumentów MF | <https://ksef.podatki.gov.pl/pliki-do-pobrania-ksef-20/> |
| Ustawa o VAT z 11 marca 2004 r. (Dz. U. z 2025 r. poz. 775 ze zm.) | podstawa prawna reguł arytmetycznych | — |

Numer KSeF jest w źródłach pomocniczych, a nie rozstrzygających, celowo: walidacja numeru KSeF
jest poza zakresem tego projektu (sekcja 2 specu). Dokument jest tu dlatego, że reguły
dotyczące faktur korygujących odwołują się do numeru KSeF faktury pierwotnej i trzeba wiedzieć,
jak on wygląda.

---

## Stan sztuki

Nie są to źródła reguł. Są tu, żeby projekt wiedział, w jakim towarzystwie stoi, i żeby
sekcja README o stanie sztuki miała na czym stać.

| Projekt | Co to | Licencja |
|---|---|---|
| [`ksefuj`](https://github.com/ksefuj/ksefuj), [`ksefuj.to`](https://ksefuj.to) | walidator FA(3) w TypeScripcie: XSD, 44 reguły semantyczne, arytmetyka VAT, kursy NBP, IBAN; CLI, pakiet npm, walidacja lokalnie w przeglądarce przez `libxml2-wasm` | Apache 2.0 |
| `ksef2`, `ksef-client`, `ksef2.0-python`, `python-ksef` | klienci API KSeF 2.0 w Pythonie — uwierzytelnianie, sesje, szyfrowanie | różne, otwarte |
| Walidator XML KSeF FA(3), RAFSOFT | walidator webowy | zamknięty |

**Zasada wobec `ksefuj`:** kodu ani brzmienia reguł nie kopiujemy. Reguły wyprowadzamy
z pierwotnych dokumentów MF. Ich publiczny podział kategorii (Podmiot 8, Fa 5, Adnotacje 11,
FaWiersz 4, korekty 2, płatność 8, format 2, logika biznesowa 4) wolno użyć **wyłącznie jako
listy kontrolnej pokrycia** na koniec etapu 6, z atrybucją. Jeśli w trakcie pracy znajdziemy
u nich błąd z reprodukowalnym przypadkiem — zgłaszamy go do nich. To jest tańsze niż
konkurowanie i uczciwsze.
