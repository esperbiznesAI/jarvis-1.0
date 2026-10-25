"""Reconstruct the supplied voxel revolver's visible shapes and pixel grid."""
from pathlib import Path
from PIL import Image, ImageDraw
import base64
import json
import runpy
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent
NAME = 'magnum_44_reference'
TEXTURE = ROOT / f'assets/fallout/textures/item/{NAME}.png'
MODEL = ROOT / f'assets/fallout/models/item/{NAME}.json'
for path in (TEXTURE, MODEL):
    path.parent.mkdir(parents=True, exist_ok=True)

# One texture pixel per visible reference cell, with no fine noise or wear.
# Each component gets its own small UV island at the same pixel density.
atlas = Image.new('RGB', (32, 32), (60, 62, 62))
d = ImageDraw.Draw(atlas)
ISLANDS = {}
def island(name, origin, rows):
    x0, y0 = origin
    for y, row in enumerate(rows):
        for x, color in enumerate(row):
            atlas.putpixel((x0+x, y0+y), color if isinstance(color, tuple) else (color, color, color))
    ISLANDS[name] = [x0, y0, x0+len(rows[0]), y0+len(rows)]

island('frame_side', (0, 0), [
    [99, 111, 102, 125, 117, 93],
    [57, 64, 58, 68, 67, 71],
    [49, 56, 58, 62, 61, 68],
    [47, 51, 50, 53, 57, 55],
    [45, 51, 49, 46, 54, 50],
])
island('frame_top', (8, 0), [
    [145, 151, 142, 158, 150, 141],
    [139, 148, 151, 147, 143, 148],
    [131, 137, 145, 140, 138, 142],
])
island('cylinder', (16, 0), [
    [68, 70, 66, 77],
    [60, 64, 65, 61],
    [53, 57, 55, 61],
    [52, 54, 57, 53],
])
island('silver', (22, 0), [[(211, 212, 205), (168, 172, 168), (216, 218, 210)],
                         [(199, 201, 194), (163, 167, 163), (205, 208, 201)]])
island('barrel_side', (0, 8), [
    [62, 58, 76, 67, 59, 79, 63, 82, 76],
    [116, 112, 126, 107, 120, 131, 110, 127, 117],
])
island('barrel_top', (0, 11), [[99, 110, 104, 91, 111, 99, 114, 102, 111]])
island('barrel_bottom', (0, 13), [[86, 98, 109, 97, 114, 102, 109, 98, 101]])
island('tip', (12, 8), [[119, 123], [104, 112]])
island('dark', (16, 8), [[58, 66], [60, 54]])
island('hammer', (20, 8), [[101], [94], [89]])
island('hammer_join', (20, 12), [[96]])
island('trigger', (24, 8), [[145, 158], [136, 145]])
island('grip', (0, 16), [
    [(191, 173, 100), (207, 189, 115), (207, 189, 115), (190, 172, 99)],
    [(181, 162, 89), (203, 184, 109), (194, 176, 101), (190, 173, 98)],
    [(177, 158, 84), (198, 180, 105), (199, 181, 105), (189, 172, 96)],
    [(176, 156, 82), (187, 168, 93), (199, 181, 105), (191, 172, 97)],
    [(180, 159, 83), (188, 169, 92), (191, 172, 95), (184, 165, 89)],
])
island('grip_edge', (6, 16), [
    [(145, 128, 66), (155, 139, 74), (153, 136, 70)],
    [(134, 119, 59), (148, 131, 67), (146, 129, 64)],
    [(133, 117, 58), (145, 128, 64), (146, 128, 63)],
    [(133, 116, 56), (140, 122, 60), (145, 127, 63)],
    [(141, 122, 58), (145, 128, 62), (143, 125, 60)],
])
island('neck', (12, 16), [[(201, 181, 106), (210, 191, 114), (200, 181, 103)],
                        [(188, 169, 94), (201, 182, 106), (205, 186, 109)],
                        [(181, 162, 87), (194, 174, 99), (197, 178, 102)]])
island('neck_top', (17, 16), [[(216, 197, 120), (204, 185, 109)],
                            [(207, 187, 111), (215, 195, 117)]])
island('black', (22, 16), [[31]])
atlas.save(TEXTURE)

CELL = 1.5
elements = []
groups = {}
def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, NAME + '/' + name))
def world(p):
    return [round(CELL*p[0], 6), round(CELL*p[1], 6), round(8+CELL*p[2], 6)]

def cube(name, fr, to, material, group, rotation=None, origin=None, face_materials=None, face_uv=None):
    faces = {}
    for face in ('north', 'east', 'south', 'west', 'up', 'down'):
        tile = ISLANDS[(face_materials or {}).get(face, material)].copy()
        if face == 'north':
            tile[0], tile[2] = tile[2], tile[0]
        if face_uv and face in face_uv:
            tile = face_uv[face]
        faces[face] = {'uv': tile, 'texture': 0}
    e = {'name': name, 'type': 'cube', 'uuid': uid(name), 'from': world(fr), 'to': world(to),
         'origin': world(origin or [0, 0, 0]), 'box_uv': False, 'autouv': 0,
         'rescale': False, 'shade': True, 'visibility': True, 'export': True,
         'faces': faces, 'color': len(groups) % 8}
    if rotation:
        e['rotation'] = rotation
    elements.append(e)
    groups.setdefault(group, []).append(e['uuid'])
    return e

def frame(name, fr, to):
    # World-aligned pixel UVs keep the ring's six by five cell grid continuous.
    x0,y0,z0 = fr; x1,y1,z1 = to
    return cube(name, fr, to, 'frame_side', 'Korpus',
                face_materials={'up': 'frame_top'},
                face_uv={'north': [x1, 11.5-y1, x0, 11.5-y0],
                         'south': [x0, 11.5-y1, x1, 11.5-y0]})

# Square outline and a small physically projecting silver block, as photographed.
frame('Korpus / gorna krawedz', [0, 10.5, -1.25], [6, 11.5, 1.25])
frame('Korpus / dolna krawedz', [0, 6.5, -1.25], [6, 7.5, 1.25])
frame('Korpus / tyl', [0, 7.5, -1.25], [1, 10.5, 1.25])
frame('Korpus / przod', [5, 7.5, -1.25], [6, 10.5, 1.25])
cube('Beben / kwadratowy srodek', [1, 7.5, -1.5], [5, 10.5, 1.5], 'cylinder', 'Beben')
cube('Beben / srebrny wystep', [1.25, 9.0, -1.75], [4.25, 10.5, 1.75], 'silver', 'Beben',
     face_materials={'east': 'tip', 'west': 'tip', 'up': 'tip', 'down': 'dark'})

# The barrel has a stepped, square cross-section rather than smooth bevels.
cube('Lufa / ciemny bok', [5.75, 10.0, -1.0], [14.0, 11.25, 1.0], 'barrel_side', 'Lufa',
     face_materials={'up': 'barrel_top', 'down': 'barrel_bottom'})
cube('Lufa / jasny dol', [6.25, 9.5, -.75], [14.0, 10.0, .75], 'barrel_bottom', 'Lufa')
cube('Lufa / zakonczenie', [14.0, 9.5, -1.0], [15.25, 11.25, 1.0], 'tip', 'Lufa',
     face_materials={'east': 'dark', 'up': 'barrel_top'})
cube('Muszka', [13, 11.25, -.3], [15, 11.9, .3], 'dark', 'Lufa')

# A bent, block-stepped neck merges into the wider pixel grip.
cube('Chwyt / gorna szyjka', [-1.5, 7.5, -1], [.25, 9.5, 1], 'neck', 'Chwyt',
     face_materials={'up': 'neck_top', 'west': 'grip_edge'})
cube('Chwyt / srodkowy stopien', [-1.5, 6.7, -1.48], [.25, 7.5, 1.48], 'neck', 'Chwyt',
     face_materials={'up': 'neck_top', 'west': 'grip_edge'})
cube('Chwyt / wypelnienie lokcia', [-1.5, 5.5, -1.48], [.75, 6.7, 1.48], 'neck', 'Chwyt',
     face_materials={'west': 'grip_edge'})
def grip_block(name, x0, x1, y0, y1):
    def v(y): return 16+(6.3-y)/5.35*5
    cube(name, [x0,y0,-1.5], [x1,y1,1.5], 'grip', 'Chwyt',
         rotation=[0,0,-45], origin=[0,6.5,0],
         face_materials={'west':'grip_edge', 'east':'grip_edge', 'up':'neck_top', 'down':'grip_edge'},
         face_uv={'north':[x1+2.3,v(y1),x0+2.3,v(y0)],
                  'south':[x0+2.3,v(y1),x1+2.3,v(y0)],
                  'east':[6,v(y1),9,v(y0)], 'west':[6,v(y1),9,v(y0)]})
# Extend the complete upper grip to the neck, filling the rear notch.
# A single solid replaces the old base and its narrow front-only shoulder.
grip_block('Chwyt / szeroki korpus', -2.3, 1.7, .95, 6.3)

# The reference has a long rear lever and a small square trigger, with no loop.
cube('Kurek / lacznik', [-2.5, 9.25, -.5], [-1.0, 10.5, .5], 'hammer_join', 'Mechanizm')
cube('Kurek / schodek', [-3.25, 10.0, -.5], [-2.5, 11.0, .5], 'hammer_join', 'Mechanizm')
cube('Kurek / dlugie ramie', [-3.9, 7.7, -.51], [-3.1, 10.7, .51], 'hammer', 'Mechanizm',
     rotation=[0, 0, -45], origin=[-3.5, 10.5, 0])
cube('Spust', [2, 5.0, -.4], [3.25, 6.75, .4], 'trigger', 'Mechanizm')

display = {
    'gui': {'rotation': [0, 0, 0], 'translation': [0, -1, 0], 'scale': [.5, .5, .5]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [.35, .35, .35]},
    'fixed': {'rotation': [0, 180, 0], 'translation': [0, 0, 0], 'scale': [.6, .6, .6]},
    'thirdperson_righthand': {'rotation': [0, -90, 0], 'translation': [0, 1.5, 1], 'scale': [.65, .65, .65]},
    'thirdperson_lefthand': {'rotation': [0, 90, 0], 'translation': [0, 1.5, 1], 'scale': [.65, .65, .65]},
    'firstperson_righthand': {'rotation': [0, -90, 7], 'translation': [1, .8, -2.5], 'scale': [.6, .6, .6]},
    'firstperson_lefthand': {'rotation': [0, 90, -7], 'translation': [1, .8, -2.5], 'scale': [.6, .6, .6]},
}
bbmodel = {
    'meta': {'format_version': '4.10', 'model_format': 'java_block', 'box_uv': False},
    'name': NAME, 'model_identifier': NAME, 'parent': '',
    'credit': 'Custom voxel revolver reconstructed from supplied visual reference',
    'ambientocclusion': False, 'front_gui_light': True,
    'resolution': {'width': 32, 'height': 32}, 'elements': elements,
    'outliner': [{'name': name, 'uuid': uid('group/' + name), 'origin': [0,0,8],
                  'visibility': True, 'export': True, 'isOpen': False, 'children': children}
                 for name,children in groups.items()],
    'textures': [{'name': NAME+'.png', 'id': '0', 'uuid': uid('texture'), 'path': '',
                  'folder': 'item', 'namespace': 'fallout', 'particle': True,
                  'render_mode': 'default', 'visible': True, 'mode': 'bitmap', 'saved': True,
                  'width': 32, 'height': 32, 'uv_width': 32, 'uv_height': 32,
                  'source': 'data:image/png;base64,'+base64.b64encode(TEXTURE.read_bytes()).decode()}],
    'display': display,
}
PROJECT = ROOT/(NAME+'.bbmodel')
PROJECT.write_text(json.dumps(bbmodel, ensure_ascii=False, indent=2), encoding='utf-8')
java = {'credit': bbmodel['credit'], 'texture_size': [32,32], 'ambientocclusion': False,
        'gui_light': 'front', 'textures': {'0':'fallout:item/'+NAME, 'particle':'fallout:item/'+NAME},
        'elements': [], 'display': display}
for e in elements:
    item = {'name':e['name'], 'from':e['from'], 'to':e['to'], 'faces':{}}
    if e.get('rotation'):
        axis=next(i for i,a in enumerate(e['rotation']) if a)
        item['rotation']={'angle':e['rotation'][axis], 'axis':'xyz'[axis], 'origin':e['origin']}
    for face,spec in e['faces'].items():
        item['faces'][face]={'uv':[v/2 for v in spec['uv']], 'texture':'#0'}
    java['elements'].append(item)
MODEL.write_text(json.dumps(java, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT/'CZYTAJ_MNIE.txt').write_text('''REWOLWER — WERSJA WEDŁUG ZDJĘCIA

Korpus, srebrny występ bębna, lufa, szyjka i szeroki chwyt
odtworzone według widocznej bryły i układu dużych pikseli w referencji.
Tekstura 32×32 jest osadzona w pliku .bbmodel.

Otwórz magnum_44_reference.bbmodel w Blockbenchu.
Zasoby Java są w folderze assets; model: fallout:item/magnum_44_reference.
Podgląd reference_pose pokazuje model pod kątem zbliżonym do zdjęcia.
Podglądy dotyczą geometrii i tekstury. Pozycje dłoni wymagają testu w grze.
''', encoding='utf-8')

def previews():
    renderer=runpy.run_path(str(ROOT.parent/'44_magnum/render_preview.py'))
    renderer['render'](bbmodel, ROOT/'preview_side.png', camera=(0,0,-1), light_direction=(-.3,.9,-1))
    renderer['render'](bbmodel, ROOT/'preview_reference_pose.png', camera=(-.4,.65,-1),
                       roll_degrees=-25.3, size=(768,768), padding=45, light_direction=(-.3,.9,-1))
    renderer['render'](bbmodel, ROOT/'preview_aligned.png', camera=(-.4,.65,-1),
                       roll_degrees=-25.3, size=(641,630), pixel_scale=28.6/CELL,
                       anchor=(world([0,11.5,-1.25]), [214,294]), background_color=(38,42,47),
                       light_direction=(-.3,.9,-1))

def package():
    with zipfile.ZipFile(ROOT/(NAME+'.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in [PROJECT, MODEL, TEXTURE, ROOT/'CZYTAJ_MNIE.txt', ROOT/'preview_side.png', ROOT/'preview_reference_pose.png', ROOT/'preview_aligned.png']:
            archive.write(path,path.relative_to(ROOT))

if __name__ == '__main__':
    previews()
    package()
    print(json.dumps({'cubes':len(elements), 'project':str(PROJECT)},ensure_ascii=False))
