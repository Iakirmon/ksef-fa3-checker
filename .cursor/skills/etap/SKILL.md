---
name: etap
description: Prowadzi jeden etap realizacji fa3-check z sekcji 16 specu. Użyj, gdy prośba brzmi "zrób etap N", "etap 4", "kolejny etap" albo gdy zaczynasz pracę nad nowym fragmentem projektu opisanym w kolejności realizacji.
---

# Etap realizacji

Prowadzisz **jeden** etap z sekcji 16 dokumentu `docs/spec/2026-08-11-fa3-check-design.md`.
Nie dwa. Nie „etap 5, a przy okazji trochę 6".

## Zanim zaczniesz

1. Przeczytaj `docs/spec/2026-08-11-fa3-check-design.md` — całość, nie tylko wiersz tabeli
   z sekcji 16. **Sekcje 2 i 3 są obowiązkowe.** Z sekcji 2 wynika podział na dwa rejestry
   i bez niej napiszesz reguły duplikujące XSD. Sekcja 3 to dwanaście faktów sprawdzonych
   eksperymentalnie, z których trzy przewracają rzeczy „oczywiste" — nazwy typów XSD,
   zawartość `error.path` i zachowanie parsera przy XXE.
2. Przeczytaj opis tego etapu w `docs/spec/2026-08-11-cursor-prompty.md`. Zawiera zakres,
   kryterium ukończenia i — dla części etapów — ostrzeżenie o tym, co zwykle idzie nie tak.
3. Sprawdź, czy poprzedni etap jest **faktycznie** ukończony:
   `ruff check . ; if ($?) { mypy --strict src/ } ; if ($?) { pytest -q }`.
   Jeśli nie jest zielony, zgłoś to i zapytaj, czy najpierw domykamy poprzedni.

## Jak prowadzić

**TDD jest obowiązkowe.** Najpierw test, uruchom go, **pokaż użytkownikowi czerwony wynik**,
dopiero potem implementacja. Test, którego nikt nie widział czerwonego, nie jest testem.

**Zatrzymuj się na kryteriach cząstkowych.** Etapy 3, 4 i 7 idą wpisami: jeden wpis, test
czerwony, implementacja, test zielony, złoty korpus, raport użytkownikowi, następny. Nie rób
dwudziestu wpisów i nie pokazuj wyniku dopiero na końcu.

**Zadawaj sobie pytanie kwalifikujące.** Przy każdym nowym sprawdzeniu: *czy XSD już to łapie?*
Jeśli tak — to jest tłumaczenie, nie reguła. Sprawdź w `korpus/schema/`, nie w pamięci.

**Nie wybiegaj do przodu.** Jeśli zauważysz, że coś z późniejszego etapu byłoby teraz wygodne —
powiedz o tym i zapytaj. Nie dopisuj tego samodzielnie.

**Nie refaktoryzuj poprzednich etapów** bez wyraźnej prośby.

## Po zakończeniu

Zamknij raportem, który zawiera:

1. wynik `ruff check`, `mypy --strict src/` i `pytest -q` — wklejony, nie streszczony,
2. listę plików, które powstały albo się zmieniły,
3. wprost: czy kryterium ukończenia z sekcji 16 jest spełnione, i skąd to wiesz,
4. wszystko, co zostało niedokończone albo pominięte, i dlaczego.

Punkt 4 jest obowiązkowy także wtedy, gdy nic nie zostało pominięte — wtedy napisz, że nic.

Nie zaczynaj kolejnego etapu z własnej inicjatywy. Czekaj na „dalej".

## Etapy, które mają dodatkowe warunki

**Etap 0** — korpus, nie kod walidatora. Dwie pułapki, obie sprawdzone: numer przykładu jest na
**końcu** nazwy pliku (`FA_3_Przykład_12.xml`), więc naiwne `re.search(r"(\d+)")` łapie `3`
z `FA_3` i wszystkie 26 plików nadpisuje się na jeden — użyj `r"(\d+)\s*$"`. Do broszury
`pdftotext -layout -enc UTF-8`; bez `-enc UTF-8` polskie znaki są zepsute i `test_zrodla.py`
nigdy niczego nie znajdzie. Na koniec sprawdź, że fraza „Kwoty podawane są co do zasady
z dokładnością do 2 miejsc po kropce" występuje w wyciągu.

**Etap 1** — pierwszym wpisem jest `SEM-001`, celowo: to reguła, której XML Schema 1.0 wyrazić
nie umie. Nie zaczynaj od reguły formatu — formaty łapie schemat. `fixtures/lamie.xml` musi
przechodzić XSD, bo o tym jest cała ta reguła.

**Etap 2** — sedno jest w sekcji 8.4 i jest nieoczywiste: `error.path` zwraca ścieżkę
**pozycyjną** (`/*/*[4]/*[15]/*[7]`), bez nazw. Nazwę elementu uzyskujesz, wykonując tę ścieżkę
jako XPath na dokumencie. Wypisz mapę typów dla `P_15`, `P_11`, `P_9A`, `P_1`, `NIP`, `Nazwa`,
`KursWaluty` — spodziewane `TKwotowy`, `TKwotowy`, `TKwotowy2`, `TDataT`, `TNrNIP`,
`TZnakowy512`, `TIlosci`. Pokaż wynik złotego korpusu **plik po pliku**, wszystkie 26.

**Etap 3** — najpierw `struktura.py`, potem tłumaczenia. Obowiązuje niezmiennik z sekcji 8.5:
dopasowanie **nigdy** po treści komunikatu. Test z wyzerowanym polem `komunikat` musisz
uruchomić i pokazać. Granice bierz z `korpus/schema/`, nie z pamięci.

**Etap 4** — `TEC-005` udowodnij przypadkiem: NIP o poprawnym wzorcu `TNrNIP` i błędnej sumie
kontrolnej. Pokaż, że XSD go przyjmuje, a reguła odrzuca. To dowód, że drugi rejestr ma powód
istnienia.

**Etap 5** — web i hartowanie razem, nie osobno. Oczekiwania w `test_safexml.py` **różnią się
między wektorami** (tabela w sekcji 13 specu): bomba i głębokie zagnieżdżenie dają wyjątek,
a XXE tylko dzięki zakazowi `DOCTYPE` — naiwny test „każdy atak rzuca wyjątek" nie przejdzie.
Test przechwytujący logi **udowodnij**: dopisz tymczasowo `logger.exception` z surowym wyjątkiem
`lxml`, pokaż czerwony test, usuń. Nie wdrażaj publicznie przed ukończeniem tego etapu.

**Etap 6** — etap dokumentacyjny, nie piszesz kodu. Rozdziałami, ze zatrzymaniem po każdym.
Każdy kandydat przechodzi pytanie kwalifikujące i wypada do tłumaczeń, jeśli XSD go łapie.

**Etap 7** — powiedz, którą partię bierzesz, i czekaj na potwierdzenie. Przy każdej regule
sprawdź, czy `lamie.xml` przechodzi XSD — to granica między dwoma rejestrami.
