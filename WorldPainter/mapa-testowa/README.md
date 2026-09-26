# Mapa testowa WorldPainter: dwie góry i rzeka

Mała mapa 512 × 512 bloków z dwiema górami, łąkami i jedną krętą rzeką przebiegającą między górami. Skaliste wyższe zbocza i śnieg na szczytach ułatwiają ocenę ukształtowania terenu.

## Otwieranie

Pobierz `dwie-gory-rzeka.world` i otwórz go w WorldPainterze przez **File → Open**. Projekt utworzono w WorldPainter 2.27.1, w formacie Minecraft Java 1.20.5 lub nowszym. To edytowalny projekt WorldPainter; eksport do Minecrafta wykonuje się osobno przez **File → Export → Export as new Minecraft map**.

## Pliki

- `dwie-gory-rzeka.world` — gotowy projekt.
- `heightmap.png` — 16-bitowa mapa wysokości, zakres obrazu 0–65535 odpowiada wysokościom 0–255.
- `terrain-mask.png` — maska trawy, skał i brzegów rzeki.
- `frost-mask.png` — śnieg na wysokich szczytach.
- `generator.py` — odtwarzalny generator danych terenu; wymaga Python, NumPy i Pillow.
- `build-world.js` — tworzy i ponownie otwiera plik `.world` w silniku WorldPaintera.
- `metadata.json` — parametry i wyniki kontroli mapy wysokości.

## Odtworzenie

W katalogu z plikami uruchom `python generator.py`, a następnie `wpscript build-world.js .` (lub podaj pełną ścieżkę do zainstalowanego `wpscript.exe`).

Poziom wody wynosi 62; koryto rzeki leży poniżej tego poziomu, a pozostała część mapy powyżej niego. Mapa nie dodaje innych zbiorników wody.
