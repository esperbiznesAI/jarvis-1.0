# Iron's Arms 'n Artifice — kontekst do dalszej pracy

Odczyt: 25.10.2026. Repozytorium: [iron431/irons-artifice](https://github.com/iron431/irons-artifice/tree/1.20.1).
Gałąź: `1.20.1`; sprawdzony commit: `c3afda729ed1834f3fda4c714015cb411b52da52` z 22.10.2026.
Obydwa linki użytkownika prowadzą do jednego repozytorium; drugi wskazuje jego folder zasobów.
Jest to rozpoznanie struktury i wybranych plików, bez kompilacji, uruchomienia gry lub audytu całego kodu.

## Środowisko tej gałęzi

Według `gradle.properties`, `build.gradle` i `META-INF/mods.toml`:

| Parametr | Wartość |
| --- | --- |
| Minecraft | 1.20.1 |
| Forge | 47.4.0 |
| Java toolchain | 17 |
| GeckoLib | 4.4.9 |
| Iron's Lib | 1.20.1-2.2.0 |
| Mod ID | `irons_artifice` |
| Wersja moda w źródłach | `1.20.1-1.1.1` |

`src/generated/resources` jest dołączony do zasobów przez build. Pliki `.bbmodel` są wyłączone z pakowania JAR; to pliki robocze do edycji, a nie format modelu ładowany w grze.
W buildzie znajduje się komentarz portowania `sable-companion`: zależność jest zakomentowana. Sam wpis wersji w properties nie oznacza, że jest aktywną zależnością tej gałęzi.

Źródła: [gradle.properties](https://github.com/iron431/irons-artifice/blob/1.20.1/gradle.properties), [build.gradle](https://github.com/iron431/irons-artifice/blob/1.20.1/build.gradle), [mods.toml](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/resources/META-INF/mods.toml).

## Gdzie jest mechanika broni

Wszystkie poniższe ścieżki Java są względem `src/main/java/io/redspace/irons_artifice/`.

| Plik/pakiet | Rola przy dalszych pracach |
| --- | --- |
| `registry/ItemRegistry.java` | Rejestruje przedmioty, w tym `new GunItem(..., Guns.SIX_SHOOTER)` i pozostałą broń. |
| `gun/Guns.java` | Definicje gotowych profili broni, odgłosów, animacyjnych cue i zajętości dłoni. |
| `gun/GunProfile.java` | Builder przyjmuje pojemność, liczbę slotów modyfikatorów, czas przeładowania w tickach, tryb strzału, pozę i dostawcę parametrów strzału. |
| `data/ShotComponents.java` | Klucze parametrów: obrażenia, rozrzut, opóźnienie/szybkostrzelność, prędkość, grawitacja, przebijanie, rykoszet, odrzut, dźwięki i błysk. |
| `item/GunItem.java`, `item/GunplayManager.java` | Klasy wykonujące zachowanie broni; przed implementacją trzeba przeczytać konkretne ścieżki strzelania/przeładowania. W tym rozeznaniu nie analizowano każdej metody. |
| `modifier/GunModifier.java`, `modifier/modifiers/` | Modyfikatory zmieniają `ShotComponentMap`; mogą też dostarczyć patch NBT. |
| `utils/ModifierPatchHandler.java` | Scala patch modyfikatorów, w tym mapę załączonych dodatków, i zapisuje ją do stacka. |
| `api/` | Zdarzenia dotyczące amunicji, składania strzału, strzelania i trafienia; nazwy standardowych kości i animacji. |
| `network/packets/` | Pakiety klient–serwer i serwer–klient dla strzelania, przeładowania, animacji, dźwięków i efektów. |
| `datagen/` | Generowanie modeli przedmiotów, receptur, tagów i innych danych. |

Zarejestrowane bronie: `flintlock`, `musket`, `blunderbuss`, `blackpowder_revolver`, `six_shooter`, `arquebus`, `clockwork_rifle`.
`SIX_SHOOTER` w tym commicie: pojemność 6, 5 slotów modyfikatorów, przeładowanie 20 ticków, tryb `SEMI`, poza `PISTOL`. Nie traktować tych parametrów jako ustaleń balansowych dla serwera Fallout.

Źródła: [ItemRegistry.java](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/java/io/redspace/irons_artifice/registry/ItemRegistry.java), [Guns.java](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/java/io/redspace/irons_artifice/gun/Guns.java), [GunProfile.java](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/java/io/redspace/irons_artifice/gun/GunProfile.java), [ShotComponents.java](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/java/io/redspace/irons_artifice/data/ShotComponents.java).

## Zasoby i format modeli

Baza ścieżek: `src/main/resources/assets/irons_artifice/`.

| Folder | Zawartość |
| --- | --- |
| `geckolib/` | Edytowalne projekty `.bbmodel`, m.in. `template_gun`, `six_shooter`, `blackpowder_revolver` oraz dodatki. |
| `geo/item/` | Eksporty GeckoLib `.geo.json`. |
| `animations/item/` | Pliki `.animation.json`. |
| `textures/item/` | Tekstury PNG broni, przedmiotów i dodatków. |
| `models/item/` | Ustawienia widoków i rodzice modeli przedmiotów; nie są samą geometrią broni. |
| `sounds.json`, `sounds/` | Definicje i pliki dźwięków. |
| `lang/` | Tłumaczenia nazw i opisów. |

Dodatkowo `src/generated/resources/assets/irons_artifice/models/item/` zawiera generowane pliki dla poszczególnych przedmiotów, np. `six_shooter.json`.
`ItemModelDataGenerator` kieruje rewolwery do `item/pistol_display`, a inne bronie do `item/gun_display`; ścieżka rodziców prowadzi do renderera `builtin/entity`.

Sprawdzone przykłady geometryczne:

- `six_shooter.geo.json`: format geometrii `1.12.0`, tekstura 32×32, 10 kości i 13 brył.
- `blackpowder_revolver.geo.json`: tekstura 64×64, 11 kości i 14 brył; dodatkowa kość `break_action`.
- `six_shooter.animation.json`: format animacji `1.8.0`, animacje `idle`, `fire`, `reload`, `equip`.
- Konwencje obejmują `root`, `gun`, `hammer`, `cylinder`, `cylinder_spin`, `attachment_muzzle`, `attachment_optic`, `attachment_bayonet`, `right_arm`, `left_arm`; dokładna hierarchia zależy od broni.
- `template_gun.bbmodel` używa `model_format: geckolib_model`, `box_uv: true`, tekstury 64×64 i formatu projektu 5.0. Nie jest projektem `java_block`.
- Kod deklaruje kontrolery `Actions` i `gun_animation_controller`; animacje muszą być dopasowane do pivotów własnej geometrii, więc nie należy automatycznie zakładać zgodności animacji innego rewolweru.

Przed przyszłą integracją brać rzeczywiste ścieżki z `client/gun/GunGeoModel.java` i plików danej gałęzi. README zawiera przykład ścieżki z prefiksem `geckolib/animations`, który nie odpowiada lokalizacji katalogów tej gałęzi.
`IronsArtificeClient.gunExtension()` przekazuje identyfikator rejestrowanego przedmiotu do `GunGeoModel`, dziedziczącego `DefaultedItemGeoModel`. Dla `irons_artifice:six_shooter` układ zasobów to `geo/item/six_shooter.geo.json`, `animations/item/six_shooter.animation.json` i `textures/item/six_shooter.png`, pod katalogiem `assets/irons_artifice/`.

Źródła: [zasoby](https://github.com/iron431/irons-artifice/tree/1.20.1/src/main/resources/assets/irons_artifice), [six_shooter.geo.json](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/resources/assets/irons_artifice/geo/item/six_shooter.geo.json), [GunBones.java](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/java/io/redspace/irons_artifice/api/GunBones.java), [GunAnimations.java](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/java/io/redspace/irons_artifice/api/GunAnimations.java), [ItemModelDataGenerator.java](https://github.com/iron431/irons-artifice/blob/1.20.1/src/main/java/io/redspace/irons_artifice/datagen/ItemModelDataGenerator.java).

## Co to oznacza dla naszego magnuma

Aktualny zaakceptowany projekt to `Fallout-MC/44_magnum_reference/magnum_44_reference.bbmodel`, 18 brył i tekstura 32×32, po wypełnieniu wcięcia chwytu.
Ma format `java_block` i statyczny eksport vanilla JSON. Nie jest jeszcze gotowym modelem GeckoLib do tego moda.

Przy późniejszym dodawaniu do moda trzeba dopasować hierarchię kości, pivots, orientację, skalę i pozycje dłoni, wyeksportować `.geo.json` oraz przygotować animacje i zgodne nazwy zasobów. Samo przemianowanie namespace `fallout` na `irons_artifice` nie wystarczy.
Nie wykonywać takiej migracji bez kolejnego zadania; użytkownik teraz poprosił tylko o poznanie repozytorium.
Własny namespace i sposób rejestracji zależą od kodu kolegi, którego osobnego forka nie otrzymaliśmy.

## Warunki dalszego korzystania z repozytorium

`LICENSE.md` oznacza projekt jako All Rights Reserved. Wprost dopuszcza modpacki, własne dodatki zależne od moda i niedystrybuowane publicznie modyfikacje; zabrania używania/redystrybucji jego assetów. To zapis odczytany z pliku, a nie założenie o prawach użytkownika lub kolegi. Na tym etapie tylko poznano strukturę — nie skopiowano modeli, tekstur ani dźwięków do naszych zasobów.

Źródło: [LICENSE.md](https://github.com/iron431/irons-artifice/blob/1.20.1/LICENSE.md).

## Powrót do pracy

1. Odczytać aktualny commit gałęzi `1.20.1` i ewentualny właściwy fork kolegi.
2. Wyszukać ścieżki w zapisanym `tree-1.20.1.json`, a potem odczytać aktualne pliki z repozytorium.
3. Rozdzielać model wizualny, animacje, zachowanie broni i balans; dopasować zakres do nowego zadania.
