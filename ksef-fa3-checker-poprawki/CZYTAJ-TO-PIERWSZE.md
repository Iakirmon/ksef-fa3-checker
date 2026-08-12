# Poprawki do ksef-fa3-checker — jak tego użyć

Paczka zawiera **spec poprawek i prompty**, nie kod. Projekt działa; to lista sześciu defektów
z dowodami i kryteriami odbioru.

## Co wrzucić i gdzie

Rozpakuj do katalogu repozytorium `ksef-fa3-checker`. Pliki trafią na swoje miejsca:

```
docs/spec/2026-08-12-poprawki-design.md            spec poprawek — dokument główny
docs/spec/2026-08-12-cursor-prompty-poprawki.md    prompty, jeden czat na defekt
scripts/zmien_nazwy_wpisow.py                      gotowy skrypt do defektu D
CZYTAJ-TO-PIERWSZE.md                              ten plik — możesz go potem usunąć
```

Nic nie nadpisuje istniejących plików. Spec z 11 sierpnia zostaje dokumentem nadrzędnym; nowy
go uzupełnia i w trzech punktach koryguje.

## Od czego zacząć

Nowy czat w Cursorze, potem:

```
Przeczytaj @docs/spec/2026-08-12-poprawki-design.md i wykonaj defekt A z sekcji 1.
```

Dalej po jednym defekcie na czat, w kolejności z sekcji 8 specu: **A → D → B → C → E → F**.
Prompty są gotowe w `2026-08-12-cursor-prompty-poprawki.md`.

Defekt A jest pierwszy, bo trwa minutę i daje zieloną bazę do porównania. Defekt D przed B,
bo B tworzy nowe katalogi tłumaczeń — lepiej, żeby od razu powstały z poprawną nazwą.

## Stan wyjściowy — punkt odniesienia

Zmierzone 12 sierpnia na commicie `7ca2fae`:

| | |
|---|---|
| `pytest` | 137 zielonych |
| `mypy --strict` (z wykluczeniami) | czysto, 14 plików |
| `ruff format --check` | czysto, 80 plików |
| `ruff check` | **2 błędy `I001`** — jedyna przyczyna czerwonego CI |
| PROVENANCE | OK, 32 pliki |
| Złoty korpus | 26/26 bez `BLAD`, ale 26 × `TEC-006` + 26 × `TEC-007` |
| Pokrycie | 87% |

Jeśli po którejkolwiek poprawce testów jest mniej niż 137 albo któryś pada — cofnij się, zanim
pójdziesz dalej.

## Trzy rzeczy, które trzeba wiedzieć od razu

**Trzy z sześciu defektów wynikają z błędów w specu z 11 sierpnia, nie z implementacji.**
Oznaczone w specu jako `[błąd specu]`. W tych przypadkach poprawia się regułę projektu, a nie
kod, który tę regułę wiernie wykonał. Dotyczy to defektów C, D i F.

**Defekt D został wykonany i przetestowany**, nie zaproponowany. Zmiana nazw 21 katalogów na
poprawne identyfikatory Pythona: 137 testów zielonych, `mypy --strict src/` obejmuje **35 plików
zamiast 14** i przechodzi bez zastrzeżeń, zero zmian w kodzie poza nazwami i konfiguracją.
Gotowy skrypt: `scripts/zmien_nazwy_wpisow.py`.

**Defekt B jest największy i ma dwa wystąpienia, nie jedno.** Poza znanym duplikatem na kwotach,
tłumaczenie `XSD-kwota-zapis` odpala się **na polach daty** z treścią o separatorze tysięcy —
potwierdzone uruchomieniem na `P_1 = 2026-13-45`. Sekcja 2 specu zawiera zweryfikowane listy
typów (17 typów z facetem `pattern`, pogrupowanych) i gotowe bloki kluczy. **Nie zgaduj tych
list ponownie.**

Uwaga dla porządku: pierwsza wersja poprawki B w tym dokumencie była błędna — kazała użyć
cytatów pkt 5 i pkt 10, które są już zajęte przez istniejące wpisy. Sekcja 2 została przepisana
po sprawdzeniu na plikach.

## Czego nie robić

Nie przepisywać tego, co działa. Nie osłabiać testów, żeby przeszły — defekt C powstał właśnie
tak. Nie zaczynać od sekcji 9 („co jeszcze"), dopóki defekty z sekcji 8 nie są zamknięte.

Pełna lista w sekcji 10 specu.

## Co jeszcze — po zamknięciu defektów

Sekcja 9 specu opisuje sześć rozszerzeń, uszeregowanych po stosunku wartości do nakładu.
Najciekawsze dwa:

**Walidacja wsadowa odblokowuje `TEC-007`.** Reguła unikalności jest nierozstrzygalna dla jednego
pliku, ale w paczce wgranej przez użytkownika jest w pełni rozstrzygalna. Nie dodaje warstwy —
uruchamia regułę, która dziś nie może działać.

**Wyjście JSON i kody wyjścia dla CLI.** Dla integratora ERP, którego README nazywa odbiorcą, to
różnica między demonstracją a narzędziem wchodzącym do potoku. Cała logika już istnieje.
