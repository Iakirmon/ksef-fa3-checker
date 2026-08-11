# fa3-check

Walidator faktury ustrukturyzowanej FA(3) z warstwą webową. Python 3.12+, FastAPI, Jinja2, HTMX.

**Dokument nadrzędny:** `docs/spec/2026-08-11-fa3-check-design.md`. Gdy kod i spec się
rozjeżdżają, wygrywa spec, a rozbieżność zgłoś.

**Bibliografia źródeł:** `docs/zrodla.md`. Reguła walidacyjna, której nie da się zaczepić
w jednym z tych dokumentów, nie istnieje.

Pełne zasady dla Cursora są w `.cursor/rules/`. Ten plik jest skrótem dla narzędzi, które ich
nie czytają.

## Obietnica projektu

> Każda reguła mówi, skąd się wzięła. Każdy błąd mówi, co z nim zrobić.

Środek ciężkości leży nie w liczbie reguł, a w ich audytowalności i w jakości wyjaśnień.
Istnieje kilka walidatorów FA(3), w tym `ksefuj` z 44 regułami — nie wygrywamy liczbą reguł
i nie próbujemy. Mając do wyboru dodanie dwudziestej reguły albo poprawienie wyjaśnienia
w istniejącej, poprawiaj wyjaśnienie.

## Dwa rejestry

> **Reguła, którą łapie XSD, nie jest regułą — jest tłumaczeniem.**

Schemat FA(3) to XML Schema 1.0 z pełnym zestawem facetów: `fractionDigits`, `totalDigits`,
`maxLength`, `pattern`, `minInclusive`. Precyzja kwot, formaty dat, długości pól i wzorce NIP-ów
są już wymuszone przez `lxml`. Pisanie na to reguły to duplikowanie schematu.

| Rejestr | Co tam wchodzi |
|---|---|
| `src/fa3check/tlumaczenia/` | wszystko, co XSD łapie — zamieniamy komunikat `lxml` na wyjaśnienie |
| `src/fa3check/reguly/` | wyłącznie to, czego XML Schema 1.0 wyrazić nie umie |

Poza zasięgiem XSD 1.0 zostaje: arytmetyka (brak `xs:assert`), zależności między odległymi
polami, sumy kontrolne (wzorzec nie policzy modulo), własności bajtów (BOM, instrukcje
przetwarzania, rozmiar) i reguły zależne od stanu systemu.

**Przed napisaniem reguły sprawdź w `korpus/schema/`, czy schemat już tego nie wymusza.**

## Niezmienniki

1. Reguła w `src/fa3check/reguly/` i tłumaczenie w `src/fa3check/tlumaczenia/` importują wyłącznie
   z `typy`, `rejestr`, `faktura` i biblioteki standardowej. Nigdy z `web`, `schema`, `walidacja`,
   `safexml`.
2. Reguła jest funkcją czystą: bez stanu, plików, sieci i zegara.
3. `safexml.py` jest **jedynym** miejscem, które parsuje XML. `etree.XMLParser`,
   `etree.fromstring` i `etree.parse` nie mają prawa wystąpić nigdzie indziej — domyślny parser
   `lxml` rozwiązuje encje, więc drugie miejsce parsowania to gotowa dziura XXE. Wymusza to
   `test_niezmienniki.py` analizą AST.
4. `safexml` odrzuca `DOCTYPE` wprost. Sprawdzone: przy `resolve_entities=False` XXE nie wycieka,
   ale dokument **przechodzi bez błędu**. Faktura KSeF nie ma powodu mieć `DOCTYPE`.
5. Nazwy typów XSD odczytujesz z `korpus/schema/`, nigdy z pamięci. FA(3) używa `TKwotowy`
   (18/2), `TKwotowy2` (22/8), `TIlosci` (22/6), `TDataT` (2006-01-01…2050-01-01),
   `TZnakowy512` — nie `TKwota2` ani `TData`, które istnieją w schemacie bazowym, ale nie dla
   tych pól.
6. Kwoty wyłącznie `Decimal`. `float` w kodzie liczącym pieniądze to błąd.
7. Dopasowanie tłumaczeń **nigdy po treści komunikatu** `lxml` — wyłącznie po `error.type_name`,
   nazwie typu XSD i nazwie elementu. `error.path` zwraca ścieżkę **pozycyjną**, więc nazwę
   elementu uzyskujesz, wykonując ją jako XPath na dokumencie. Surowy komunikat trafia tylko do
   pola `diagnostyka`.
8. Każdy wpis ma `Zrodlo` z **dosłownym cytatem** z dokumentu MF, który musi występować
   dosłownie w `korpus/broszura/broszura-fa3.txt` na podanej stronie. Sprawdza to
   `test_zrodla.py` — to bramka CI, nie obietnica.
9. Wpis przegrywa z fakturą przykładową MF. Gdy odpala się z wagą `BLAD` na którymkolwiek
   z 26 plików w `korpus/zloty/`, zepsuty jest wpis — nie faktura. Wszystkie 26 są zgodne z XSD.
10. Treść faktury nigdy nie trafia do logu, na dysk ani do bazy. W logu wyłącznie znacznik czasu,
    rozmiar w bajtach, liczba zastrzeżeń i czas przetwarzania. Dotyczy to także logowania
    wyjątków — komunikaty `lxml` noszą w sobie treść węzła.
11. Nie orzekamy o obowiązkach ustawowych. Mówimy, co jest niezgodne ze strukturą, formatem albo
    arytmetyką — nie że ktoś naruszył przepis. Nie przewidujemy też reakcji KSeF, której nie ma
    w dokumentacji: system nie weryfikuje rachunkowej treści faktury.

## Czego nie wymyślasz

Kodów błędów KSeF, nazw pól FA(3), limitów i długości, reguł arytmetycznych „bo tak wynika
z VAT-u". Wszystko to ma konkretne miejsca w dokumentach z `docs/zrodla.md`. Materiałów
wtórnych — blogów, artykułów o „najczęstszych błędach KSeF", dokumentacji cudzych systemów —
wolno użyć wyłącznie do znalezienia właściwego miejsca w dokumencie MF, nigdy do treści reguły.

Gdy nie wiesz: powiedz, że nie wiesz, i powiedz, którego dokumentu potrzebujesz. To jest
poprawna odpowiedź.

Szczegóły: `.cursor/rules/30-zrodla.mdc`.

## Tryb pracy

Jeden etap z sekcji 16 specu na raz. TDD obowiązkowe: najpierw test, uruchomiony i pokazany jako
czerwony, potem implementacja.

Po każdym etapie i po każdej nowej regule:

```
ruff check . ; if ($?) { mypy --strict src/ } ; if ($?) { pytest -q }
```

Nie twierdź, że coś jest gotowe, dopóki nie zobaczysz wyniku. Nie commituj i nie pushuj bez
wyraźnej prośby. Nie refaktoryzuj poprzednich etapów bez prośby.

## Uruchomienie

```
python -m fa3check.web                 strona na localhost:8000
python -m fa3check waliduj plik.xml    walidacja z terminala
```

Oba są narzędziami deweloperskimi, nie produktem. Pakietu nie publikujemy, stabilnego API
biblioteki nie obiecujemy.
