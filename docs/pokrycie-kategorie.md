# Porównanie kategorii (etap 8)

Publiczny podział kategorii `ksefuj` (z `docs/zrodla.md`) jako lista kontrolna —
**nie** jako źródło reguł.

| Kategoria ksefuj | W fa3-check | Uwaga |
|---|---|---|
| Podmiot | SEM-001 (NIP nabywcy); TEC-005 (suma NIP) | Wąsko — świadomie; dalsze Podmiot* w kolejnych partiach z broszury |
| Fa | SEM-004/005/006, ARY-001 | Z wyciągu etapu 6 |
| Adnotacje | — | Luka na razie; wiele to `xsd:choice` (tłumaczenia, nie reguły) |
| FaWiersz | ARY-002, SEM-004/005 | |
| Korekty | SEM-002 (kandydat, niezaimplementowany) | |
| Płatność | — | Poza partią Fa/FaWiersz |
| Format | XSD-* tłumaczenia | Świadomy brak reguł — XSD łapie |
| Logika biznesowa | TEC-006/007 (offline info) | Część wymaga KSeF |

Kategorie bez wpisu nie zawsze oznaczają lukę produktową: często XSD albo brak
cytatu pozwalającego napisać regułę bez domysłów.
