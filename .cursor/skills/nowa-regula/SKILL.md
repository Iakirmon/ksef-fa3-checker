---
name: nowa-regula
description: Dodaje jeden wpis do fa3-check — regułę walidacyjną albo tłumaczenie komunikatu XSD. Użyj, gdy prośba dotyczy dodania, zmiany albo usunięcia sprawdzenia na fakturze FA(3), poprawienia komunikatu błędu, albo gdy powstaje nowy katalog w src/fa3check/reguly/ lub src/fa3check/tlumaczenia/.
---

# Nowy wpis

Dodajesz **jeden** wpis. Jeśli warunek rozpada się na dwa niezależne sprawdzenia z dwoma różnymi
cytatami — to są dwa wpisy i wracasz z pytaniem, który robimy pierwszy.

Kontrakt: `.cursor/rules/10-reguly.mdc`. Zakaz wymyślania: `.cursor/rules/30-zrodla.mdc`.
Oba przeczytaj, zanim napiszesz linię kodu.

## Krok 1 — pytanie kwalifikujące: reguła czy tłumaczenie?

**To jest pierwszy krok i nie wolno go pominąć.**

> Czy XSD już to łapie?

Otwórz `korpus/schema/` i sprawdź, czy schemat wymusza ten warunek facetem: `fractionDigits`,
`totalDigits`, `maxLength`, `minLength`, `pattern`, `minInclusive`, `maxInclusive`, `enumeration`,
`minOccurs`, kolejność w `xsd:sequence`. Sprawdź w pliku, nie w pamięci.

| Odpowiedź | Co robisz |
|---|---|
| **XSD to łapie** | To nie jest reguła. Idź do części „Tłumaczenie" — dodaj albo popraw wpis w `tlumaczenia/` |
| **XSD tego nie umie wyrazić** | To jest reguła. Idź do części „Reguła" |

Poza zasięgiem XML Schema 1.0 są: arytmetyka między polami (brak `xs:assert`), zależności między
odległymi elementami, sumy kontrolne (wzorzec nie policzy modulo), własności bajtów (BOM,
instrukcje przetwarzania, rozmiar) i reguły zależne od stanu systemu.

Pokaż użytkownikowi wynik tego sprawdzenia razem z fragmentem schematu. Reguła duplikująca XSD
zostanie odrzucona przy audycie, więc lepiej to rozstrzygnąć teraz.

## Krok 2 — źródło, przed kodem

Zacznij od cytatu, nie od implementacji. Ustal i pokaż użytkownikowi:

- **dokument** i jego wersję (z `docs/zrodla.md`),
- **sekcję** i **numer strony**,
- **dosłowny cytat** — przepisany z dokumentu, z jego interpunkcją.

Jeśli nie masz cytatu, **zatrzymaj się tutaj**. Powiedz, którego fragmentu potrzebujesz, i poproś
o niego. Nie ma cytatu — nie ma wpisu, i to nie jest przeszkoda do obejścia.

Sprawdź też, czy wpis już nie istnieje: przejrzyj identyfikatory w obu rejestrach i cytaty
w plikach `zrodlo.md`. Dwa wpisy na jeden cytat to znak, że któryś jest zbędny.

---

# Reguła

## Identyfikator i poziom

| Poziom | Prefiks | Kiedy |
|---|---|---|
| `TECHNICZNA` | `TEC` | własności bajtów, sumy kontrolne, reguły przyjęcia KSeF |
| `SEMANTYCZNA` | `SEM` | zależność między polami |
| `ARYTMETYCZNA` | `ARY` | rachunek |

Numer kolejny w ramach prefiksu. Katalog nazywa się **dokładnie** identyfikatorem.

Wagę ustal według zasady z sekcji 10 specu, wyprowadzonej z broszury — nie według tego, jak
poważnie brzmi błąd. Brak pola `opcjonalny` **nigdy** nie jest `BLAD`.

## Fixture'y, przed implementacją

```
src/fa3check/reguly/<ID>/fixtures/przechodzi.xml
src/fa3check/reguly/<ID>/fixtures/lamie.xml
```

Zbuduj je na bazie faktury z `korpus/zloty/` — realnego przykładu MF, nie minimalnego pliku
skrojonego pod regułę. `lamie.xml` powstaje z `przechodzi.xml` przez **jedną** zmianę, bo
`test_reguly.py` wymaga, żeby odpalił dokładnie tę jedną regułę.

**Dla reguł `SEMANTYCZNA` i `ARYTMETYCZNA`: `lamie.xml` musi przechodzić walidację XSD.**
Sprawdź to i pokaż wynik. Jeśli nie przechodzi, wróciłeś do kroku 1 z błędną odpowiedzią — to
jest przypadek dla tłumaczenia. XSD jest bramką dla reguł semantycznych, więc reguła z fixture'em
łamiącym schemat nigdy się nie uruchomi w prawdziwym przebiegu.

## Test na czerwono

Uruchom `pytest -q` i **pokaż użytkownikowi czerwony wynik**. Współdzielone testy wykryją nowy
katalog automatycznie. Jeśli nie wykryły — zepsuty jest rejestr i to jego naprawiasz, nie test.

## Implementacja

Wzorzec w `.cursor/rules/10-reguly.mdc`. Rzeczy, które łatwo złamać:

- importy tylko z `fa3check.typy`, `fa3check.rejestr`, `fa3check.faktura` i stdlib,
- dostęp do dokumentu wyłącznie przez fasadę `Faktura`, nigdy własny XPath z namespace'em,
- kwoty przez `f.dec()`, wyłącznie `Decimal`; gdy `f.dec()` zwróci `None`, **reguła milczy**,
- `f.surowe_bajty()` tylko w regułach `TECHNICZNA`,
- listy pól jako stałe modułowe `frozenset`, nie wplecione w kod,
- funkcja czysta: bez sieci, bez plików, bez `datetime.now()`.

---

# Tłumaczenie

## Identyfikator i klucz

Identyfikatory opisowe, nie po nazwie typu: `XSD-kwota-precyzja`, `XSD-kwota-zapis`,
`XSD-wzorzec`, `XSD-data-zakres`, `XSD-dlugosc`, `XSD-struktura`, `XSD-zapasowe`. Nazwa typu
może się zmienić przy nowym wzorze faktury, opis problemu nie.

`KluczBledu` składa się z `typ_lxml` (`error.type_name`), `typ_xsd` (nazwa typu ze schematu)
i `element` (nazwa lokalna). Wypełnij najmniej pól, ile wystarcza — dopasowanie idzie po
szczegółowości i zbyt wąski klucz zostawi błędy w tłumaczeniu zapasowym.

## Zasada, której nie wolno złamać

**Dopasowanie nigdy po treści komunikatu.** Jeśli w Twoim kodzie pojawia się
`"not a valid value" in blad.komunikat` albo cokolwiek podobnego — `test_tlumaczenia.py` upadnie
i ma upaść. Brzmienie komunikatów `libxml2` zmienia się między wersjami.

Surowy komunikat `lxml` trafia wyłącznie do pola `diagnostyka`, nigdy do `co`, `dlaczego`
ani `jak_naprawic`.

## Fixture

```
src/fa3check/tlumaczenia/<ID>/fixtures/wywoluje.xml
```

Faktura, która wywołuje **ten konkretny** błąd XSD. Zbudowana z faktury ze złotego korpusu przez
jedną zmianę.

## Wartości graniczne

Bierz je ze schematu, nie z pamięci. Prawdziwe, odczytane z
`korpus/schema/bazowe/ElementarneTypyDanych_v10-0E.xsd`:

| Typ | Facety | Gdzie |
|---|---|---|
| `TKwotowy` | `totalDigits=18`, `fractionDigits=2` | `P_15`, `P_11` |
| `TKwotowy2` | `totalDigits=22`, `fractionDigits=8` | `P_9A`, `P_9B` |
| `TIlosci` | `totalDigits=22`, `fractionDigits=6` | `KursWaluty` |
| `TDataT` | `2006-01-01` … `2050-01-01` | `P_1`, `P_6` |
| `TZnakowy512` | `maxLength=512` | `Nazwa` |
| `TNrNIP` | `pattern=[1-9]((\d[1-9])\|([1-9]\d))\d{7}` | `NIP` |

`TKwota2` i `TData` istnieją w schemacie bazowym, ale FA(3) **nie używa ich do tych pól** —
pierwsza wersja specu pomyliła się dokładnie tutaj. Otwórz plik i sprawdź, zanim wpiszesz
jakąkolwiek liczbę do wyjaśnienia.

---

# Wspólne — wyjaśnienie

To jest krok, w którym powstaje wartość tego projektu, i jednocześnie ten, który najłatwiej
odbębnić.

Napisz `co`, `dlaczego` i `jak_naprawic` tak, jakby czytał je księgowy, który pierwszy raz widzi
odrzuconą fakturę i nie wie, co to XSD.

- `co` zawiera **liczby z tej konkretnej faktury** i nazwę pola,
- `dlaczego` mówi o skutku: dla KSeF, dla nabywcy, dla rozliczenia. **Nie przewiduj reakcji
  KSeF, której nie ma w dokumentacji** — system nie weryfikuje rachunkowej treści faktury, więc
  „KSeF odrzuci, bo sumy się nie zgadzają" jest nieprawdą,
- `jak_naprawic` mówi w trybie rozkazującym, co zrobić — i jeśli istnieje właściwe pole
  alternatywne, wskazuje je.

Zwroty zakazane są w `tests/test_wyjasnienia.py`. Jeśli Twoje wyjaśnienie brzmi jak jeden z nich,
przepisz je, a nie obchodź test synonimem.

# Wspólne — `zrodlo.md`

Cztery sekcje: **Cytat** (dłuższy niż w dekoratorze, z kontekstem i stroną), **Interpretacja**
(jak z cytatu wynika ta implementacja), **Wyjątki** (czego nie dotyczy i skąd o tym wiadomo —
albo słowo „brak"), **Czego wpis nie sprawdza** (granica; najczęściej pomijana i najbardziej
przydatna sekcja).

Dla reguł dopisz jedno zdanie: **dlaczego XSD tego nie łapie.** To jest uzasadnienie istnienia
wpisu w tym rejestrze i pierwsza rzecz, którą sprawdzi audyt.

# Wspólne — zielono i złoty korpus

```
pytest -q
```

Muszą przejść: `test_rejestr.py`, `test_reguly.py` albo `test_tlumaczenia.py`,
`test_wyjasnienia.py` i **`test_zloty_korpus.py`**.

Jeśli nowy wpis odpala się z wagą `BLAD` na którymkolwiek z 26 przykładów MF — **wpis jest
zepsuty, nie faktura**. Rozstrzygnij, co dokładnie źle zrozumiałeś w źródle. Nie dopisuj wyjątku,
żeby korpus przeszedł, dopóki nie potrafisz pokazać w dokumencie, że ten wyjątek tam jest.

# Raport

Na koniec podaj: identyfikator, rejestr, poziom, wagę, cytat ze stroną, odpowiedź na pytanie
kwalifikujące z fragmentem schematu, wynik `pytest -q` i jedno zdanie o tym, czego wpis **nie**
sprawdza.
