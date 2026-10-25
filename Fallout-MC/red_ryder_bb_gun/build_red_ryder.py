"""Fallout 1 Red Ryder BB gun in the established coarse Minecraft pixel style."""
from pathlib import Path
from PIL import Image
import base64
import json
import runpy
import uuid
import zipfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
NAME = 'red_ryder_bb_gun'
TEXTURE = ROOT / f'assets/fallout/textures/item/{NAME}.png'
MODEL = ROOT / f'assets/fallout/models/item/{NAME}.json'
for path in (TEXTURE, MODEL):
    path.parent.mkdir(parents=True, exist_ok=True)

atlas = Image.new('RGB', (32, 32), (48, 53, 54))
islands = {}
def island(name, origin, rows):
    x0,y0=origin
    for y,row in enumerate(rows):
        for x,c in enumerate(row):
            atlas.putpixel((x0+x,y0+y), c if isinstance(c,tuple) else (c,c,c))
    islands[name]=[x0,y0,x0+len(rows[0]),y0+len(rows)]

# Broad clusters: one texel is approximately one model unit.
island('barrel', (0,0), [
    [(62,68,69),(62,68,69),(71,77,77),(71,77,77),(58,65,67),(58,65,67),(73,79,79),(73,79,79),(64,70,71),(64,70,71),(78,84,83),(78,84,83),(66,73,74),(66,73,74),(77,84,83),(77,84,83),(64,72,73),(64,72,73),(73,81,81),(73,81,81)],
    [(44,50,53),(44,50,53),(51,58,60),(51,58,60),(42,49,52),(42,49,52),(52,59,60),(52,59,60),(46,53,56),(46,53,56),(55,62,62),(55,62,62),(45,52,55),(45,52,55),(53,61,61),(53,61,61),(44,52,55),(44,52,55),(49,57,59),(49,57,59)],
])
island('barrel_top', (0,3), [[(120,126,123),(120,126,123),(106,114,113),(106,114,113),(127,133,128),(127,133,128),(111,120,117),(111,120,117),(131,136,129),(131,136,129),(115,124,120),(115,124,120),(132,137,130),(132,137,130),(115,124,120),(115,124,120),(124,132,127),(124,132,127),(109,119,117),(109,119,117)]])
island('barrel_under', (0,5), [[(54,61,62),(54,61,62),(63,70,70),(63,70,70),(50,58,61),(50,58,61),(65,72,72),(65,72,72),(56,64,66),(56,64,66),(68,75,74),(68,75,74),(58,65,67),(58,65,67),(66,73,73),(66,73,73)]])
island('receiver', (22,0), [
    [(86,92,91),(117,122,117),(134,137,128),(114,122,118),(87,95,94),(79,88,89)],
    [(53,59,61),(57,65,67),(49,57,60),(42,50,54),(62,70,71),(65,73,74)],
    [(40,47,50),(45,53,56),(43,50,53),(38,45,49),(48,56,59),(50,58,61)],
])
# Muted walnut and broad faded patches, matching the inventory sprite's colour.
wood_palette={'a':(104,86,66),'b':(113,94,71),'c':(94,76,58),
              'd':(103,74,56),'e':(117,98,75),'f':(91,70,54)}
island('wood', (0,8), [[wood_palette[c] for c in row] for row in
    ['aabbeebb','aabbccaa','ddaaccbb','ddbbffaa','ccaaddbb','ccddffaa']])
island('wood_edge', (10,8), [[(77,62,47),(85,68,50),(79,62,46)],[(75,59,44),(83,65,47),(79,60,45)],[(73,57,43),(79,61,45),(76,58,44)],[(72,56,42),(78,60,44),(75,57,43)],[(70,54,41),(75,58,43),(73,55,42)],[(69,52,40),(73,55,42),(71,53,41)]])
island('wood_top', (0,15), [[(118,100,78),(118,100,78),(127,108,84),(127,108,84),(111,92,70),(111,92,70),(121,101,78),(121,101,78)],[(107,88,67),(107,88,67),(119,99,75),(119,99,75),(104,84,63),(104,84,63),(115,95,71),(115,95,71)]])
island('dark', (15,9), [[(43,49,51),(48,55,56)],[(38,44,47),(44,50,53)]])
island('steel', (19,9), [[(96,103,101),(112,118,111)],[(77,85,84),(89,97,94)]])
island('upper_steel', (23,9), [[(126,133,126),(142,146,134),(135,142,131),(118,128,121)]])
island('sight', (28,9), [[(69,65,53),(78,72,55)],[(61,59,50),(70,65,53)]])
island('muzzle_rim', (25,14), [[(120,55,35),(112,49,32)],[(98,44,31),(106,49,32)]])
island('bore', (28,14), [[(16,21,23),(16,21,23)],[(16,21,23),(16,21,23)]])
island('lever', (25,18), [[(73,80,79),(80,87,84)],[(55,63,63),(63,71,69)]])
island('butt', (15,14), [[(66,42,26),(74,47,27)],[(62,38,24),(69,43,25)]])
island('muzzle', (20,14), [[(83,88,83),(83,88,83),(75,81,79)],[(70,77,75),(18,23,26),(73,80,77)],[(68,75,74),(71,78,75),(65,72,72)]])
body_palette={'a':(73,76,69),'b':(88,84,70),'c':(62,65,61),'d':(75,66,54),
              'e':(53,57,55),'f':(66,58,49),'g':(48,52,51)}
island('body', (0,20), [[body_palette[c] for c in row] for row in
    ['aabbbbaaacca','aaccccaaddcc','ccddcceeddcc','eeffccccggcc','eegggeeeeeee']])
island('body_top', (15,20), [[(84,85,76),(84,85,76),(105,105,90),(105,105,90),(110,108,91),(110,108,91),(90,91,81),(90,91,81),(76,80,76),(76,80,76),(82,84,77),(82,84,77)]])
atlas.save(TEXTURE)

elements=[]
groups={}
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,NAME+'/'+s))
def cube(name,fr,to,material,group,face_materials=None,face_uv=None):
    faces={}
    for face in ('north','east','south','west','up','down'):
        uv=islands[(face_materials or {}).get(face,material)].copy()
        if face=='north':uv[0],uv[2]=uv[2],uv[0]
        if face_uv and face in face_uv:uv=face_uv[face]
        faces[face]={'uv':uv,'texture':0}
    e={'name':name,'type':'cube','uuid':uid(name),'from':fr,'to':to,'origin':[0,0,8],
       'box_uv':False,'autouv':0,'shade':True,'visibility':True,'export':True,'rescale':False,
       'faces':faces,'color':len(groups)%8}
    elements.append(e);groups.setdefault(group,[]).append(e['uuid'])
    return e

# The long exposed metal barrel is the defining silhouette of the original icon.
cube('Lufa / glowny przekroj',[3.9,10.4,7.45],[24.4,11.45,8.55],'barrel','Lufa',
     face_materials={'up':'barrel_top','down':'dark'})
cube('Lufa / srodkowy dolny stopien',[5.0,9.7,7.3],[15.7,10.4,8.7],'barrel_under','Lufa')
cube('Lufa / przedni dolny profil',[15.7,10.05,7.4],[23.65,10.4,8.6],'barrel_under','Lufa')
cube('Lufa / nasada',[3.7,10.0,7.2],[6.25,11.65,8.8],'steel','Lufa',
     face_uv={'north':[2.55,0,0,2],'south':[0,0,2.55,2],
              'up':[0,3,2.55,4],'down':[0,5,2.55,6]})
cube('Lufa / tuleja wylotu',[23.65,10.1,7.25],[24.8,11.55,8.75],'dark','Lufa',
     face_materials={'east':'bore','up':'steel'})

# The rim is flush with the muzzle sleeve on every outer side. Its uniform
# 0.2-unit walls surround a recessed dark opening without enlarging the barrel.
cube('Wylot / dol',[24.8,10.1,7.25],[25.1,10.3,8.75],'muzzle_rim','Wylot')
cube('Wylot / gora',[24.8,11.35,7.25],[25.1,11.55,8.75],'muzzle_rim','Wylot')
cube('Wylot / bok lewy',[24.8,10.3,7.25],[25.1,11.35,7.45],'muzzle_rim','Wylot')
cube('Wylot / bok prawy',[24.8,10.3,8.55],[25.1,11.35,8.75],'muzzle_rim','Wylot')
cube('Muszka / niski wystep',[23.7,11.55,7.8],[24.1,11.95,8.2],'sight','Wylot')

# Receiver rebuilt from the supplied Fallout sprite after levelling its barrel.
# These are silhouette blocks, not surface details: a deep belly and a stepped
# rounded rear replace the previous shallow rectangular box and top rail.
def receiver(name,fr,to):
    x0,y0,z0=fr;x1,y1,z1=to
    def u(x):return (x+1.9)/7.2*12
    def v(y):return 20+(11.9-y)/3.65*5
    return cube(name,fr,to,'body','Korpus',
                face_materials={'up':'body_top','down':'dark','east':'dark','west':'dark'},
                face_uv={'north':[u(x1),v(y1),u(x0),v(y0)],
                         'south':[u(x0),v(y1),u(x1),v(y0)],
                         'up':[15+u(x0),20,15+u(x1),21]})
receiver('Korpus / przednie zaokraglenie',[4.95,9.0,7.15],[5.3,11.45,8.85])
receiver('Korpus / dolne wybrzuszenie',[4.2,8.55,7.05],[4.95,11.55,8.95])
receiver('Korpus / przednia czesc',[2.1,8.45,6.95],[4.2,11.65,9.05])
receiver('Korpus / srodek',[.1,8.55,6.9],[2.1,11.9,9.1])
receiver('Korpus / tylny luk',[-.8,8.65,6.9],[.1,11.75,9.1])
receiver('Korpus / skos tylnej krawedzi',[-1.4,8.85,7.0],[-.8,11.5,9.0])
receiver('Korpus / zaokraglony koniec',[-1.9,9.05,7.15],[-1.4,11.15,8.85])
cube('Szczerbinka',[.15,11.9,7.7],[.85,12.35,8.3],'dark','Korpus')

# The stock's upper notch is deep, but its lower notch is shallow. The wood
# remains thick at the wrist and drops below the barrel toward the broad butt.
# All side faces share one projection, preventing seams between silhouette steps.
def stock(name,fr,to):
    x0,y0,z0=fr;x1,y1,z1=to
    def u(x):return (x+8.35)/7.35*8
    def v(y):return 8+(11.7-y)/5.7*6
    return cube(name,fr,to,'wood','Kolba',face_materials={'up':'wood_top','down':'wood_edge','west':'wood_edge','east':'wood_edge'},
                face_uv={'north':[u(x1),v(y1),u(x0),v(y0)],
                         'south':[u(x0),v(y1),u(x1),v(y0)],
                         'up':[u(x0),15,u(x1),17],
                         'down':[10+u(x0)*3/8,8,10+u(x1)*3/8,10]})
stock('Kolba / bark pod metalem',[-1.9,8.0,7.1],[-1.0,11.7,8.9])
stock('Kolba / przednie ramie',[-2.65,7.35,7.05],[-1.9,11.3,8.95])
stock('Kolba / dolna pietka',[-3.4,6.9,7.05],[-2.65,10.8,8.95])
stock('Kolba / gorne przewazenie',[-3.8,6.9,7.1],[-3.4,10.3,8.9])
stock('Kolba / plytkie dolne wciecie',[-4.4,7.4,7.1],[-3.8,10.6,8.9])
stock('Kolba / nasada szerokiej stopki',[-5.2,6.95,7.0],[-4.4,10.8,9.0])
stock('Kolba / srodek stopki',[-6.25,6.45,7.0],[-5.2,10.85,9.0])
stock('Kolba / tyl stopki',[-7.3,6.1,7.0],[-6.25,10.8,9.0])
stock('Kolba / gorna krawedz tylu',[-8.35,9.3,7.0],[-7.3,10.8,9.0])
stock('Kolba / srodkowa krawedz tylu',[-8.2,7.8,7.0],[-7.3,9.3,9.0])
stock('Kolba / dolna krawedz tylu',[-8.05,6.1,7.0],[-7.3,7.8,9.0])

# Two compact adjacent loops occupy about 18% of the final gun length. The rear
# lever has a slightly sloping bottom and no separate upper rail or leather ties.
cube('Petle / wspolna przegroda',[-.45,6.6,7.75],[0,8.85,8.25],'lever','Dzwignia')
cube('Dzwignia / dol przy metalu',[-1.0,6.6,7.75],[-.45,6.9,8.25],'lever','Dzwignia')
cube('Dzwignia / srodkowy schodek',[-1.85,6.4,7.75],[-1.0,6.7,8.25],'lever','Dzwignia')
cube('Dzwignia / tylna dolna krawedz',[-2.25,6.25,7.75],[-1.85,6.55,8.25],'lever','Dzwignia')
cube('Dzwignia / dolny tylny luk',[-2.5,6.25,7.75],[-2.2,6.85,8.25],'lever','Dzwignia')
cube('Dzwignia / mocowanie pod drewnem',[-2.65,6.55,7.75],[-2.35,8.0,8.25],'lever','Dzwignia')
cube('Kablak / dolna krawedz',[0,6.8,7.75],[1.35,7.1,8.25],'lever','Kablak')
cube('Kablak / przedni dolny luk',[1.35,6.95,7.75],[1.75,7.7,8.25],'lever','Kablak')
cube('Kablak / przednie mocowanie',[1.75,7.4,7.75],[2.05,8.7,8.25],'lever','Kablak')
cube('Spust',[.55,7.35,7.85],[.85,8.65,8.15],'steel','Spust')

# The final proportion adjustment lengthens the stock and both loops
# horizontally while keeping their height and depth. The stock joint and the
# centre of the shared loop divider stay fixed; both loop openings grow outward.
def lengthen_horizontal(group_names,anchor_x,factor=1.4):
    selected={element_id for name in group_names for element_id in groups[name]}
    for e in elements:
        if e['uuid'] in selected:
            for corner in ('from','to'):
                e[corner][0]=round(anchor_x+(e[corner][0]-anchor_x)*factor,5)

lengthen_horizontal(('Kolba',),-1.0)
lengthen_horizontal(('Dzwignia','Kablak','Spust'),-.225)

display={
    'gui':{'rotation':[0,0,0],'translation':[-2,-1,0],'scale':[.44,.44,.44]},
    'ground':{'rotation':[0,0,0],'translation':[0,3,0],'scale':[.4,.4,.4]},
    'fixed':{'rotation':[0,180,0],'translation':[0,0,0],'scale':[.5,.5,.5]},
    'thirdperson_righthand':{'rotation':[0,-90,0],'translation':[0,1.5,1],'scale':[.65,.65,.65]},
    'thirdperson_lefthand':{'rotation':[0,90,0],'translation':[0,1.5,1],'scale':[.65,.65,.65]},
    'firstperson_righthand':{'rotation':[0,-90,0],'translation':[0,1,-2.5],'scale':[.6,.6,.6]},
    'firstperson_lefthand':{'rotation':[0,90,0],'translation':[0,1,-2.5],'scale':[.6,.6,.6]},
}
project={'meta':{'format_version':'4.10','model_format':'java_block','box_uv':False},
         'name':NAME,'model_identifier':NAME,'credit':'Custom Minecraft fan model based on Fallout 1 Red Ryder BB gun',
         'parent':'','ambientocclusion':False,'front_gui_light':True,'resolution':{'width':32,'height':32},
         'elements':elements,'outliner':[{'name':name,'uuid':uid('group/'+name),'origin':[0,0,8],
         'visibility':True,'export':True,'isOpen':False,'children':children} for name,children in groups.items()],
         'textures':[{'name':NAME+'.png','id':'0','uuid':uid('texture'),'path':'','folder':'item','namespace':'fallout',
         'particle':True,'render_mode':'default','visible':True,'mode':'bitmap','saved':True,'width':32,'height':32,
         'uv_width':32,'uv_height':32,'source':'data:image/png;base64,'+base64.b64encode(TEXTURE.read_bytes()).decode()}],
         'display':display}
PROJECT=ROOT/(NAME+'.bbmodel')
PROJECT.write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf-8')
java={'credit':project['credit'],'texture_size':[32,32],'ambientocclusion':False,'gui_light':'front',
      'textures':{'0':'fallout:item/'+NAME,'particle':'fallout:item/'+NAME},'elements':[], 'display':display}
for e in elements:
    java['elements'].append({'name':e['name'],'from':e['from'],'to':e['to'],
        'faces':{face:{'uv':[v/2 for v in spec['uv']],'texture':'#0'} for face,spec in e['faces'].items()}})
MODEL.write_text(json.dumps(java,ensure_ascii=False,indent=2),encoding='utf-8')

renderer=runpy.run_path(str(ROOT.parent/'44_magnum/render_preview.py'))
renderer['render'](project,ROOT/'preview_side.png',camera=(0,0,1),size=(1400,420))
renderer['render'](project,ROOT/'preview_angle.png',camera=(.2,.5,1),size=(1400,540))
renderer['render'](project,ROOT/'preview_muzzle.png',camera=(.65,.28,1),size=(1400,540))
renderer['render'](project,ROOT/'preview_reference.png',camera=(0,.12,1),size=(1400,540),roll_degrees=-6.35)

# Official Blockbench URL import; a fragment keeps the project out of HTTP queries.
data=json.dumps(project,ensure_ascii=False,separators=(',',':')).replace('&',r'\u0026')
url='https://web.blockbench.net/#loadtype=json&loadname='+quote(NAME+'.bbmodel',safe='')+'&loaddata='+quote(data,safe='')
opener='''<!doctype html><html lang="pl"><meta charset="utf-8"><title>Otwórz Red Rydera w Blockbenchu</title>
<style>body{font:18px system-ui;background:#202328;color:#eee;padding:48px}button{font:inherit;padding:16px 24px;cursor:pointer}</style>
<h1>Red Ryder BB gun — Fallout 1</h1><p>Otwórz gotowy model z teksturą w Blockbenchu online.</p>
<button id="open-model">Otwórz model w Blockbenchu</button><script>
document.getElementById('open-model').addEventListener('click',()=>{window.location.href=MODEL_URL;});
</script></html>'''.replace('MODEL_URL',json.dumps(url))
(ROOT/'OTWORZ_W_BLOCKBENCHU.html').write_text(opener,encoding='utf-8')
(ROOT/'CZYTAJ_MNIE.txt').write_text('''RED RYDER BB GUN — FALLOUT 1

Własny model w stylu zaakceptowanego magnuma: duże piksele i proste,
przestrzenne bryły. Tekstura 32×32 jest osadzona w projekcie.

Otwórz red_ryder_bb_gun.bbmodel w Blockbenchu albo otwórz
OTWORZ_W_BLOCKBENCHU.html i kliknij przycisk importu online.
Nie są wymagane wtyczki.

Folder assets zawiera statyczny model Minecraft Java i teksturę PNG.
Model zasobu: fallout:item/red_ryder_bb_gun.
To zasoby do własnego resource packa, bez mechaniki strzelania.
Przyszła integracja z modem GeckoLib wymaga dopasowania kości i animacji.
Pozycje w dłoniach wymagają sprawdzenia w grze.

REFERENCJE
Najnowszy sprite dostarczony przez użytkownika jest wzorem sylwetki:
pełniejsza, opuszczona kolba z płytkim dolnym wcięciem, głębszy korpus
ze schodkowo zaokrąglonym tyłem i dwie zwarte pętle.
Kolba oraz obie pętle zostały wydłużone poziomo o kolejne 25%
względem poprzedniej wersji (łącznie o 40% względem bazowego profilu).
https://fallout.fandom.com/wiki/Red_Ryder_BB_gun_(Fallout)
''',encoding='utf-8')

with zipfile.ZipFile(ROOT/(NAME+'.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
    for path in [PROJECT,TEXTURE,MODEL,ROOT/'OTWORZ_W_BLOCKBENCHU.html',ROOT/'CZYTAJ_MNIE.txt',
                 ROOT/'preview_side.png',ROOT/'preview_angle.png',ROOT/'preview_muzzle.png',ROOT/'preview_reference.png']:
        archive.write(path,path.relative_to(ROOT))
    if (ROOT/'blockbench_full.jpg').exists():
        archive.write(ROOT/'blockbench_full.jpg','blockbench_full.jpg')
print(json.dumps({'cubes':len(elements),'project':str(PROJECT),'url_length':len(url)},ensure_ascii=False))
