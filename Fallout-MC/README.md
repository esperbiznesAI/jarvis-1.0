# Serwer Minecraft RP w uniwersum Fallout

## Ustalenia z użytkownikiem

- Projekt dotyczy serwera RP w uniwersum Fallout.
- Użytkownik podał repozytorium `iron431/irons-artifice`, gałąź `1.20.1`, jako materiał do poznania w związku z modem tworzonym przez kolegę. Link sam w sobie nie potwierdza, że to ich własny fork ani że pokazuje wszystkie zmiany kolegi.
- Użytkownik zaakceptował ostatni rewolwer inspirowany zdjęciem, po wypełnieniu wcięcia w uchwycie. Preferowany styl: duże minecraftowe piksele i kanciaste bryły, bez realistycznych rys, śrub i drobnych frezów.

## Aktualny zaakceptowany model

- Projekt: `44_magnum_reference/magnum_44_reference.bbmodel`.
- Komplet do przekazania: `44_magnum_reference/magnum_44_reference.zip`.
- Podgląd: `44_magnum_reference/preview_aligned.png`.
- Wersja po ostatniej poprawce ma 18 brył, teksturę 32×32 i pełne połączenie chwytu. Model oraz PNG i eksport Java są w folderze projektu.
- To obecnie statyczny model Java Block/Item. Nie został jeszcze podpięty do moda ani przekonwertowany na jego system GeckoLib.

## Red Ryder BB gun z Fallouta 1 — model po poprawkach

- Użytkownik poprawił rozpoznanie broni ze sprite’a: to Red Ryder BB gun. Wcześniejszy model został zastąpiony, bez zachowywania osobnej starej wersji.
- Projekt: `red_ryder_bb_gun/red_ryder_bb_gun.bbmodel`.
- Komplet: `red_ryder_bb_gun/red_ryder_bb_gun.zip`.
- Styl dopasowany do zaakceptowanego magnuma: duże piksele, kanciaste bryły, ciemny metal i przygaszone brązowe drewno; 39 brył i tekstura 32×32.
- Środek i tył zbudowano od nowa na podstawie najnowszego sprite’a użytkownika, po porównaniu profili w tej samej skali: głębszy korpus ze schodkowo zaokrąglonym tyłem, niżej opadająca pełniejsza kolba, wyraźne górne przewężenie i płytkie dolne wcięcie.
- Kolba oraz obie pętle są wydłużone poziomo o kolejne 25% względem poprzedniej wersji (łącznie o 40% względem bazowego profilu). Wysokość i głębokość pozostają takie jak w przebudowanym profilu.
- Dwie sąsiadujące pętle mają łącznie około 18% długości broni. Tylna ma lekko opadający spód i przechodzi pod stykiem drewna z metalem. Nie ma osobnej górnej poprzeczki ani frędzli.
- Czerwona obwódka wylotu ma taki sam zewnętrzny obrys jak tuleja lufy z każdej strony, z równą grubością ścianek i zagłębionym ciemnym otworem.
- Podglądy: `preview_side.png`, `preview_angle.png`, `preview_muzzle.png`, `preview_reference.png` (kąt zbliżony do sprite’a).
- Model otwarto i obejrzano w Blockbenchu online. Zrzut z edytora: `red_ryder_bb_gun/blockbench_full.jpg`.
- `red_ryder_bb_gun/OTWORZ_W_BLOCKBENCHU.html` otwiera go w aplikacji online przez oficjalny import parametrów URL, z osadzoną teksturą. Nie wymaga instalowania wtyczki.
- Nadal jest to statyczny model Java; szkielet GeckoLib i animacje wymagają osobnego zadania.

## Red Ryder — drugi wariant z płaskim spustem i pętlami

- Oryginał przestrzenny pozostaje w folderze `red_ryder_bb_gun`.
- Osobny projekt: `red_ryder_bb_gun_flat/red_ryder_bb_gun_flat.bbmodel`.
- Komplet: `red_ryder_bb_gun_flat/red_ryder_bb_gun_flat.zip`.
- Spust i obie pętle są jedną dwustronną płaszczyzną z przezroczystą teksturą. Pozostałe 29 brył, długość drewna i pętli oraz dopasowanie czerwonej obwódki są zachowane.
- Wariant zawiera 29 brył i jedną płaszczyznę; oryginalna tekstura 32×32 pozostaje bez zmian, a osobna tekstura pętli ma 128×128 pikseli.
- Oba projekty można otworzyć równolegle i porównać. Każdy folder ma własny plik `OTWORZ_W_BLOCKBENCHU.html`.
- Nowy wariant sprawdzono z obu stron i pod kątem w Blockbenchu online. Podglądy edytora zapisano jako `blockbench_side.jpg`, `blockbench_reverse.jpg` i `blockbench_full.jpg`.

## Rozeznanie repozytorium moda

Szczegóły, ważne klasy, ścieżki zasobów i punkty potrzebne przy późniejszej integracji: [ROZEZNANIE.md](references/irons-artifice/ROZEZNANIE.md).

Zapisany indeks plików: `references/irons-artifice/tree-1.20.1.json`.
Stan sprawdzono 25.10.2026, commit `c3afda729ed1834f3fda4c714015cb411b52da52`.
Przed przyszłymi zmianami trzeba odczytać aktualną gałąź i ewentualne repozytorium kolegi. W tym rozeznaniu niczego nie zmieniano na GitHubie ani nie uruchamiano kompilacji.
