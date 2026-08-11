---
name: audyt-zrodel
description: Audytuje repozytorium fa3-check pod kątem niezmienników — źródła przy wpisach, brak reguł duplikujących XSD, dopasowanie tłumaczeń niezależne od treści komunikatu, jakość wyjaśnień, jedno wejście do parsowania XML, brak float w kwotach, brak wycieku treści faktury do logów. Użyj po zakończeniu etapu, przed commitem większej partii wpisów albo gdy prośba dotyczy sprawdzenia, czy projekt trzyma swoje zasady.
---

# Audyt niezmienników

Sprawdzasz, czy repozytorium trzyma to, co obiecuje. **Każdy punkt kończysz dowodem — wynikiem
polecenia albo cytatem z pliku. Nie deklaracją, że sprawdziłeś.**

Raport ma być krótki i konkretny: przy każdym punkcie `SPEŁNIONY` z dowodem albo `ZŁAMANY`
z listą miejsc.

## 1. Żadna reguła nie duplikuje XSD

**Najważniejszy punkt tego audytu**, bo dotyczy zasady, z której wynika cała architektura:
reguła, którą łapie XSD, nie jest regułą — jest tłumaczeniem.

Przejdź wszystkie wpisy w `src/fa3check/reguly/` i dla każdego odpowiedz, **czym dokładnie**
schemat tego nie wyraża. Dopuszczalne uzasadnienia to: arytmetyka między polami (XSD 1.0 nie ma
`xs:assert`), zależność między odległymi elementami, suma kontrolna (wzorzec nie policzy modulo),
własność bajtów, zależność od stanu systemu.

Zgłoś jako złamane każdą regułę, która sprawdza: liczbę miejsc dziesiętnych, długość pola, format
daty, wzorzec identyfikatora, obecność wymaganego elementu, kolejność elementów. To wszystko
schemat FA(3) wymusza facetami `fractionDigits`, `totalDigits`, `maxLength`, `pattern`,
`minInclusive`, `minOccurs` i `xsd:sequence`. Pokaż fragment schematu jako dowód.

Sprawdź też z drugiej strony: czy `zrodlo.md` każdej reguły zawiera zdanie o tym, dlaczego XSD
tego nie łapie. Brak tego zdania to sygnał, że nikt nie zadał pytania kwalifikującego.

## 2. Każdy wpis ma źródło z cytatem

Przejdź wszystkie katalogi w `src/fa3check/reguly/` **i** `src/fa3check/tlumaczenia/`. Zbuduj
tabelę: identyfikator, rejestr, poziom, dokument, sekcja, strona, długość cytatu, obecność
`zrodlo.md`, obecność wymaganych fixture'ów.

Zgłoś jako złamane:

- puste albo brakujące `zrodlo.cytat`,
- cytat, który jest **parafrazą** — brzmi jak zdanie programisty, nie jak urzędowy dokument.
  To jest ocena jakościowa i masz ją wykonać, nie pominąć. Cytat urzędowy ma charakterystyczną
  składnię: „Kwoty podawane są co do zasady…", „Wartość należy wpisać…",
- brak numeru strony przy wpisach, których źródłem jest broszura,
- `strona` poza zakresem rozdziału podanego w `docs/zrodla.md` — na przykład wpis dotyczący
  `FaWiersz` (86–103) ze stroną 12,
- brak pliku `zrodlo.md` albo `zrodlo.md` bez sekcji „Czego wpis nie sprawdza",
- dwa wpisy z identycznym cytatem — jeden z nich jest prawdopodobnie zbędny.

## 3. Dopasowanie tłumaczeń nie zależy od treści komunikatu

Poszukaj w `src/fa3check/tlumaczenia.py` i we wszystkich katalogach `tlumaczenia/` odwołań do
`blad.komunikat`, `.komunikat`, `message`, oraz operatorów `in`, `startswith`, `find`,
`re.search` zastosowanych do tekstu komunikatu.

**Dozwolone wyłącznie** przypisanie komunikatu do pola `diagnostyka`. Każde użycie do dopasowania
albo do budowania `co` / `dlaczego` / `jak_naprawic` jest złamaniem niezmiennika.

Uruchom `test_tlumaczenia.py` i potwierdź, że test z wyzerowanym polem `komunikat` faktycznie
istnieje i przechodzi. Jeśli go nie ma — to jest poważniejsze niż samo naruszenie, bo znaczy, że
niezmiennik nie jest pilnowany.

Sprawdź też, czy wersja `lxml` w `pyproject.toml` jest przypięta dokładnie, a nie zakresem.

## 4. Wyjaśnienia nie są ogólnikami

Zbierz zastrzeżenia produkowane przez wszystkie fixture'y `lamie.xml` i `wywoluje.xml` i przeczytaj
je jak księgowy, który nie wie, co to XSD.

Zgłoś każde, w którym:

- `co` nie zawiera ani liczby z faktury, ani nazwy pola FA(3),
- `dlaczego` jest tautologią („pole jest niezgodne, bo nie spełnia wymogu"),
- `dlaczego` **przewiduje reakcję KSeF, której nie ma w dokumentacji** — szczególnie zdania
  w rodzaju „KSeF odrzuci fakturę, bo sumy się nie zgadzają". KSeF nie weryfikuje rachunkowej
  treści faktury i takie zdanie wprowadza użytkownika w błąd,
- `jak_naprawic` nie mówi, co zrobić, tylko powtarza, co jest źle,
- w treści widzialnej dla użytkownika pojawia się surowy komunikat `lxml` albo słowa „atomic
  type", „XSD", „schema validation",
- którekolwiek z trzech pól jest krótsze niż 20 znaków.

Zaproponuj rozszerzenie listy zwrotów zakazanych w `tests/test_wyjasnienia.py` o wszystko, co
znalazłeś.

## 5. Jedno wejście do parsowania XML

To jest cały mechanizm bezpieczeństwa tego projektu.

Poszukaj w `src/` wystąpień `XMLParser`, `fromstring`, `etree.parse`, `xml.etree`, `minidom`,
`xmltodict`. **Dozwolone wyłącznie w `src/fa3check/safexml.py`.** Pokaż wynik wyszukiwania, nie
podsumowanie.

Sprawdź, czy parser w `safexml.py` ma nadal wszystkie flagi z sekcji 8.3 specu:
`resolve_entities=False`, `no_network=True`, `load_dtd=False`, `dtd_validation=False`,
`huge_tree=False`, `recover=False`. Brak którejkolwiek to otwarta dziura.

## 6. Brak `float` w kwotach

Poszukaj `float(`, `: float`, `-> float` w `src/fa3check/`. W kodzie dotyczącym kwot, kursów
i ilości niedozwolone. Dopuszczalne wyłącznie w pomiarach czasu i rozmiaru.

Sprawdź też, czy `faktura.dec()` zwraca `Decimal` i nigdy nie podnosi wyjątku przy wartości
nieparsowalnej, oraz czy reguły arytmetyczne faktycznie milczą po otrzymaniu `None`.

## 7. Wpisy nie wiedzą o resztcie systemu

Poszukaj w `src/fa3check/reguly/` i `src/fa3check/tlumaczenia/` importów z `web`, `schema`,
`walidacja`, `safexml`. Żaden nie jest dozwolony.

Poszukaj też oznak nieczystości: `open(`, `requests`, `httpx`, `datetime.now`, `time.time`,
`random`, zmiennych modułowych, które nie są `frozenset` ani stałą.

## 8. Treść faktury nie wycieka

W `src/fa3check/web/` poszukaj wywołań logowania i sprawdź, co jest ich argumentem. Zgłoś każde,
które przekazuje treść żądania, węzeł XML, komunikat `lxml` albo cały obiekt zastrzeżenia.

Osobno sprawdź `logger.exception` i `logger.error` z surowym wyjątkiem — wyjątki `lxml` noszą
w komunikacie fragment dokumentu i to jest najczęstsza droga wycieku w takiej aplikacji.

Sprawdź, czy `tests/test_web.py` nadal zawiera test przechwytujący logi i szukający w nich NIP-u.

## 9. Rejestr jest szczelny

Sprawdź, czy `rejestr.py` nadal podnosi wyjątek przy: duplikacie identyfikatora, braku `zrodlo`,
pustym `zrodlo.cytat`, braku wymaganego fixture'a. Uruchom te przypadki, nie czytaj samego kodu —
warunek zakomentowany „na chwilę" wygląda w kodzie prawie tak samo jak działający.

## 10. Nic ponad spec

Wypisz wszystko, co jest w repozytorium, a nie ma uzasadnienia w
`docs/spec/2026-08-11-fa3-check-design.md`: moduły, klasy, opcje konfiguracyjne, zależności, trasy
HTTP, warstwy abstrakcji z jedną implementacją.

Założenie robocze: coś takiego **jest**. Agenci dokładają warstwy „na przyszłość", a to jest
dokładnie ten rodzaj kodu, który sprawia, że mały projekt wygląda na przekombinowany.

Zaproponuj usunięcie każdego takiego elementu. Nie usuwaj bez zgody.

## Na koniec

Podaj liczby: ile wpisów w każdym rejestrze z podziałem na poziomy, ile ma numer strony, ile
reguł ma uzasadnienie „dlaczego XSD tego nie łapie", ile jest rozstrzygalnych offline, ile
zastrzeżeń trafiło na listę do poprawy. Te liczby idą potem do tabeli pokrycia w README, więc
niech będą policzone z rejestrów, a nie oszacowane.
