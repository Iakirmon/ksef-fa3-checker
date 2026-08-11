# fa3-check — projekt techniczny

**Data:** 2026-08-11
**Wersja:** 2 — po weryfikacji eksperymentalnej założeń wersji 1
**Status:** zatwierdzony do realizacji

---

## 1. Cel

`fa3-check` to walidator faktury ustrukturyzowanej FA(3) z warstwą webową: wklejasz XML,
natychmiast dostajesz odpowiedź. Projekt portfolio, ale użyteczny — ma rozwiązywać prawdziwy
problem człowieka, który dostał odrzuconą fakturę i nie wie dlaczego.

Obietnica projektu, którą repo ma udowadniać zawartością, a nie deklaracją:

> Walidator FA(3), w którym **każda reguła mówi, skąd się wzięła**, a **każdy błąd mówi, co
> z nim zrobić**.

Obie połowy są wymuszone testami, i to nie testami na słowo honoru. `test_zrodla.py` sprawdza,
że cytat przy każdym wpisie **występuje dosłownie** w wyciągu tekstowym broszury i że podany
numer strony się zgadza. `test_wyjasnienia.py` odrzuca wyjaśnienia bez liczb i z listy zwrotów
zakazanych. To nie są dobre praktyki do pilnowania — to bramki w CI.

Środek ciężkości leży **nie w liczbie reguł, a w jakości wyjaśnień i audytowalności źródeł**.
Istnieje kilka walidatorów FA(3), w tym `ksefuj` z 44 regułami. Nie wygramy liczbą reguł i nie
próbujemy.

## 2. Zasada, z której wynika cała architektura

Schemat FA(3) to **XML Schema 1.0** i używa pełnego zestawu facetów. Zweryfikowane w plikach
(sekcja 3):

```xml
TKwotowy      decimal, totalDigits=18, fractionDigits=2, pattern -?([1-9]\d{0,15}|0)(\.\d{1,2})?
TKwotowy2     decimal, totalDigits=22, fractionDigits=8
TIlosci       decimal, totalDigits=22, fractionDigits=6
TDataT        etd:TData, minInclusive=2006-01-01, maxInclusive=2050-01-01
TZnakowy512   token,   minLength=1, maxLength=512
TNrNIP        string,  pattern [1-9]((\d[1-9])|([1-9]\d))\d{7}
```

Stąd wniosek, który trzeba było sprawdzić, zanim powstała pierwsza reguła: **rozdział „Formaty
pól (danych)" broszury FA(3) (s. 4–6) jest opisem tego, co schemat już wymusza.** Precyzja kwot,
format daty, maksymalne długości pól, NIP bez separatorów — wszystko to łapie `lxml` bez ani
jednej linii naszego kodu.

Zasada nadrzędna:

> **Reguła, którą łapie XSD, nie jest regułą — jest tłumaczeniem.**

Wartością nie jest złapanie takiego błędu. Wartością jest zamiana komunikatu

```
Element '{http://crd.gov.pl/wzor/2025/06/25/13775/}P_11': [facet 'fractionDigits']
The value '1234.567' has more fractional digits than are allowed ('2').
```

w zdanie, które rozumie księgowy, razem z odnośnikiem do strony dokumentu, z którego to wynika.

Projekt ma więc **dwa rejestry, nie jeden**:

| Rejestr | Co zawiera | Wartość, którą dodaje |
|---|---|---|
| `tlumaczenia/` | tłumaczenia komunikatów XSD na wyjaśnienia | czytelność i odnośnik do źródła |
| `reguly/` | wyłącznie to, czego XSD 1.0 wyrazić **nie umie** | wykrycie błędu, którego nikt inny nie zgłosi |

Co leży poza zasięgiem XSD 1.0 i dlatego trafia do `reguly/`:

- **arytmetyka** — sumy, wyliczenia VAT, zgodność pozycji z podsumowaniem. XSD 1.0 nie ma
  `xs:assert`, więc nie umie dodawać,
- **zależności między odległymi polami** — „NIP nabywcy w tym polu, a nie w tamtym", spójność
  faktury korygującej z pierwotną,
- **sumy kontrolne** — `TNrNIP` sprawdza **wzorzec**, nie sumę kontrolną. Wyrażenie regularne
  nie policzy modulo,
- **własności bajtów** — BOM, deklaracja kodowania, `DOCTYPE`, rozmiar pliku,
- **reguły zależne od stanu systemu** — duplikat faktury, data przyjęcia. Nierozstrzygalne
  offline, sekcja 11.

To rozgraniczenie jest też odpowiedzią na pytanie „ile reguł napiszemy". Mniej, niż wyglądało —
i każda z powodem istnienia.

## 3. Co zostało sprawdzone eksperymentalnie

Wersja 1 tego dokumentu zawierała cztery założenia, z których **trzy były błędne**. Zostały
sprawdzone na plikach i w działającym `lxml`. Tabela jest tu dlatego, że każdy z tych faktów
zmienia coś w implementacji, a agent, który go nie zna, popełni ten sam błąd co ja.

| Sprawdzone | Wynik |
|---|---|
| Czy 26 przykładów MF przechodzi XSD | **26/26 przechodzi.** Kryterium etapu jest osiągalne |
| Nazwy typów kwotowych i datowych | **Były błędne.** FA(3) używa `TKwotowy`, `TKwotowy2`, `TIlosci`, `TDataT`, `TZnakowy512` — nie `TKwota2` ani `TData`, które istnieją w schemacie bazowym, ale nie dla tych pól |
| Czy `error.path` daje nazwę elementu | **Nie.** Zwraca ścieżkę pozycyjną `/*/*[4]/*[15]/*[7]`. Nazwa jest tylko w komunikacie |
| Czy da się ustalić typ bez czytania komunikatu | **Tak**, przez wykonanie `error.path` jako XPath na dokumencie → węzeł → nazwa → mapa typów ze schematu. Sprawdzone na 8 klasach błędów, za każdym razem zgodne z komunikatem |
| Mapa element → typ XSD | 250 wpisów, z tego **7 niejednoznacznych** — wszystkie to typy złożone (`DaneIdentyfikacyjne`, `OsobaFizyczna`, `AdresPol`…), nie typy wartości |
| Czy flagi parsera blokują bombę entyfikacyjną | **Tak.** `libxml2` 2.11.9 odrzuca: „Maximum entity amplification factor exceeded" |
| Czy blokują XXE | **Częściowo.** Dokument **parsuje się poprawnie**, encja nie jest rozwijana, tekst pusty, zero wycieku. Ale wyjątku nie ma — test „każdy atak rzuca wyjątek" by nie przeszedł |
| Limit głębokości | `libxml2` odrzuca przy **256** poziomach z `huge_tree=False`. Własny limit 100 był zbędny |
| Kodowanie `pdftotext` | Domyślnie **nie UTF-8** na Windowsie. Wymagane `-enc UTF-8`, inaczej polskie znaki są zepsute |
| Numeracja stron w wyciągu | Numer fizyczny **równa się** nadrukowanemu — różnica 0 na 172 wykrytych stopkach |
| Czy cytat da się odnaleźć dosłownie | **Tak**, po normalizacji białych znaków. 6 z 6 cytatów odnalezione na oczekiwanych stronach |
| Sumy kontrolne NIP w złotym korpusie | **64 NIP-y, wszystkie poprawne.** Gdyby choć jeden był fikcyjny, `TEC-005` z wagą `BLAD` łamałby bramkę złotego korpusu — sprzeczności nie ma |
| Czy da się wyciągnąć model treści dla `struktura.py` | **Nie naiwnie.** Przejście `complexType.iter(element)` zwraca dla `Fa` **222** deklaracje, a prawdziwa `Fa` ma 19 dzieci — `iter()` schodzi przez całe zagnieżdżone drzewo |
| Czy przejście **bezpośrednich cząstek** działa | **Tak, z jednym brakiem.** `Fa` daje 53 cząstki, zero nieznanych dzieci na 5 typach, przestawienie wykryte. Ale `brakujace` daje 7 fałszywych trafień, bo nie propagowałem `minOccurs` **grupy** — element w opcjonalnej grupie nie jest wymagany. Sekcja 8.6 |
| Czy `xsd:choice` uniemożliwia orzekanie o kolejności | **Nie.** `Fa` ma `choice`, a kolejność wykryła się poprawnie. Pierwsza wersja 8.6 była zbyt ostrożna i wyciszyłaby najważniejszy element |
| Zły albo brakujący namespace | Jeden błąd, kod `SCHEMAV_CVC_ELT_1`: „No matching global declaration available for the validation root". Najczęstszy błąd początkujących — wersja 1 nie miała dla niego tłumaczenia |
| Dokument, który nie jest fakturą FA(3) | Ten sam kod `SCHEMAV_CVC_ELT_1`, komunikat nieczytelny. Potrzebne sprawdzenie korzenia przed walidacją, sekcja 8.8 |
| Wykrycie `DOCTYPE` | `drzewo.docinfo.doctype` zwraca `'<!DOCTYPE Faktura>'`, `internalDTD` nie jest `None` — wykrywalne pewnie po sparsowaniu |
| Środowisko | Python 3.14.5, `lxml` 6.1.1 (`libxml2` 2.11.9), FastAPI 0.141.1, Jinja2 3.1.6 — koła dostępne |

Dwie pułapki wykryte przy okazji, obie trafiłyby w implementację:

**Nazwy plików w archiwum MF.** Numer przykładu jest **na końcu** nazwy, a nazwa zawiera cyfrę
wcześniej: `FA_3_Przykład_12.xml`. Naiwne `re.search(r"(\d+)", stem)` łapie `3` z `FA_3`
i wszystkie 26 plików nadpisuje się na jeden. Poprawnie: `re.search(r"(\d+)\s*$", stem)`.
Dodatkowo wielkość liter jest niespójna — w archiwum są zarówno `FA_3`, jak i `Fa_3`.

**`SCHEMAV_ELEMENT_CONTENT` wskazuje sąsiada, nie winowajcę.** Po usunięciu `P_2` ścieżka
wskazała `P_6`. Ten jeden kod obsługuje trzy różne problemy: brak wymaganego elementu, element
nadmiarowy i zaburzoną kolejność. Sekcja 8.6 opisuje, jak to obejść.

## 4. Nie-cele

Świadomie poza zakresem. Każdy z tych punktów to osobny projekt:

- wysyłanie faktur do KSeF i jakakolwiek integracja z API — nie jesteśmy klientem KSeF,
- generowanie faktur, kreator formularzowy, autopoprawki,
- wizualizacja faktury, eksport do PDF, kody QR, walidacja numeru KSeF,
- struktury inne niż FA(3): FA(2), PEF, FA_KOR_PEF, FA_RR,
- konta użytkowników, historia walidacji, jakakolwiek baza danych,
- pakiet na PyPI i stabilne publiczne API biblioteki,
- tłumaczenia interfejsu — polski; angielski dopiero na końcu i opcjonalnie,
- **duplikowanie tego, co łapie XSD** — sekcja 2,
- korpus mutacyjny i generator celowo złamanych faktur — reguły testujemy fixture'ami.

Dwa ostatnie punkty były rozważane i celowo odrzucone. Zapisane, żeby nie wróciły przez
przypadek.

## 5. Stan sztuki

**Ten projekt nie jest pierwszy i README musi to powiedzieć wprost w sekcji otwierającej.**
Projekt, który udaje pioniera, traci wiarygodność w chwili, gdy recenzent wpisze hasło
w wyszukiwarkę.

| Narzędzie | Co ma | Czym się różnimy |
|---|---|---|
| [`ksefuj`](https://github.com/ksefuj/ksefuj) (Apache 2.0, TypeScript, `ksefuj.to`) | XSD, 44 reguły semantyczne z broszury, arytmetyka VAT, kursy NBP, IBAN, CLI, pakiet npm, trzy języki, walidacja lokalnie w przeglądarce przez `libxml2-wasm` | słownik tłumaczeń komunikatów XSD; cytat ze źródła weryfikowany testem przy każdym wpisie; pięcioczęściowe wyjaśnienie. Ich faza 1.5 to dosłownie „human-readable error messages" — to obszar, w którym wchodzimy |
| Walidatory komercyjne i webowe (np. RAFSOFT) | walidacja XSD, czasem semantyka | audytowalność źródeł, otwarty kod |

Uczciwie o tym, w czym jesteśmy słabsi: `ksefuj` waliduje w przeglądarce, więc XML nigdy nie
opuszcza komputera użytkownika. My mamy serwer, więc mamy problem prywatności, którego oni nie
mają. Odpowiadamy trybem lokalnym w pierwszej kolejności i zasadami z sekcji 13, ale to nasza
słabsza strona i README ma to przyznać.

Kod ani teksty reguł `ksefuj` **nie są kopiowane**. Reguły wyprowadzamy z pierwotnych dokumentów
MF. Ich publiczny podział kategorii wolno użyć wyłącznie jako listy kontrolnej pokrycia,
z atrybucją.

## 6. Decyzje projektowe

| Decyzja | Uzasadnienie |
|---|---|
| **Reguła, którą łapie XSD, jest tłumaczeniem, nie regułą** | Sekcja 2. Bez tego połowa rejestru byłaby duplikatem `lxml` |
| **Typ XSD ustalany przez wykonanie `error.path` jako XPath**, nigdy z treści komunikatu | Sekcja 3 potwierdza wykonalność. Brzmienie komunikatów `libxml2` zmienia się między wersjami |
| Tylko FA(3) | Od 1 lutego 2026 r. jedyny obowiązujący wzór |
| Python 3.12+, FastAPI, Jinja2, HTMX | Bez `npm`, bez kroku budowania. Jedno polecenie podnosi stronę |
| `lxml` z **dokładnie przypiętą wersją** + `lxml-stubs` | Słownik tłumaczeń zależy od kodów `libxml2`. Bez `lxml-stubs` `mypy --strict` nie przejdzie, bo `lxml` nie ma wbudowanych typów |
| **XSD nie jest bramką** dla reguł semantycznych | Wersja 1 blokowała reguły po błędzie schematu. Użytkownik z jednym błędem formatu i pięcioma semantycznymi zobaczyłby jeden. Reguły są odporne na braki (`dec()` zwraca `None`), więc lecą zawsze; wynik jest oznaczony jako częściowy |
| **Limit ciała żądania 3 MB**, nie 1 MB | Wersja 1 odrzucałaby legalną fakturę z załącznikiem (KSeF dopuszcza 3 MB). Regułą jest `TEC-004`, nie limit HTTP |
| `safexml` **odrzuca `DOCTYPE`** | Sekcja 3: przy `resolve_entities=False` XXE nie wycieka, ale dokument przechodzi. `DOCTYPE` w fakturze KSeF nie ma uzasadnienia, więc odrzucenie czyni XXE niemożliwym strukturalnie |
| Kwoty wyłącznie `Decimal` | `float` w kodzie liczącym pieniądze to błąd, nie wybór stylu |
| Cienka fasada `Faktura`, bez modelu typowanego całej struktury | FA(3) to 250 elementów i 170 stron opisu. Pełny model to osobny projekt |
| Wpis = katalog + dekorator, zero edycji w istniejących plikach | Bez tego dodanie wpisu przestaje być tanie |
| Schemat i korpus **wendorowane** razem z `PROVENANCE` | Repo samowystarczalne; SHA-256 wyłapie podmianę wzoru |
| Wyciąg broszury do tekstu, **PDF niecommitowany** | Bez wyciągu wymóg dosłownego cytatu jest niewykonalny, a niewykonalny wymóg zamienia się w zachętę do zmyślania |
| **Identyfikatory po polsku** — świadome odejście od konwencji `sortlab` | Słownik domeny jest polski w źródle: `P_15`, `Podmiot2`, `NrVatUE`, `Zastrzezenie`, `Waga`, `Zrodlo`. Tłumaczenie go na angielski tworzy stałą warstwę mapowania między broszurą, specem i kodem. Docstringi i proza też po polsku |
| Ogranicznik liczby żądań **pisany ręcznie**, bez nowej zależności | Licznik w pamięci na słowniku wystarcza dla jednego procesu |
| Waga zastrzeżenia wyprowadzona z broszury | Broszura sama rozdziela poprawność pliku od obowiązku ustawowego (s. 4). Sekcja 10 |
| Lokalnie w pierwszej kolejności; publiczne demo po hartowaniu | Strona przyjmująca cudzy XML to zobowiązanie, nie funkcja |

## 7. Architektura

```
                 ┌────────────────────────────────┐
                 │ web/   FastAPI + Jinja2 + HTMX │
                 └────────────────┬───────────────┘
                                  │
                 ┌────────────────┴───────────────┐
                 │         walidacja.py           │
                 └──┬──────────┬─────────┬────────┘
                    │          │         │
        ┌───────────┴──┐ ┌─────┴────┐ ┌──┴─────────┐
        │  safexml.py  │ │schema.py │ │ faktura.py │
        │  parsowanie  │ │ XSD 1.0  │ │   fasada   │
        │  niezaufane  │ │ + typy   │ └──┬─────────┘
        └──────────────┘ └─────┬────┘    │
                               │         │
                    ┌──────────┴──┐ ┌────┴────────┐
                    │ tlumaczenia │ │  rejestr.py │
                    │ .py         │ └────┬────────┘
                    │ struktura.py│      │
                    └──────┬──────┘      ▼
                           │        reguly/<ID>/
                  tlumaczenia/<ID>/      │
                           └──────┬──────┘
                                  ▼
                            ┌──────────┐
                            │ typy.py  │
                            └──────────┘
```

Zależności idą wyłącznie w jedną stronę: `reguly/` i `tlumaczenia/` → `rejestr` → `typy`. Ani
reguła, ani tłumaczenie nie importuje niczego z `web`, `schema`, `walidacja` ani `safexml`.
**Wymusza to `test_niezmienniki.py` analizą AST**, nie prośba w dokumencie.

Reguła to funkcja czysta — dostaje fasadę dokumentu, zwraca zastrzeżenia. Bez stanu, plików,
sieci i zegara. Reguła bezstanowa jest testowalna jednym fixture'em i obsługuje stronę oraz
testy bez warstwy pośredniej. Reguła sięgająca po kurs NBP przestaje być testowalna offline
i pada w najgorszym momencie.

`safexml.py` jest **jedynym** miejscem, które parsuje XML, i jedynym, które wolno wywołać na
niezaufanym wejściu.

### 7.1 Struktura katalogów

```
fa3-check/
├── README.md
├── LICENSE                                  (MIT)
├── AGENTS.md
├── pyproject.toml
├── .gitattributes                           krytyczny — sekcja 13.1
├── .cursorignore
├── .cursorindexingignore
├── .cursor/
│   ├── rules/{00-projekt,10-reguly,20-web,30-zrodla}.mdc
│   └── skills/{etap,nowa-regula,audyt-zrodel}/SKILL.md
├── .github/workflows/ci.yml
├── src/fa3check/
│   ├── typy.py                              Zastrzezenie, Zrodlo, KluczBledu, BladSchematu…
│   ├── safexml.py                           parsowanie niezaufanego XML
│   ├── schema.py                            walidacja XSD + mapa element→typ
│   ├── struktura.py                          analiza modelu treści dla SCHEMAV_ELEMENT_CONTENT
│   ├── tlumaczenia.py                       dopasowanie błędu do tłumaczenia
│   ├── faktura.py                           fasada: xp(), dec(), linia()
│   ├── rejestr.py                           @rejestruj, @tlumacz, autodiscovery
│   ├── walidacja.py                         orkiestracja
│   ├── tlumaczenia/<ID>/                    tlumaczenie.py, zrodlo.md, fixtures/wywoluje.xml
│   ├── reguly/<ID>/                         regula.py, zrodlo.md, fixtures/{przechodzi,lamie}.xml
│   └── web/
│       ├── app.py
│       ├── szablony/{strona,wynik,reguly}.html
│       └── static/{styl.css,htmx.min.js}
├── tests/
│   ├── conftest.py
│   ├── test_rejestr.py
│   ├── test_zrodla.py                       cytat dosłownie w broszurze + numer strony
│   ├── test_niezmienniki.py                 architektura sprawdzana przez AST
│   ├── test_zloty_korpus.py
│   ├── test_reguly.py
│   ├── test_tlumaczenia.py
│   ├── test_struktura.py
│   ├── test_wyjasnienia.py
│   ├── test_safexml.py
│   ├── test_fuzz.py                         Hypothesis
│   └── test_web.py
├── korpus/
│   ├── PROVENANCE.md
│   ├── schema/                              schemat_FA(3) + bazowe/
│   ├── zloty/                               fa3-przyklad-01.xml … -26.xml
│   ├── broszura/broszura-fa3.txt            wyciąg ze znacznikami stron
│   ├── zrodla/weryfikacja-faktury.md        źródło reguł TECHNICZNA, dla test_zrodla
│   └── zlosliwe/
├── scripts/pobierz_korpus.py
└── docs/
    ├── zrodla.md
    ├── reguly-z-broszury.md                 wyciąg (etap 6)
    └── spec/{…-design.md, …-cursor-prompty.md}
```

## 8. Kontrakty modułów

### 8.1 `typy.py`

```python
class Poziom(StrEnum):
    SCHEMA        = "schema"        # przetłumaczony błąd XSD
    TECHNICZNA    = "techniczna"    # reguły przyjęcia KSeF, na bajtach
    SEMANTYCZNA   = "semantyczna"   # zależności między polami
    ARYTMETYCZNA  = "arytmetyczna"  # rachunki

class Waga(StrEnum):
    BLAD = "blad"; OSTRZEZENIE = "ostrzezenie"; INFORMACJA = "informacja"

@dataclass(frozen=True, slots=True)
class Zrodlo:
    dokument: str; wersja: str; sekcja: str; cytat: str
    strona: int | None = None
    url: str | None = None

@dataclass(frozen=True, slots=True)
class BladSchematu:
    typ_lxml: str          # error.type_name, np. "SCHEMAV_CVC_FRACTIONDIGITS_VALID"
    element: str | None    # z rozwiązania error.path — NIE z komunikatu
    typ_xsd: str | None    # z mapy schematu
    xpath: str             # error.path, pozycyjny
    linia: int
    wartosc: str | None
    komunikat: str         # surowy tekst — wyłącznie do diagnostyki

@dataclass(frozen=True, slots=True)
class Zastrzezenie:
    wpis: str; waga: Waga; poziom: Poziom
    xpath: str; linia: int | None
    co: str; dlaczego: str; jak_naprawic: str
    zrodlo: Zrodlo
    diagnostyka: str | None = None

@dataclass(frozen=True, slots=True)
class Wynik:
    zastrzezenia: tuple[Zastrzezenie, ...]
    schema_ok: bool
    czesciowy: bool        # True gdy schemat odrzucił i część reguł mogła nie mieć danych
    czas_ms: int
```

Hierarchia wyjątków: `Fa3Error` → `XmlNiebezpieczny`, `XmlNiepoprawny`, `WpisBezZrodla`,
`LimitPrzekroczony`. Nigdy `except:` ani `except Exception` bez ponownego podniesienia — poza
jednym miejscem opisanym w 8.8.

### 8.2 `rejestr.py`

```python
def rejestruj(**metadane) -> Callable[[FunkcjaReguly], FunkcjaReguly]
def tlumacz(**metadane) -> Callable[[type], type]
def odkryj() -> None
def reguly() -> tuple[Regula, ...]
def tlumaczenia() -> tuple[Tlumaczenie, ...]
def pobierz(id: str) -> Regula | Tlumaczenie
```

Rejestracja podnosi `WpisBezZrodla`, gdy: identyfikator się powtarza, brakuje `zrodlo`,
`zrodlo.cytat` jest puste, albo katalog nie zawiera wymaganych fixture'ów.

**Warunek akceptacji:** dodanie wpisu to jeden nowy katalog i jeden dekorator. Zero edycji
w istniejących plikach.

### 8.3 `safexml.py`

```python
LIMIT_BAJTOW = 3_145_728        # 3 MB — górny limit KSeF z załącznikiem
LIMIT_CZASU_S = 5.0

def sparsuj(dane: bytes) -> Dokument   # XmlNiebezpieczny | XmlNiepoprawny
```

Kolejność sprawdzeń, każde uzasadnione wynikiem z sekcji 3:

1. **rozmiar przed parsowaniem** — to jest główna obrona przed bombą obliczeniową,
2. **BOM i deklaracja kodowania inna niż UTF-8** → `XmlNiepoprawny`,
3. **obecność `DOCTYPE`** → `XmlNiebezpieczny`. Bez tego XXE nie wycieka, ale dokument
   przechodzi; faktura KSeF nie ma powodu mieć `DOCTYPE`, więc odrzucamy wprost. Wykrycie
   po sparsowaniu przez `drzewo.docinfo.doctype` — sprawdzone, zwraca `'<!DOCTYPE Faktura>'`.
   Parsowanie przed tym sprawdzeniem jest bezpieczne, bo encje nie są rozwijane,
4. **instrukcje przetwarzania** → `XmlNiepoprawny`,
5. parsowanie parserem:

```python
etree.XMLParser(
    resolve_entities=False,   # bomba entyfikacyjna, XXE
    no_network=True,          # zewnętrzne DTD i importy
    load_dtd=False,
    dtd_validation=False,
    huge_tree=False,          # limit głębokości 256 po stronie libxml2
    recover=False,
)
```

Uczciwie o tym, co czym jest chronione: bombę entyfikacyjną odrzuca sam `libxml2` licznikiem
amplifikacji, głębokość powyżej 256 też. Nasz wkład to limit rozmiaru, zakaz `DOCTYPE`
i sprowadzenie parsowania do jednego wejścia, które da się przetestować i pilnować.

Własnego limitu głębokości **nie ma** — byłby zbędny wobec 256 z `libxml2`.

### 8.4 `schema.py`

```python
def wczytaj_schemat() -> etree.XMLSchema          # cache'owane
def mapa_typow() -> Mapping[str, frozenset[str]]  # element → nazwy typów, cache'owane
def sprawdz(dok: Dokument) -> list[BladSchematu]
```

Ustalenie `element` i `typ_xsd` **bez czytania komunikatu**, mechanizmem sprawdzonym w sekcji 3:

1. `error.path` to poprawne wyrażenie XPath, choć pozycyjne (`/*/*[4]/*[15]/*[7]`),
2. wykonaj je na dokumencie → węzeł,
3. `etree.QName(wezel).localname` → nazwa elementu,
4. `mapa_typow()[nazwa]` → nazwa typu XSD.

`mapa_typow()` buduje się z wszystkich plików w `korpus/schema/` po atrybucie `type` deklaracji
`xsd:element`. Daje 250 wpisów, z czego 7 niejednoznacznych — wszystkie to typy złożone, więc
dla błędów wartości mapa jest jednoznaczna. Przy niejednoznaczności `typ_xsd` zostaje `None`,
a dopasowanie schodzi na klucz po `typ_lxml`.

Mapa musi być **deterministyczna**: wartości jako `frozenset`, a wybór przy jednym elemencie
przez `sorted()`. Zbiór iterowany bez sortowania mógłby dać inny `typ_xsd` między uruchomieniami,
a to złamałoby test powtarzalności odpowiedzi z `test_web.py` w sposób trudny do wyśledzenia.

Gdy `error.path` nie da się rozwiązać (bywa przy błędach struktury), `element` zostaje `None`.

### 8.5 `tlumaczenia.py`

```python
@dataclass(frozen=True, slots=True)
class KluczBledu:
    typ_lxml: str | None = None
    typ_xsd: str | None = None
    element: str | None = None

def dopasuj(blad: BladSchematu) -> Tlumaczenie
def na_zastrzezenie(blad: BladSchematu) -> Zastrzezenie
```

Dopasowanie po szczegółowości: `element` bije `typ_xsd`, `typ_xsd` bije `typ_lxml`. Gdy nic nie
pasuje, wchodzi `XSD-zapasowe`, które nazywa pole i linię, a surowy komunikat schowany jest pod
„szczegółami technicznymi". **Nagi komunikat `lxml` nigdy nie jest główną treścią.**

Tłumaczenia mają zawsze wagę `BLAD` — naruszenie schematu oznacza odrzucenie przez KSeF. Wagi
nie ma w metadanych tłumaczenia, bo byłaby polem o jednej możliwej wartości.

**Niezmiennik:** dopasowanie nie zależy od `blad.komunikat`. `test_tlumaczenia.py` zeruje to pole
i sprawdza, że dopasowanie nadal działa; `test_niezmienniki.py` dodatkowo wyszukuje odwołania do
`.komunikat` w katalogach tłumaczeń analizą AST.

### 8.6 `struktura.py` — obejście dla `SCHEMAV_ELEMENT_CONTENT`

Ten jeden kod obsługuje trzy różne problemy, a `error.path` wskazuje **sąsiada, nie winowajcę**
(sekcja 3). Ponieważ to najczęstsza klasa błędu w praktyce, ma dedykowane rozwiązanie.

```python
@dataclass(frozen=True, slots=True)
class RoznicaStruktury:
    rodzic: str
    nadmiarowe: tuple[str, ...]      # dzieci niezadeklarowane na tym poziomie
    brakujace: tuple[str, ...]       # cząstki o minOccurs>=1, nieobecne
    przestawione: tuple[str, ...]    # obecne, ale w innym porządku
    pewnosc_kolejnosci: bool         # False, gdy model zawiera xsd:choice
```

**Uwaga o metodzie, opłacona nieudaną sondą.** Wersja 1 tego specu mówiła „wyciągamy ze schematu
zadeklarowaną sekwencję dzieci". Sprawdziłem: naiwne `complexType.iter(xsd:element)` zwraca dla
`Fa` **222** deklaracje, bo schodzi przez całe zagnieżdżone drzewo, a prawdziwa `Fa` ma 19
dzieci. Na takiej liście „brakujące" wskazałoby dwieście pól, a „kolejność" nie znaczyłaby nic.

Poprawnie trzeba przejść **wyłącznie bezpośrednie cząstki** typu złożonego: dzieci grupy modelu
(`xsd:sequence`, `xsd:choice`, `xsd:all`) na pierwszym poziomie, wchodząc w zagnieżdżone grupy,
ale **nie** w zagnieżdżone typy elementów.

**Sonda potwierdziła, że to działa, i wskazała jeden konkretny brak.** Wyniki na wzorcowej
fakturze MF:

| Typ | Cząstek | Dzieci w fakturze | Nieznane | Fałszywie brakujące |
|---|---|---|---|---|
| `Faktura` | 8 | 5 | brak | brak |
| `Fa` | **53** (nie 222) | 19 | brak | **7** |
| `Podmiot2` | 9 | 6 | brak | brak |
| `FaWiersz` | 25 | 8 | brak | brak |
| `Platnosc` | 13 | 3 | brak | brak |

Co z tego wynika:

- **`nadmiarowe` jest solidne** — zero nieznanych dzieci na wszystkich pięciu typach,
- **`przestawione` działa** — po celowym przestawieniu pierwszego dziecka `Fa` wykryło
  `KodWaluty`,
- **`brakujace` wymaga propagacji `minOccurs` grupy.** `Fa` dało 7 fałszywych trafień:
  `P_13_2`, `P_14_2`, `P_13_4`, `P_14_4`, `P_13_5`, `DaneFaKorygowanej`, `P_15ZK`. Wszystkie
  mają domyślne `minOccurs=1`, ale leżą w **zagnieżdżonych grupach opcjonalnych**. Element jest
  wymagany tylko wtedy, gdy on **i każda grupa nad nim** mają `minOccurs>=1`. To jest cały błąd
  i cała poprawka.

**Kryterium akceptacji jest mechaniczne:** `brakujace` musi być **puste dla wszystkich 26 faktur
złotego korpusu** i dla każdego typu w nich występującego. Fałszywe trafienie na poprawnej
fakturze MF oznacza, że propagacja opcjonalności jest niepełna. To jest dokładnie ten test,
który wyłapał powyższe siedem.

**Kolejność — poprawka wobec pierwszej wersji.** Napisałem, że przy `xsd:choice` nie wolno
orzekać o kolejności. Sonda pokazała, że to zbyt ostrożne: `Fa` **ma** `choice`, a kolejność
i tak wykryła się poprawnie. Ta zasada wyciszyłaby najważniejszy element bez potrzeby.

Poprawnie: kolejność orzekamy dla elementów **spoza gałęzi `choice`**, a elementy wewnątrz
gałęzi są z tego orzeczenia wyłączone. `pewnosc_kolejnosci` opisuje więc nie „czy w ogóle",
a „czy dla wszystkich dzieci".

**Furtka awaryjna:** jeśli propagacja opcjonalności okaże się trudniejsza, niż wygląda, wolno
wypuścić `struktura.py` **bez `brakujace`** — z samym `nadmiarowe` i `przestawione`, które są
sprawdzone. To wciąż zamienia „The element content is not valid" w „pole `KodWaluty` stoi
w niewłaściwym miejscu". Nie wolno natomiast zgadywać winowajcy z treści komunikatu ani
raportować `brakujace`, które zapala się na poprawnych fakturach.

### 8.7 `faktura.py` — fasada

```python
NS = {"tns": "http://crd.gov.pl/wzor/2025/06/25/13775/"}

class Faktura:
    def xp(self, wyrazenie: str) -> list[Any]
    def tekst(self, wyrazenie: str) -> str | None
    def dec(self, wyrazenie: str) -> Decimal | None
    def linia(self, wezel: Any) -> int | None
    def obecny(self, wyrazenie: str) -> bool
    def surowe_bajty(self) -> bytes            # tylko reguły TECHNICZNA
```

`dec()` zwraca `None` przy wartości nieparsowalnej i **nigdy nie podnosi wyjątku**. Reguła
arytmetyczna, która dostała `None`, milczy — wartością zajmuje się XSD. Bez tej zasady jeden
błąd formatu produkowałby lawinę zastrzeżeń arytmetycznych.

### 8.8 `walidacja.py`

```python
def zwaliduj(dane: bytes) -> Wynik
```

Kolejność: `safexml.sparsuj` → **sprawdzenie korzenia** → reguły `TECHNICZNA` →
`schema.sprawdz` → tłumaczenie każdego błędu → **reguły `SEMANTYCZNA` i `ARYTMETYCZNA`
uruchamiane zawsze**, także gdy schemat odrzucił. Gdy odrzucił, `Wynik.czesciowy = True`
i strona to komunikuje.

**Sprawdzenie korzenia jest pierwsze i zwarciowe.** Gdy korzeń nie jest `Faktura`
w przestrzeni `http://crd.gov.pl/wzor/2025/06/25/13775/`, zwracamy **jedno** zastrzeżenie
i kończymy — nie uruchamiamy ani schematu, ani reguł.

Powód jest z sondy: wklejenie strony HTML albo faktury bez przestrzeni nazw daje jeden błąd
`SCHEMAV_CVC_ELT_1` z komunikatem „No matching global declaration available for the validation
root", który dla użytkownika nie znaczy nic. A to najczęstszy błąd początkujących. Sprawdzenie
korzenia pozwala powiedzieć wprost: „to nie wygląda na fakturę FA(3) — korzeń dokumentu to
`html`, a oczekiwany jest `Faktura` w przestrzeni nazw `…/13775/`. Jeśli wklejasz fakturę,
sprawdź, czy nie zgubiłeś atrybutu `xmlns`". Bez tego użytkownik dostaje w najczęstszym
przypadku najgorszy możliwy komunikat.

To zmiana względem wersji 1, która blokowała reguły po błędzie schematu. Powód zmiany:
użytkownik z jednym błędem formatu i pięcioma semantycznymi widziałby jeden. Reguły są już
odporne na braki danych, więc blokada kupowała ostrożność za cenę użyteczności.

Zastrzeżenia sortowane deterministycznie: waga, potem linia, potem identyfikator wpisu. Ta sama
treść wejściowa daje bajtowo tę samą listę — sprawdza to `test_web.py`.

Reguła, która podniesie wyjątek, **nie wywala walidacji** — zostaje zamieniona na zastrzeżenie
`INFORMACJA` o awarii tej reguły, pozostałe lecą dalej. To jedyne dopuszczone `except Exception`
w projekcie. W testach ten sam wyjątek **musi** wywalić test, inaczej zepsuta reguła przechodzi
niezauważona; `conftest.py` przestawia to zachowanie przez `pytest`-owy przełącznik.

### 8.9 Wejścia deweloperskie

```
python -m fa3check.web                 strona na localhost:8000
python -m fa3check waliduj plik.xml    walidacja z terminala
```

Narzędzia deweloperskie, nie produkt. Pakietu nie publikujemy, API biblioteki nie obiecujemy.

## 9. Zawartość rejestrów

### 9.1 Tłumaczenia — klucze zweryfikowane

Wszystkie kody `typ_lxml` poniżej zostały **wywołane eksperymentalnie** (sekcja 3), nie wzięte
z dokumentacji.

| ID | Klucz | Co tłumaczy | Zaczepienie |
|---|---|---|---|
| `XSD-kwota-precyzja` | `typ_lxml=SCHEMAV_CVC_FRACTIONDIGITS_VALID` | za dużo miejsc dziesiętnych. Limit zależy od typu: `TKwotowy` 2, `TIlosci` 6, `TKwotowy2` 8 — podaj ten właściwy | broszura s. 6, pkt 6 |
| `XSD-kwota-zapis` | `typ_lxml=SCHEMAV_CVC_DATATYPE_VALID_1_2_1` | wartość nie jest liczbą — spacja tysięcy, przecinek zamiast kropki. Uwaga: to **nie** `PATTERN_VALID`, bo odpada już na typie bazowym | broszura s. 6, pkt 5 |
| `XSD-wzorzec` | `typ_lxml=SCHEMAV_CVC_PATTERN_VALID` | wartość nie pasuje do wzorca; przy `typ_xsd=TNrNIP` — NIP z myślnikami lub spacjami | broszura s. 6, pkt 10 |
| `XSD-data-zakres` | `typ_lxml=SCHEMAV_CVC_MININCLUSIVE_VALID` / `…MAXINCLUSIVE…` | data poza zakresem. `TDataT`: 2006-01-01 … 2050-01-01. Zakres jest niespodzianką i warto go nazwać wprost | broszura s. 6, pkt 8 |
| `XSD-dlugosc` | `typ_lxml=SCHEMAV_CVC_MAXLENGTH_VALID` / `…MINLENGTH…` | pole za długie albo puste; `TZnakowy512` to 512 znaków, `TZnakowy` 256 | broszura s. 5, pkt 3 |
| `XSD-struktura` | `typ_lxml=SCHEMAV_ELEMENT_CONTENT` | brak pola, pole nadmiarowe albo zła kolejność — **rozstrzygane przez `struktura.porownaj()`**, nie zgadywane | broszura s. 4, definicje pól |
| **`XSD-korzen`** | `typ_lxml=SCHEMAV_CVC_ELT_1` | dokument nie jest fakturą FA(3) albo zgubił przestrzeń nazw. Sprawdzone: to jeden konkretny kod, a komunikat `lxml` brzmi „No matching global declaration available for the validation root" | broszura s. 3, adres wzoru |
| `XSD-zapasowe` | brak klucza | nazwa pola, linia, surowy komunikat pod szczegółami | — |

**`XSD-korzen` jest najwartościowszym wpisem w tabeli**, choć wygląda najbanalniej. Zły albo
zgubiony `xmlns` to najczęstszy błąd początkujących, a obecny komunikat jest kompletnie
nieczytelny. W większości przypadków wyprzedzi go sprawdzenie korzenia z sekcji 8.8, ale
tłumaczenie musi istnieć dla sytuacji, w których korzeń jest poprawny, a niezgodność leży głębiej.

`XSD-struktura` jest najtrudniejszym wpisem — sekcja 8.6 opisuje, dlaczego, i co wolno zrobić,
gdy nie wyjdzie. `XSD-data-zakres` jest najlepszy na pierwszy: kod pojedynczy, granice odczytane
ze schematu, efekt natychmiast widoczny.

### 9.2 Reguły — źródła zweryfikowane

`TECHNICZNA`, źródło `faktury/weryfikacja-faktury.md`:

| ID | Reguła | Waga | Dlaczego XSD tego nie łapie |
|---|---|---|---|
| `TEC-001` | Kodowanie UTF-8 bez BOM | `BLAD` | własność bajtów |
| `TEC-002` | Brak instrukcji przetwarzania XML | `BLAD` | własność dokumentu |
| `TEC-003` | Brak niedozwolonych znaków Unicode | `BLAD` | facety tego nie obejmują |
| `TEC-004` | Rozmiar ≤ 1 MB bez załącznika, ≤ 3 MB z załącznikiem | `BLAD` | własność pliku; reguła sama rozstrzyga który limit po obecności `Zalacznik` |
| `TEC-005` | **Suma kontrolna NIP** | `BLAD` | `TNrNIP` sprawdza wzorzec; wyrażenie regularne nie policzy modulo. Waga `BLAD` jest bezpieczna: sprawdziłem wszystkie 64 NIP-y w złotym korpusie i każdy ma poprawną sumę |
| `TEC-006` | Data wystawienia nie późniejsza niż data przyjęcia | `OSTRZEZENIE` | daty przyjęcia offline nie znamy — sekcja 11 |
| `TEC-007` | Unikalność: NIP sprzedawcy + rodzaj + numer | `INFORMACJA` | zależy od stanu systemu — sekcja 11 |

`TEC-005` jest dowodem sensu drugiego rejestru: schemat przepuści `1234567890`, bo wzorzec się
zgadza, a suma kontrolna nie.

`SEMANTYCZNA`, źródło broszura FA(3):

| ID | Reguła | Waga | Zaczepienie |
|---|---|---|---|
| `SEM-001` | Polski NIP nabywcy musi być w `Podmiot2/DaneIdentyfikacyjne/NIP`, nie w `NrVatUE` ani `NrID` | `BLAD` | s. 6, ramka WAŻNE |

Cytat, sprawdzony jako dosłownie obecny na stronie 6 wyciągu:

> „Polski identyfikator podatkowy NIP nabywcy należy podawać w polu NIP w elemencie
> Podmiot2/DaneIdentyfikacyjne. Nie należy wskazywać go w polu NrVatUE, ani w polu NrID. Faktura
> zostanie odpowiednio udostępniona nabywcy w KSeF wyłącznie, gdy jego identyfikator podatkowy
> NIP ujęto w polu NIP, a nie w polu NrVatUE lub NrID."

Dlaczego to wizytówka projektu: taka faktura **przejdzie XSD i zostanie przyjęta przez KSeF**,
dostanie numer i UPO — a nabywca jej nie zobaczy. Żadna warstwa schematu tego nie złapie, skutek
jest biznesowy, a wyjaśnienie da się napisać tak, że czytający natychmiast rozumie problem.

### 9.3 Skąd biorą się pozostałe reguły

Broszura ma 170 stron. Podział rozdziałów ze stronami jest w `docs/zrodla.md`.

Etap 6 przechodzi rozdziały i produkuje `docs/reguly-z-broszury.md` — numerowaną listę
kandydatów, każdy z numerem strony i dosłownym cytatem. To **dokument, nie kod**. Etap 7
implementuje partiami: `Fa`, `FaWiersz`, `Platnosc`, `Podmiot1`–`3`, resztę.

Pracuje się na `korpus/broszura/broszura-fa3.txt`, nie na PDF-ie. Wyciąg robi
`scripts/pobierz_korpus.py`:

```
pdftotext -layout -enc UTF-8 broszura.pdf broszura-fa3.txt
```

Flaga `-enc UTF-8` jest **obowiązkowa** — bez niej polskie znaki są zepsute (sekcja 3). Znak
wysuwu strony podmieniany jest na wiersz `=== strona N ===`, numerując fizycznie od 1; numer
fizyczny równa się nadrukowanemu, co zostało sprawdzone na 172 stopkach.

Każdy kandydat przechodzi **pytanie kwalifikujące: czy XSD już to łapie?** Jeśli tak, nie
powstaje reguła — powstaje albo poprawia się tłumaczenie. To pytanie odrzuci większość rozdziału
„Formaty pól" i jest to zamierzone.

Lista kategorii `ksefuj` służy wyłącznie jako lista kontrolna pokrycia na końcu etapu 8.

## 10. Wagi zastrzeżeń — zasada wyprowadzona ze źródła

Broszura sama rozdziela obowiązkowość pola od poprawności pliku. O polach `opcjonalny` mówi
(s. 4): *„zapisów dokonuje się obowiązkowo, jeśli jest spełniony warunek ustawowy […];
wypełnienie pola nie jest wymagane dla poprawności semantycznej pliku"*.

| Waga | Kiedy | Przykład |
|---|---|---|
| `BLAD` | naruszenie schematu, sumy kontrolnej, arytmetyki albo obowiązkowości strukturalnej | NIP z błędną sumą kontrolną |
| `OSTRZEZENIE` | pole `opcjonalny` niewypełnione, a kontekst wskazuje na spełniony warunek ustawowy; albo reguła nierozstrzygalna offline, ale prawdopodobna | brak `P_11A` przy danych wskazujących na obowiązek |
| `INFORMACJA` | reguła zależna od stanu systemu | duplikat numeru faktury |

**Nie orzekamy o obowiązkach ustawowych.** Walidator, który mówi księgowemu „naruszyłeś
art. 106e", przekracza kompetencje i będzie się mylił. Mówimy: „to pole jest w strukturze
opcjonalne, ale w Twoim kontekście prawdopodobnie wymagane — sprawdź".

## 11. Reguły niesprawdzalne offline

Trzy reguły przyjęcia KSeF są nierozstrzygalne po jednym pliku:

- **duplikat faktury** — NIP sprzedawcy, rodzaj, numer; KSeF zwraca kod `440`,
- **data przyjęcia** — nadaje ją KSeF; regułę da się sprawdzić tylko względem czasu bieżącego,
- **limit 10 000 faktur w sesji** — dotyczy sesji, nie pliku.

Zostają w rejestrze z wagą `INFORMACJA` albo `OSTRZEZENIE` i z wyjaśnieniem, dlaczego nie
umiemy ich rozstrzygnąć. Wyrzucenie byłoby wygodniejsze i nieuczciwe.

README musi powiedzieć wprost, w dwie strony: **zielony wynik w `fa3-check` nie jest gwarancją
przyjęcia faktury przez KSeF**, a przyjęcie przez KSeF nie jest gwarancją, że faktura jest
poprawna — system nie weryfikuje jej rachunkowej treści.

## 12. Warstwa webowa

```
GET  /            pole tekstowe, strefa upuszczania, informacja o prywatności
POST /waliduj     fragment HTML z wynikiem (HTMX)
GET  /reguly      lista reguł i tłumaczeń ze źródłami — audytowalność na widoku
GET  /zdrowie     status
```

Wynik: werdykt jednym zdaniem, przy wyniku częściowym wyraźna informacja, że schemat odrzucił
dokument i część sprawdzeń mogła nie mieć danych. Potem zastrzeżenia pogrupowane po wadze, każde
zwinięte do jednego wiersza, rozwijalne do pięciu części z cytatem ze źródła. Kliknięcie
podświetla fragment XML-a po numerze linii. Surowy komunikat `lxml` wyłącznie pod „szczegółami
technicznymi".

`GET /reguly` jest małą stroną, a robi najwięcej: pokazuje, że każdy wpis ma źródło, i pozwala
sprawdzić nas bez czytania kodu.

HTMX wendorowany do `static/`, bez CDN. Strona działa bez połączenia z internetem, co jest
spójne z obietnicą, że nic nie wychodzi na zewnątrz.

## 13. Bezpieczeństwo i prywatność

1. **Treść faktury żyje wyłącznie w pamięci obsługi żądania.** Zero zapisu na dysk, bazy,
   cache'u. W logu: znacznik czasu, rozmiar w bajtach, liczba zastrzeżeń, czas przetwarzania,
   kod odpowiedzi. **Nigdy** NIP, numer faktury, fragment XML-a — dotyczy to także logowania
   wyjątków, bo komunikaty `lxml` noszą w sobie treść węzła.
2. **Limit ciała żądania 3 MB**, sprawdzany przed parsowaniem. Nie 1 MB — inaczej legalna
   faktura z załącznikiem zostaje odrzucona przez transport, a nie przez regułę.
3. **Limit czasu na żądanie** i ogranicznik liczby żądań z jednego adresu, pisany ręcznie.
4. **Zero ruchu wychodzącego** w trakcie walidacji. Bez kursów NBP, bez sprawdzania NIP
   w rejestrach, bez telemetrii, bez zewnętrznych czcionek.
5. **Parsowanie wyłącznie przez `safexml.sparsuj`.** `DOCTYPE` odrzucany wprost.
6. **Escapowanie w szablonach.** Komunikaty `lxml` i wartości pól zawierają treść od
   użytkownika. Autoescape Jinja2 włączony, `|safe` zakazane w szablonach wyniku —
   `test_web.py` wstrzykuje `<script>` w pole tekstowe faktury i sprawdza, że w odpowiedzi nie
   ma nieescapowanego znacznika.
7. **Informacja o prywatności przy polu wklejania**, nie w stopce.
8. **Publiczne wdrożenie dopiero po etapie 5.** Do tego momentu wyłącznie `localhost`.
9. **Nigdy nie wysyłamy wklejonego XML-a do żadnego API KSeF.**

Nagłówki: `Content-Security-Policy` bez `unsafe-inline` dla skryptów,
`X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`.

Korpus `korpus/zlosliwe/` i test przepuszczający każdy plik przez `safexml`. **Oczekiwane
zachowanie różni się między wektorami** i test musi to odzwierciedlać, bo inaczej nie przejdzie:

| Plik | Oczekiwanie |
|---|---|
| bomba entyfikacyjna | wyjątek — `libxml2` zgłasza przekroczenie amplifikacji |
| XXE z odczytem pliku | **wyjątek z powodu `DOCTYPE`**; gdyby zakaz zdjąć — dokument przechodzi, ale treść pliku nie wycieka i to trzeba asertować osobno |
| XXE z żądaniem sieciowym | jak wyżej; dodatkowo zero ruchu sieciowego |
| zagnieżdżenie 10 000 poziomów | wyjątek — limit 256 w `libxml2` |
| deklaracja kodowania niezgodna z treścią | wyjątek |
| plik z BOM | wyjątek |
| plik 4 MB | wyjątek przed parsowaniem |

### 13.1 `.gitattributes` — bez tego testy bajtowe kłamią

```
* text=auto eol=lf
*.xml -text
korpus/** -text
```

Reguły `TEC-001` i `TEC-002` działają na bajtach: BOM, kodowanie, znaki. Jeśli git znormalizuje
końce linii w fixture'ach, te same testy dadzą inny wynik na Windowsie i na Linuksie w CI, a
diagnoza zajmie pół dnia. To najtańsza linia obrony w całym projekcie.

## 14. Testy

Zasada: **jeden współdzielony zestaw parametryzowany po rejestrach**. Żaden wpis nie ma własnego
pliku testowego. Nowy wpis dziedziczy cały zestaw automatycznie.

| Plik | Zakres |
|---|---|
| `test_rejestr.py` | `odkryj()` znajduje wszystkie katalogi; identyfikatory unikalne; każdy wpis ma `zrodlo` z niepustym `dokument`, `wersja`, `sekcja`, `cytat`; wymagane fixture'y istnieją |
| **`test_zrodla.py`** | ∀ wpis: `zrodlo.cytat` **występuje dosłownie** w pliku źródłowym po normalizacji białych znaków. Dla broszury dodatkowo `zrodlo.strona` wskazuje stronę, na której cytat się znajduje. Źródła muszą być **wendorowane**: `korpus/broszura/broszura-fa3.txt` oraz `korpus/zrodla/weryfikacja-faktury.md` — inaczej reguły `TECHNICZNA` wymykają się sprawdzeniu. Sprawdza też, że `zrodlo.url` należy do domeny MF |
| **`test_niezmienniki.py`** | analizą AST: `lxml` importowany wyłącznie w `safexml.py`; `reguly/` i `tlumaczenia/` nie importują `web`, `schema`, `walidacja`, `safexml`; brak odwołań do `.komunikat` w katalogach tłumaczeń; brak `float` w adnotacjach w `reguly/`; brak `open(`, `requests`, `datetime.now` w obu rejestrach |
| `test_zloty_korpus.py` | ∀ z 26 przykładów MF: zgodność z XSD **oraz zero zastrzeżeń wagi `BLAD`** |
| `test_reguly.py` | ∀ reguła, **różnicowo**: zbiór zastrzeżeń z `lamie.xml` minus zbiór z `przechodzi.xml` równa się dokładnie tej jednej regule |
| `test_tlumaczenia.py` | ∀ tłumaczenie: `wywoluje.xml` produkuje dopasowany błąd; **po wyzerowaniu `komunikat` dopasowanie nadal działa**; żaden błąd z fixture'ów ani ze złotego korpusu nie wpada w `XSD-zapasowe` |
| `test_struktura.py` | `porownaj()` na przypadkach: brak wymaganego, element nadmiarowy, przestawiona kolejność, kombinacja dwóch — wzorce policzone ręcznie |
| `test_wyjasnienia.py` | ∀ zastrzeżenie: `co`, `dlaczego`, `jak_naprawic` dłuższe niż 20 znaków; `co` zawiera cyfrę albo nazwę pola FA(3); brak zwrotów zakazanych; brak słów „atomic type", „XSD", „facet" w treści widzianej przez użytkownika |
| `test_safexml.py` | ∀ plik z `korpus/zlosliwe/` zgodnie z tabelą w sekcji 13 — **oczekiwanie na wektor, nie jedno dla wszystkich** |
| `test_fuzz.py` | Hypothesis: `sparsuj()` na losowych bajtach i na zmutowanych bajtach złotego korpusu nigdy nie podnosi nic poza `Fa3Error` i mieści się w limicie czasu; `zwaliduj()` zawsze zwraca `Wynik`, nigdy nie rzuca |
| `test_web.py` | żądanie ponad limit odrzucone przed parsowaniem; treść faktury nieobecna w logach (przechwycone logi sprawdzane wzorcem); `<script>` w polu faktury nie trafia nieescapowany do odpowiedzi; ta sama odpowiedź przy powtórzeniu; walidacja złotego korpusu w budżecie czasu |

Cztery z tych plików niosą projekt.

**`test_zrodla.py`** zamienia główną obietnicę projektu w bramkę CI. Wpis z wymyślonym cytatem
nie przechodzi — nie dlatego, że ktoś zauważy, a dlatego, że cytatu nie ma w pliku źródłowym.
Wykonalność sprawdzona: 6 z 6 cytatów odnalezione dosłownie na oczekiwanych stronach.

**`test_niezmienniki.py`** zamienia zasady architektury z prozy w `.cursor/rules` w kod. Prośba
w dokumencie działa, dopóki agent ją pamięta; test działa zawsze.

**`test_zloty_korpus.py`** jest bramką, nie formalnością. Wpis, który odpala się z wagą `BLAD`
na fakturze przykładowej MF, jest zepsuty — nie faktura. Walidator krzyczący na poprawne faktury
jest gorszy niż brak walidatora, bo uczy ignorować ostrzeżenia.

**`test_fuzz.py`** pilnuje jedynego niezmiennika, który naprawdę ma znaczenie dla publicznego
punktu wejścia: cokolwiek wrzucisz, dostaniesz wynik albo zadeklarowany wyjątek — nigdy
`AttributeError` z wnętrza reguły.

Dyscyplina TDD: najpierw test, uruchomiony i zobaczony jako czerwony, potem implementacja. Test,
którego nie widziałeś czerwonego, nie jest testem — jest życzeniem.

Pokrycie ≥ 90% dla `src/fa3check/` poza `web/szablony`.

## 15. CI

GitHub Actions, na push i PR, Python 3.12, 3.13 i 3.14:

1. `ruff check` i `ruff format --check`
2. `mypy --strict src/` — wymaga `lxml-stubs`, bo `lxml` nie ma typów wbudowanych
3. `pytest --cov`
4. sprawdzenie `PROVENANCE`: SHA-256 schematu, 26 przykładów i PDF-a broszury

Punkt 4 chroni przed scenariuszem, w którym ktoś podmienia plik w korpusie, testy dalej są
zielone, a walidator waliduje wobec czegoś innego, niż deklaruje.

Wersja `lxml` przypięta dokładnie, nie zakresem. Aktualizacja może rozsypać słownik tłumaczeń,
więc ma być świadoma i przechodzić przez `test_tlumaczenia.py`.

## 16. Kolejność realizacji

Zmiana względem wersji 1: **korpus jest etapem zerowym.** Powód jest praktyczny — pierwszy wpis
potrzebuje fixture'ów zbudowanych na prawdziwej fakturze MF, a ryzyko zewnętrzne (zmiana
u MF) lepiej poznać w pierwszej godzinie niż w trzeciej.

| Etap | Zakres | Kryterium ukończenia |
|---|---|---|
| 0 | `pyproject`, `LICENSE`, `.gitattributes`, CI, `scripts/pobierz_korpus.py`, `korpus/` z XSD, 26 przykładami, wyciągiem broszury i `weryfikacja-faktury.md`, `PROVENANCE.md` | 26 plików po normalizacji nazw; wyciąg da się grepować po `=== strona N ===`; SHA-256 w CI |
| 1 | `typy.py`, `rejestr.py`, `safexml.py`, `faktura.py`, reguła `SEM-001`, `test_rejestr`, `test_zrodla`, `test_niezmienniki`, `test_reguly`, `test_wyjasnienia`, `test_safexml` | zielony CI; rejestr odrzuca wpis bez cytatu; `test_zrodla` potwierdza cytat `SEM-001` na s. 6 |
| 2 | `schema.py` z mapą typów i rozwiązywaniem `error.path`, `walidacja.py`, `test_zloty_korpus` | 26/26 zgodnych z XSD, zero `BLAD`; element i typ ustalane bez czytania komunikatu |
| 3 | `struktura.py`, `tlumaczenia.py`, siedem wpisów z 9.1, `test_struktura`, `test_tlumaczenia` | test z wyzerowanym komunikatem zielony; zero trafień w `XSD-zapasowe` |
| 4 | reguły `TEC-001` … `TEC-007` | złoty korpus czysty; `TEC-005` udowodniony NIP-em o poprawnym wzorcu i błędnej sumie |
| 5 | `web/`, `korpus/zlosliwe/`, hartowanie, `test_web`, `test_fuzz` | **projekt użyteczny i bezpieczny**; test logów udowodniony jako czerwony po dopisaniu logowania |
| 6 | `docs/reguly-z-broszury.md` — wyciąg rozdziałami, z pytaniem kwalifikującym | lista kandydatów z rozdziałów `Fa` i `FaWiersz`, każdy z cytatem i stroną |
| 7 | reguły `SEMANTYCZNA` i `ARYTMETYCZNA` partiami | po każdej partii złoty korpus czysty i CI zielony |
| 8 | dopracowanie wyjaśnień, lista zwrotów zakazanych, tabela pokrycia | tabela generowana z rejestrów |
| 9 | README; opcjonalnie publiczne wdrożenie | README kompletne |

Warstwa webowa i hartowanie są w jednym etapie celowo: wersja 1 rozdzielała je, co dawało okno,
w którym istnieje strona bez limitów. Skoro i tak nie wolno jej wystawić przed hartowaniem,
rozdzielanie kupowało tylko pozorny postęp.

Etap 6 jest dokumentem, nie kodem, i stoi **po** warstwie webowej. Do tego momentu projekt już
działa i jest użyteczny, a przejście 170 stron PDF-a jest najdłuższą i najnudniejszą częścią
całości. Gdyby stał wcześniej, byłby miejscem, w którym projekt umiera.

Etap 7 idzie partiami i po każdej repo jest kompletne. Jeśli czas skończy się po partii `Fa`
i `FaWiersz`, projekt nadal pokrywa rdzeń każdej faktury.

## 17. Ryzyka

| Ryzyko | Reakcja |
|---|---|
| Aktualizacja `lxml` zmienia kody błędów i rozsypuje słownik | Dopasowanie po `type_name` i typie XSD; wersja przypięta; test z wyzerowanym komunikatem; `test_niezmienniki` blokuje odwołania do `.komunikat` |
| MF zmieni schemat — nazwy typów są tam, gdzie się ich nie spodziewasz | To już się zdarzyło w wersji 1 tego specu. SHA-256 w CI; nazwy typów **zawsze** czytane z `korpus/schema/`, nigdy z pamięci |
| Reguły z broszury okażą się w większości duplikatami XSD | To wiemy i jest w architekturze: pytanie kwalifikujące w etapie 6 przekieruje je do tłumaczeń |
| `struktura.py` — `brakujace` może dawać fałszywe trafienia | Sprawdzone: `nadmiarowe` i `przestawione` działają, `brakujace` wymaga propagacji `minOccurs` grup nadrzędnych. Kryterium mechaniczne: puste `brakujace` na wszystkich 26 fakturach. Furtka: wypuścić bez `brakujace` |
| Wklejenie czegoś, co nie jest fakturą, daje nieczytelny komunikat | Sprawdzenie korzenia przed walidacją (8.8) plus tłumaczenie `XSD-korzen` |
| Wyciąg reguł z 170 stron przeciągnie się i zabije projekt | Etap 6 to dokument; etap 7 partiami; repo pokazywalne od etapu 5 |
| Wpis daje fałszywy alarm na prawdziwej fakturze | Złoty korpus jako bramka CI; w konflikcie wpis przegrywa z fakturą MF |
| Wyjaśnienia zdegenerują się do ogólników | `test_wyjasnienia.py` z listą zwrotów zakazanych, rosnącą przy każdym wpadniętym ogólniku |
| Pokusa dopisania reguły „z głowy" | `test_zrodla.py` — cytatu nie ma w pliku źródłowym, więc wpis nie przechodzi CI |
| Końce linii psują testy bajtowe między Windowsem i CI | `.gitattributes`, sekcja 13.1 |
| Publiczne demo a dane handlowe | Lokalnie w pierwszej kolejności; demo po etapie 5; treść tylko w pamięci |
| Lawina zastrzeżeń przy jednym błędzie formatu | `dec()` zwraca `None`, reguły arytmetyczne milczą |
| Porównanie z `ksefuj` wypadnie niekorzystnie | Sekcja „stan sztuki" wprost, z przyznaniem, w czym jesteśmy słabsi |
| Projekt wygląda jak kolejny walidator | README otwiera się przykładem jednego pełnego wyjaśnienia, nie listą funkcji |

## 18. Źródła

Pełna bibliografia: `docs/zrodla.md`. Dokumenty rozstrzygające:

- **Schemat:** `schemat_FA(3)_v1-0E.xsd` (183 798 B) plus `bazowe/ElementarneTypyDanych_v10-0E.xsd`
  (12 154 B), `KodyKrajow_v10-0E.xsd` (39 446 B), `StrukturyDanych_v10-0E.xsd` (31 473 B);
  namespace `http://crd.gov.pl/wzor/2025/06/25/13775/`
- **Broszura informacyjna dotycząca struktury logicznej FA(3)**, Warszawa, marzec 2026, wersja
  z 2026-03-04, 170 stron — źródło tłumaczeń oraz reguł `SEMANTYCZNA` i `ARYTMETYCZNA`
- **`faktury/weryfikacja-faktury.md`** z repozytorium `CIRFMF/ksef-docs` (MIT) — źródło reguł
  `TECHNICZNA`
- **Przykładowe pliki dla struktury logicznej FA(3)** — 26 faktur, złoty korpus, wszystkie
  zgodne z XSD
