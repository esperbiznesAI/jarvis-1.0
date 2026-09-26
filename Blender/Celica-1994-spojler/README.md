# Celica 1994 — niski spojler K01

Autorski model w skali 1:1: niska belka na dwóch bocznych wspornikach. Model jest **pełnym wzorcem powierzchni zewnętrznej do oceny kształtu i prób dopasowania**. Podstawy są płaskie, bez otworów; ich przyleganie do klapy nie zostało potwierdzone.

## Wymiary projektu

Wszystkie poniższe wartości są **założeniami autorskimi**, a nie wymiarami spojlera lub mocowania Toyota.

| Element | Wymiar nominalny [mm] |
|---|---:|
| Całkowita rozpiętość X | 1320 |
| Całkowita głębokość Y | 180 |
| Wysokość od płaszczyzny podstaw Z=0 | 110 |
| Maksymalna grubość belki | 22 |
| Grubość krawędzi spływu przed zaokrągleniami | 4 |
| Rozstaw osi wsporników / podstaw | 1218 |
| Położenia osi w X | −609 / +609 |
| Szerokość × głębokość wspornika | 42 × 126 |
| Obrys każdej podstawy × jej grubość | 96 × 154 × 8 |
| Rozmiar zaokrągleń podpór i podstaw | 3 |
| Rozmiar zaokrągleń końców belki | 0,75 |

Wymiary wsporników i podstaw opisują obwiednie nominalnych części źródłowych. Po połączeniu i zaokrągleniu powierzchnie przejść oraz płaski obszar styku mogą mieć inny obrys. Zaokrąglenie modelu nie jest uniwersalną specyfikacją promienia R3.

Początek układu jest pośrodku między podstawami na płaszczyźnie Z=0. X biegnie w poprzek auta, Y ku tyłowi, Z do góry. Dolne powierzchnie podstaw leżą nominalnie na Z=0. Belka ma maksymalną grubość między Z=88 i Z=110; jej tylny profil jest zwężony. Kształt profilu jest stylistyczny i nie określa właściwości aerodynamicznych.

## Pliki i jednostki

- `Celica-1994-spojler-K01.blend` — model Blendera i scena podglądu.
- `parametry.json` — źródłowe parametry modelu; `build_spoiler.py` — regeneracja sceny, eksportu i podglądów.
- `rysunek-wymiarowy-K01.svg` — schemat trzech rzutów i wymiary kontrolne. Wartości opisane liczbami są nadrzędne; wydruk nie jest szablonem 1:1.
- `wymiary.json` — rozdzielenie danych referencyjnych auta, założeń projektu i brakujących pomiarów.
- `eksporty/K01-wzorzec-1do1-MILIMETRY-nie-do-montazu.stl` — jedna połączona bryła wzorcowa, ze współrzędnymi zapisanymi w **milimetrach**.
- `kontrola-geometrii.json` — wyniki kontroli geometrii i wymiarów eksportu po pomyślnym zbudowaniu.
- `podglady/` — widoki modelu.

Blender przechowuje geometrię w metrach i wyświetla milimetry. STL nie zapisuje jednoznacznej jednostki: przy imporcie należy wybrać **mm** i sprawdzić obwiednię **1320 × 180 × 110 mm**. Scena, lampy i podłoże nie należą do eksportowanego wzorca.

Szczelna siatka STL nie oznacza gotowości do wykonania części do jazdy. Pełna bryła wzorcowa nie określa materiału, grubości ścianki lub laminatu, wzmocnień, łączeń ani mocowania. Zakres rzeczywiście wykonanych sprawdzeń podaje raport; sam rysunek nie poświadcza ich wyniku.

## Samochód referencyjny

Przyjęto **Toyota Celica GT Sport Coupe, rynek USA, rok modelowy 1994, rodzina ST204**. To wybrana referencja nadwozia, a nie potwierdzenie wersji konkretnego samochodu użytkownika.

Oryginalna broszura Toyota podaje dla GT Sport Coupe: długość 177,0 cala, szerokość 68,9 cala, rozstaw osi 99,9 cala i wysokość 51,0 cala. Odpowiada to odpowiednio około **4496, 1750, 2537 i 1295 mm**. Przeliczenie jednostek nie zwiększa dokładności danych katalogowych. Źródło: [broszura Toyota Celica 1994, strona PDF 15](https://xr793.com/wp-content/uploads/2024/12/1994-Toyota-Celica.pdf#page=15), kopia archiwalna oryginalnej publikacji producenta.

Wymiary auta służą wyłącznie jako kontekst proporcji. Nie znaleziono zweryfikowanych wymiarów powierzchni klapy, podstaw ani otworów mocujących spoiler. Żaden wymiar montażowy K01 nie pochodzi z tej broszury.

## Przed wykonaniem części użytkowej

1. Na konkretnym aucie ustalić wspólną bazę pomiarową oraz dostępny obrys, krzywiznę i nachylenie klapy pod każdą podstawą. Zmierzyć osobno lewą i prawą stronę, dostęp od spodu i ewentualne istniejące otwory.
2. Przymierzyć podstawy lub ich szablony w skali 1:1, skorygować rozstaw i powierzchnie styku, sprawdzić pełny ruch klapy i prześwity.
3. Z wykonawcą określić rolę modelu: wzorzec, forma lub geometria części. Dobrać materiał, proces, konstrukcję, tolerancje oraz projekt mocowania i wzmocnień.

Nie zweryfikowano dopasowania do auta, wytrzymałości, trwałości, osiągów aerodynamicznych ani dopuszczenia do użytkowania drogowego.

