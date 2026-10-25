"""Derive a separate flat-loop variant without modifying the accepted 3D model."""
from pathlib import Path
from io import BytesIO
import base64
import copy
import hashlib
import json
import math
import runpy
import uuid
import zipfile
from urllib.parse import quote

from PIL import Image


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'red_ryder_bb_gun' / 'red_ryder_bb_gun.bbmodel'
NAME = 'red_ryder_bb_gun_flat'
LOOPS_NAME = NAME + '_loops'


def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, NAME + '/' + label))


def package():
    paths = [ROOT / (NAME + '.bbmodel'), ROOT / 'CZYTAJ_MNIE.txt',
             ROOT / 'OTWORZ_W_BLOCKBENCHU.html', ROOT / 'build_flat_variant.py']
    paths += sorted((ROOT / 'assets').rglob('*'))
    paths += sorted(ROOT.glob('preview_*.png'))
    paths += sorted(ROOT.glob('blockbench_*.jpg'))
    with zipfile.ZipFile(ROOT / (NAME + '.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if path.is_file():
                archive.write(path, path.relative_to(ROOT))


def build():
    source_bytes = SOURCE.read_bytes()
    original = json.loads(source_bytes)
    project = copy.deepcopy(original)
    flat_groups = {'Dzwignia', 'Kablak', 'Spust'}
    flat_ids = {child for group in original['outliner'] if group['name'] in flat_groups
                for child in group['children']}
    selected = [element for element in original['elements'] if element['uuid'] in flat_ids]
    assert len(selected) == 10

    # Match the existing side-face colours and silhouette at 16 texels per unit.
    # The atlas is square to share the Java project's 32x32 UV coordinate space.
    # Its upper half maps to an 8x4-unit plane; the lower half stays transparent.
    atlas = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    original_atlas = Image.open(BytesIO(base64.b64decode(
        original['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA')
    for py in range(64):
        y = 10 - (py + .5) / 16
        for px in range(128):
            x = -4 + (px + .5) / 16
            for element in selected:
                x0, y0, _ = element['from']
                x1, y1, _ = element['to']
                if x0 <= x < x1 and y0 <= y < y1:
                    u0, v0, u1, v1 = element['faces']['south']['uv']
                    u = u0 + (u1-u0) * (x-x0) / (x1-x0)
                    v = v0 + (v1-v0) * (y1-y) / (y1-y0)
                    atlas.putpixel((px, py), original_atlas.getpixel((
                        min(31, max(0, math.floor(u))), min(31, max(0, math.floor(v))))))

    texture_dir = ROOT / 'assets' / 'fallout' / 'textures' / 'item'
    model_dir = ROOT / 'assets' / 'fallout' / 'models' / 'item'
    texture_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    main_texture = texture_dir / (NAME + '.png')
    main_texture.write_bytes(base64.b64decode(original['textures'][0]['source'].split(',', 1)[1]))
    loops_texture = texture_dir / (LOOPS_NAME + '.png')
    atlas.save(loops_texture)

    plane = {'name': 'Plaska tekstura / spust i obie petle', 'type': 'cube',
             'uuid': uid('flat-plane'), 'from': [-4, 6, 8], 'to': [4, 10, 8],
             'origin': [0, 0, 8], 'box_uv': False, 'autouv': 0,
             'shade': True, 'visibility': True, 'export': True, 'rescale': False,
             'faces': {'north': {'uv': [32, 0, 0, 16], 'texture': 1},
                       'south': {'uv': [0, 0, 32, 16], 'texture': 1},
                       **{side: {'uv': [0, 0, 0, 0], 'texture': None}
                          for side in ('east', 'west', 'up', 'down')}}, 'color': 4}
    project['name'] = NAME
    project['model_identifier'] = NAME
    project['credit'] = original['credit'] + '; separate flat trigger and loop variant'
    project['elements'] = [e for e in project['elements'] if e['uuid'] not in flat_ids] + [plane]
    project['outliner'] = [g for g in project['outliner'] if g['name'] not in flat_groups]
    project['outliner'].append({'name': 'Plaski spust i petle', 'uuid': uid('flat-group'),
                               'origin': [0, 0, 8], 'visibility': True, 'export': True,
                               'isOpen': False, 'children': [plane['uuid']]})
    project['textures'][0]['name'] = NAME + '.png'
    project['textures'].append({'name': LOOPS_NAME + '.png', 'id': '1', 'uuid': uid('loops-texture'),
                                'path': '', 'folder': 'item', 'namespace': 'fallout',
                                'particle': False, 'render_mode': 'default', 'visible': True,
                                'mode': 'bitmap', 'saved': True, 'width': 128, 'height': 128,
                                'uv_width': 32, 'uv_height': 32,
                                'source': 'data:image/png;base64,' +
                                base64.b64encode(loops_texture.read_bytes()).decode()})
    project_path = ROOT / (NAME + '.bbmodel')
    project_path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding='utf-8')

    java = {'credit': project['credit'], 'texture_size': [32, 32],
            'ambientocclusion': False, 'gui_light': 'front',
            'textures': {'0': 'fallout:item/' + NAME, '1': 'fallout:item/' + LOOPS_NAME,
                         'particle': 'fallout:item/' + NAME},
            'elements': [], 'display': project['display']}
    for element in project['elements']:
        java['elements'].append({'name': element['name'], 'from': element['from'], 'to': element['to'],
                                'faces': {side: {'uv': [v/2 for v in spec['uv']],
                                                 'texture': '#' + str(spec['texture'])}
                                          for side, spec in element['faces'].items()
                                          if spec['texture'] is not None}})
    (model_dir / (NAME + '.json')).write_text(json.dumps(java, ensure_ascii=False, indent=2), encoding='utf-8')

    render = runpy.run_path(str(ROOT.parent / '44_magnum' / 'render_preview.py'))['render']
    render(project, ROOT / 'preview_side.png', camera=(0, 0, 1), size=(1400, 420))
    render(project, ROOT / 'preview_reverse.png', camera=(0, 0, -1), size=(1400, 420))
    render(project, ROOT / 'preview_angle.png', camera=(.2, .5, 1), size=(1400, 540))
    render(project, ROOT / 'preview_loops.png', camera=(0, 0, 1), size=(1050, 540),
           pixel_scale=125, anchor=([-.3, 8.3, 8], [525, 270]))

    data = json.dumps(project, ensure_ascii=False, separators=(',', ':')).replace('&', r'\u0026')
    url = ('https://web.blockbench.net/#loadtype=json&loadname=' + quote(NAME + '.bbmodel', safe='')
           + '&loaddata=' + quote(data, safe=''))
    opener = '''<!doctype html><html lang="pl"><meta charset="utf-8">
<title>Red Ryder — płaski spust i pętle</title>
<style>body{font:18px system-ui;background:#202328;color:#eee;padding:48px}button{font:inherit;padding:16px 24px;cursor:pointer}</style>
<h1>Red Ryder — drugi wariant</h1>
<p>Spust i obie pętle są dwustronną płaską teksturą z przezroczystymi otworami.</p>
<button id="open-model">Otwórz model w Blockbenchu</button><script>
document.getElementById('open-model').addEventListener('click',()=>{window.location.href=MODEL_URL;});
</script></html>'''.replace('MODEL_URL', json.dumps(url))
    (ROOT / 'OTWORZ_W_BLOCKBENCHU.html').write_text(opener, encoding='utf-8')
    (ROOT / 'CZYTAJ_MNIE.txt').write_text('''RED RYDER — OSOBNY WARIANT Z PŁASKIM SPUSTEM I PĘTLAMI

Oryginalny model przestrzenny jest zachowany w sąsiednim folderze:
../red_ryder_bb_gun/red_ryder_bb_gun.bbmodel

Ten projekt: red_ryder_bb_gun_flat.bbmodel
Spust i obie pętle zastąpiono jedną płaszczyzną o zerowej grubości.
Tekstura jest widoczna z obu stron, a otwory są przezroczyste.
Pozostałe 29 brył, proporcje, kolory i pozycje w dłoniach są zachowane.
Model zawiera łącznie 30 elementów: 29 brył i jedną płaszczyznę.

Obie tekstury są osadzone w projekcie. Oryginalna ma 32x32 piksele,
a dodatkowa tekstura spustu i pętli 128x128 (użyta górna połowa).
Można otworzyć oba projekty jednocześnie w osobnych kartach Blockbencha.
Plik OTWORZ_W_BLOCKBENCHU.html zawiera przycisk importu online.

Folder assets zawiera statyczny model Minecraft Java i obie tekstury.
Model zasobu: fallout:item/red_ryder_bb_gun_flat
To wariant wizualny; nie dodaje mechaniki strzelania ani animacji.
Pozycje w dłoniach i działanie w docelowym modzie wymagają sprawdzenia w grze.
''', encoding='utf-8')

    assert SOURCE.read_bytes() == source_bytes, 'The accepted original must remain unchanged'
    original_by_id = {e['uuid']: e for e in original['elements']}
    assert all(e == original_by_id[e['uuid']] for e in project['elements'][:-1])
    assert set(atlas.getchannel('A').tobytes()) == {0, 255}
    assert len(project['elements']) == 30
    package()
    print(json.dumps({'project': str(project_path), 'elements': len(project['elements']),
                      'original_sha256': hashlib.sha256(source_bytes).hexdigest(),
                      'flat_elements_removed': len(selected), 'url_length': len(url)}, ensure_ascii=False))


if __name__ == '__main__':
    build()
