# JARVIS 1.0

Projekty i eksperymenty tworzone z pomocą asystenta AI. Repozytorium GitHub przechowuje pliki oraz historię ich zmian. Programy i gry uruchamiają się lokalnie na komputerze.

## Klockowa Dolina — `Voxel-gra`

Mała gra w przeglądarce inspirowana Minecraftem: mapa 80 × 80 pól, dziewięć rodzajów bloków, budowanie, kopanie, pływanie i latanie. Gra nie zapisuje trwale świata — odświeżenie lub zamknięcie strony usuwa zmiany w świecie.

### Uruchomienie

Na Windows otwórz `Voxel-gra/URUCHOM.cmd`. Możesz też otworzyć `Voxel-gra/index.html` w przeglądarce. Następnie kliknij „Wejdź do świata”.

### Sterowanie

- **WASD** — poruszanie się; **mysz** — rozglądanie.
- **Spacja** — skok / wypływanie; **Shift** — bieg.
- **Lewy przycisk myszy** — rozbijanie bloków; **prawy** — stawianie.
- **1–9** — wybór bloku.
- **F** — włączanie i wyłączanie latania; podczas lotu **Spacja** podnosi, a **C** obniża postać.
- **Esc** — menu.

## Scena testowa — `Blender-test`

- `test.blend` — scena zawierająca podłogę, sześcian i kulę. Otwórz ją w Blenderze.
- `create_scene.py` — skrypt Pythona tworzący scenę w Blenderze.

Do pracy ze sceną potrzebny jest zainstalowany Blender. Skrypt należy uruchamiać przy użyciu Pythona wbudowanego w Blender.

## Zapisywanie zmian

Zmiany plików powstają w lokalnej kopii projektu. Po utworzeniu wersji w Git i wysłaniu jej do GitHuba można pobrać ją na innym komputerze. Samo zapisanie pliku w edytorze nie wysyła go automatycznie do repozytorium.
