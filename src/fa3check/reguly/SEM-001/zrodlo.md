# Cytat

> Polski identyfikator podatkowy NIP nabywcy należy podawać w polu NIP w elemencie
> Podmiot2/DaneIdentyfikacyjne. Nie należy wskazywać go w polu NrVatUE, ani w polu NrID.
> Faktura zostanie odpowiednio udostępniona nabywcy w KSeF wyłącznie, gdy jego identyfikator
> podatkowy NIP ujęto w polu NIP, a nie w polu NrVatUE lub NrID.

Źródło: broszura FA(3), s. 6, ramka WAŻNE w rozdziale „Formaty pól (danych)".

# Interpretacja

Schemat dopuszcza w `Podmiot2/DaneIdentyfikacyjne` wybór między `NIP`, parą `KodUE`+`NrVatUE`,
`NrID` albo `BrakID`. Sam XSD nie wie, że dziesięciocyfrowy numer wyglądający jak polski NIP
trafił w złe pole wyboru. Reguła rozpoznaje wzorzec `TNrNIP` w `NrVatUE` lub `NrID`, gdy pole
`NIP` jest puste.

# Wyjątki

brak — reguła dotyczy wyłącznie nabywcy (`Podmiot2`), nie `Podmiot1` ani `Podmiot3`.

# Czego wpis nie sprawdza

- poprawności sumy kontrolnej NIP (to `TEC-005`),
- czy zagraniczny `NrVatUE` jest prawdziwym numerem VAT UE,
- obowiązków ustawowych związanych z identyfikacją nabywcy.
