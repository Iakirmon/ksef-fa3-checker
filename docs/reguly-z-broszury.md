# Reguły z broszury FA(3) — wyciąg (etap 6)

Dokument roboczy: kandydaci na wpisy rejestru semantycznego/arytmetycznego **oraz**
kandydaci na tłumaczenia XSD. Cytaty skopiowane z `korpus/broszura/broszura-fa3.txt`
(znaczniki `=== strona N ===`). Numer strony = najbliższy znacznik powyżej cytatu.

**Zakres ukończenia etapu 6:** rozdziały `Fa` (s. 42–85) i `FaWiersz` (s. 86–103).

**Pytanie kwalifikujące:** jeśli schemat wymusza regułę facetem (`fractionDigits`,
`maxLength`, `pattern`, `minInclusive`, `minOccurs`, `xsd:choice` / kolejność
`sequence`) — to **nie** jest kandydat na regułę, tylko na tłumaczenie.

Identyfikatory: `SEM-001` już istnieje (NIP nabywcy, s. 6). Numeracja poniżej od
`SEM-002` / `ARY-001`.

---

## Fa (strony 42–85)

### Kandydaci na reguły

#### SEM-002 — Korekta: podstawy, podatek i P_15 przez różnicę

- **Brzmienie:** Na fakturze korygującej pola podstaw opodatkowania, podatku i należności
  ogółem wypełnia się różnicą, a pozostałe pola — stanem po korekcie.
- **Cytat:** „W przypadku wystawienia faktury korygującej wypełnia się wszystkie pola wg stanu po korekcie, a pola dotyczące podstaw opodatkowania, podatku oraz należności ogółem wypełnia się poprzez różnicę.”
- **Strona:** 42
- **Pola:** `RodzajFaktury`, `P_13_*`, `P_14_*`, `P_15`
- **Waga:** `OSTRZEZENIE` — broszura opisuje sposób wypełnienia; pełna weryfikacja
  „różnica względem faktury pierwotnej” wymaga dokumentu korygowanego (offline tylko
  heurystyka znaku / spójności wewnętrznej).
- **Offline:** częściowo (ostrzeżenie przy `KOR` bez ujemnych/różnicowych kwot — ostrożnie)
- **XSD łapie?** Nie — schemat nie porównuje z fakturą pierwotną ani nie wymusza znaku różnicy.

#### SEM-003 — Kod waluty PLN przy fakturze w złotych

- **Brzmienie:** Gdy faktura jest w walucie polskiej, w `KodWaluty` podaje się `PLN`.
- **Cytat:** „W przypadku faktury wystawianej w polskiej walucie należy podać kod waluty: „PLN”.”
- **Strona:** 43
- **Pola:** `KodWaluty`
- **Waga:** `INFORMACJA` — broszura instruuje zapis kodu; nie da się offline rozstrzygnąć
  „czy faktura jest w złotych” poza samym kodem (tautologia). Przydatne jako przypomnienie
  przy nietypowych kodach / pustym polu tylko jeśli inne pola sugerują PLN — **raczej
  niska wartość jako BLAD**. Proponowana waga: `INFORMACJA`.
- **Offline:** tak (tylko jako wskazówka przy braku ISO)
- **XSD łapie?** Częściowo format kodu ISO; **nie** semantykę „polska waluta ⇒ PLN”.

#### SEM-004 — Wspólna data dostawy w `P_6`, nie w każdym `P_6A`

- **Brzmienie:** Gdy data jest wspólna dla wszystkich wierszy, wypełnia się `P_6` w `Fa`,
  a nie `P_6A` w wierszach.
- **Cytat:** „W przypadku, gdy dla wszystkich wierszy faktury data jest wspólna – wypełnia się pole P_6 (element Fa).”
- **Strona:** 88 (opis `P_6A` w rozdziale FaWiersz, ale reguła dotyczy relacji Fa ↔ FaWiersz;
  powiązany opis `P_6` jest w Fa)
- **Pola:** `Fa/P_6`, `FaWiersz/P_6A`
- **Waga:** `OSTRZEZENIE`
- **Offline:** tak (gdy wszystkie `P_6A` równe i `P_6` puste / odwrotnie)
- **XSD łapie?** Nie — oba pola opcjonalne niezależnie.

#### SEM-005 — `P_6A` tylko przy różnych datach pozycji

- **Brzmienie:** `P_6A` wypełnia się, gdy daty pozycji się różnią; w przeciwnym razie pole
  pozostaje puste.
- **Cytat:** „Pole wypełnia się w przypadku, gdy dla poszczególnych pozycji faktury występują różne daty. W przeciwnym przypadku pole pozostaje puste.”
- **Strona:** 88
- **Pola:** `FaWiersz/P_6A`
- **Waga:** `OSTRZEZENIE`
- **Offline:** tak (wespół z SEM-004)
- **XSD łapie?** Nie.

#### ARY-001 — Reszta po zaliczkach: `P_15` − Σ`P_15Z`

- **Brzmienie:** Gdy faktura po wydaniu towaru dokumentuje też wcześniejsze płatności,
  różnica `P_15` i sumy `P_15Z` to kwota pozostała ponad te płatności.
- **Cytat:** „różnica kwoty w polu P_15 i sumy poszczególnych pól P_15Z stanowi kwotę pozostałą ponad płatności otrzymane przed wykonaniem czynności udokumentowanej fakturą”
- **Strona:** 78
- **Pola:** `P_15`, `ZaliczkaCzesciowa/P_15Z`
- **Waga:** `OSTRZEZENIE` (broszura definiuje znaczenie różnicy, nie twierdzi wprost, że
  Σ`P_15Z` ≤ `P_15` zawsze; reguła może pilnować niesprzeczności, gdy obie strony obecne)
- **Offline:** tak
- **XSD łapie?** Nie — brak asercji arytmetycznej.

#### SEM-006 — `DodatkowyOpis/NrWiersza` wskazuje istniejący `NrWierszaFa`

- **Brzmienie:** Numer wiersza w opisie dodatkowym powinien wskazywać wiersz faktury,
  którego dotyczy informacja.
- **Cytat:** „Aby zidentyfikować, którego towaru (wymienionego w elemencie FaWiersz) dotyczy dana informacja dodatkowa, można wskazać w elemencie DodatkowyOpis, w polu NrWiersza, numer wiersza faktury, do którego odnosi się dana informacja.”
- **Strona:** 84
- **Pola:** `DodatkowyOpis/NrWiersza`, `FaWiersz/NrWierszaFa`
- **Waga:** `OSTRZEZENIE` („można” — nie twardy obowiązek; sensowna spójność referencyjna)
- **Offline:** tak
- **XSD łapie?** Nie — brak klucza obcego między węzłami.

#### ARY-002 — Wzór podatku od wartości brutto (`KP`)

- **Brzmienie:** Przy metodzie z art. 106e ust. 7 i 8 kwota podatku wyliczana jest ze
  wzoru `KP = WB × SP/(100+SP)`.
- **Cytat:** „KP = WB x SP/100+SP”
- **Strona:** 90–91 (wzór przy `P_9B` / `P_11A`)
- **Pola:** `P_11A`, `P_12`, `P_11Vat` (gdy użyta metoda brutto)
- **Waga:** `BLAD` gdy wszystkie trzy wartości obecne i rozjeżdżają się poza tolerancją
  zaokrągleń; milczenie gdy brak danych (`dec()` → `None`)
- **Offline:** tak
- **XSD łapie?** Nie — tylko precyzja kwot.

### Kandydaci na tłumaczenia (XSD już łapie)

| Temat | Cytat (skrót) | Strona | Dlaczego XSD |
|---|---|---|---|
| `P_19` + jedno z `P_19A/B/C` vs `P_19N` | „W przypadku, gdy pole P_19 równa się „1”, należy wypełnić dodatkowo jedno z pól: P_19A, P_19B lub P_19C.” | 57 | `xsd:choice` w `Zwolnienie` |
| `P_22` / `P_22N` + `NowySrodekTransportu` | pomijanie pól przy `P_22N=1` | 58 | `xsd:choice` w `NoweSrodkiTransportu` |
| `P_PMarzy` + wybór procedury | „gdy pole P_PMarzy równa się „1”, należy wypełnić dodatkowo jedno z pól…” | 63 | `xsd:choice` |
| `NrKSeFZN` + `NrFaZaliczkowej` vs `NrKSeFFaZaliczkowej` | „gdy w polu NrKSeFZN wskazano wartość „1”, należy wypełnić również pole NrFaZaliczkowej.” | 85 | `xsd:choice` / `sequence` w `FakturaZaliczkowa` |
| `P_7` max 512 znaków | „Maksymalna ilość znaków: 512” | 88 | `TZnakowy512` / `maxLength` |
| Precyzja ceny `P_9A` | „Maksymalna liczba miejsc po kropce: 8” | 89–90 | `fractionDigits` w typie kwotowym ilości/ceny |

Te pozycje **nie** wchodzą do `reguly/` — ewentualnie doprecyzowanie istniejących
`XSD-*`, jeśli komunikat lxml jest zbyt surowy.

---

## FaWiersz (strony 86–103)

### Kandydaci na reguły

#### SEM-007 — `P_7` nazwa towaru/usługi (opcjonalność ograniczona)

- **Brzmienie:** `P_7` nie jest wymagane wyłącznie w przypadku opustu/obniżki z art. 106j
  ust. 3 pkt 2; poza tym — oczekiwane przy zwykłych pozycjach.
- **Cytat:** „Pole nie jest wymagane wyłącznie dla przypadku określonego w art 106j ust. 3 pkt 2 ustawy, tj., gdy podatnik udziela opustu lub obniżki ceny i wystawia fakturę korygującą, dotyczącą wszystkich dostaw towarów i świadczenia usług na rzecz jednego odbiorcy w danym okresie.”
- **Strona:** 88
- **Pola:** `P_7`, `RodzajFaktury`
- **Waga:** `OSTRZEZENIE` — pełna kwalifikacja „wyłącznie ten przypadek” wymaga kontekstu
  korekty okresowej; reguła może ostrzegać przy zwykłej `VAT` i pustym `P_7` gdy wiersz
  ma kwoty.
- **Offline:** częściowo
- **XSD łapie?** Nie — `minOccurs=0` na `P_7`.

#### ARY-003 — Spójność wiersza netto: obecność `P_11` przy cenie i ilości

- **Brzmienie:** `P_11` to wartość sprzedaży netto pozycji; przy wypełnionych `P_8B` i
  `P_9A` oczekuje się wypełnienia `P_11` (poza wyjątkami marży/uproszczenia).
- **Cytat:** „Wartość dostarczonych towarów lub wykonanych usług, objętych transakcją, bez kwoty podatku (wartość sprzedaży netto)”
- **Strona:** 91
- **Pola:** `P_8B`, `P_9A`, `P_11`
- **Waga:** `OSTRZEZENIE` (broszura definiuje pole, nie pisze wprost „iloczyn”; twarda
  równość `P_8B×P_9A−P_10=P_11` byłaby nadinterpretacją bez cytatu o iloczynie)
- **Offline:** tak
- **XSD łapie?** Nie.

#### SEM-004 / SEM-005

Opisane wyżej (cytaty z opisu `P_6A` w FaWiersz).

#### ARY-002

Wzór `KP` — cytat w opisie metody brutto przy polach wiersza (powyżej).

### Kandydaci na tłumaczenia (FaWiersz)

| Temat | Strona | Dlaczego XSD |
|---|---|---|
| Opcjonalność `P_8A`/`P_8B`/`P_9A`/`P_11` z wyjątkami ustawowymi | 89–93 | `minOccurs=0`; wyjątki to semantyka ustawowa — **nie** tłumaczenie i **ostrożnie** z regułą |
| `P_12` enumeracje stawek | 92 | typy/enumeracje schematu |
| `maxLength` / precyzja kwot wiersza | 88–91 | facety typów |
| `NrWierszaFa` jako `TNaturalny` | 87 | typ XSD |

---

## Podsumowanie

| | Liczba |
|---|---|
| Kandydaci na reguły (SEM/ARY) | **9** (`SEM-002`…`SEM-007`, `ARY-001`…`ARY-003`) |
| Kandydaci na tłumaczenia (XSD) | **10+** (tabele powyżej) |
| Już zaimplementowane spoza tego wyciągu | `SEM-001` (s. 6, Formaty pól) |

### Priorytet implementacji (etap 7)

1. `ARY-001` (`P_15` / `P_15Z`) — jasny cytat, Decimal, milczenie przy braku danych  
2. `ARY-002` (wzór `KP`) — jasny cytat matematyczny  
3. `SEM-004` + `SEM-005` (daty `P_6` / `P_6A`)  
4. `SEM-006` (referencja `NrWiersza`)  
5. `SEM-002`, `SEM-007`, `ARY-003`, `SEM-003` — ostrożniej / niższy priorytet

### Świadomie pominięte

- Obowiązki ustawowe wykraczające poza brzmienie broszury.
- Reguły, które są wyłącznie `xsd:choice` (zwolnienia, NST, marża, zaliczki KSeF).
- „Formaty pól” s. 4–6 — domena tłumaczeń (poza istniejącym `SEM-001`).
