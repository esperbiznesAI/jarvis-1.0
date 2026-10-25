from pathlib import Path
from PIL import Image, ImageDraw
import base64, json, math, random, uuid, zipfile

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets' / 'fallout'
(ASSETS / 'textures' / 'item').mkdir(parents=True, exist_ok=True)
(ASSETS / 'models' / 'item').mkdir(parents=True, exist_ok=True)
rng = random.Random(44)

# A compact, hand-drawn pixel atlas: aged blue-grey steel and antler grips.
atlas = Image.new('RGB', (128, 128), (54, 57, 60))
px = atlas.load()
def noise_rect(rect, base, amount=5):
    x0,y0,x1,y1 = rect
    for y in range(y0,y1):
        row = rng.choice([-2,0,0,1,2])
        for x in range(x0,x1):
            n = rng.randint(-amount,amount) + row
            px[x,y] = tuple(max(0,min(255,c+n)) for c in base)

noise_rect((0,0,64,64),(92,98,101),6)
noise_rect((64,0,112,32),(80,86,89),5)
noise_rect((64,32,96,64),(57,63,66),4)
noise_rect((96,32,112,48),(18,21,23),2)
noise_rect((112,32,128,48),(125,103,67),4)
noise_rect((64,64,96,96),(137,142,140),5)
noise_rect((96,80,112,96),(55,60,63),4)
d = ImageDraw.Draw(atlas)
for _ in range(72):
    x,y = rng.randrange(2,60),rng.randrange(2,62)
    c = rng.choice([(128,132,130),(110,115,116),(68,75,78)])
    d.line((x,y,min(x+rng.randrange(1,5),63),y),fill=c)
for _ in range(13):
    x,y = rng.randrange(4,60),rng.randrange(4,60)
    d.point((x,y),fill=(127,96,68))
    if rng.random()<.5: d.point((x+1,y),fill=(100,80,61))
# Three short flutes, with rounded rear ends and an open front edge.
# This tile is projected ONCE over the full cylinder height, including bevels.
for y,half_height in ((4,2),(16,3),(28,2)):
    d.rounded_rectangle((80,y-half_height-1,116,y+half_height+1),radius=half_height+1,fill=(115,122,123))
    d.rounded_rectangle((81,y-half_height,116,y+half_height),radius=half_height,fill=(45,53,57))
    d.rounded_rectangle((83,y-half_height+1,116,y+half_height-1),radius=max(1,half_height-1),fill=(61,69,72))
    d.line((85,y+half_height+1,111,y+half_height+1),fill=(144,149,147))
# Keep all drawing inside the cylinder's allocated 48 x 32 tile.
d.rectangle((112,0,127,31),fill=(54,57,60))
for side in range(2):
    ox=side*32
    for y in range(48):
        t=y/47
        for x in range(32):
            edge=abs(x-15.5)/15.5
            dark=max(0,(t-.68)/.32)
            n=rng.randint(-6,6)
            base=(220-61*dark-13*edge,209-74*dark-15*edge,171-77*dark-18*edge)
            px[ox+x,64+y]=tuple(int(max(0,min(255,c+n))) for c in base)
    for k in range(6):
        xb=ox+3+k*5
        path=[]
        for yy in range(111,74+(k%3)*4,-2):
            t=(111-yy)/37
            x=xb+int(3*math.sin(t*2+k*.4)+t*(15-(xb-ox))*.15)
            path.append((x,yy))
        d.line(path,fill=(101+k*4,67+k*3,37+k*2),width=2 if k%2==0 else 1)
        d.line([(x+1,y) for x,y in path[:10]],fill=(173,137,85),width=1)
    d.line((ox+1,65,ox+28,65),fill=(240,229,195),width=1)
# Muzzle and screw-head tiles, with a dark recessed centre.
noise_rect((96,64,112,80),(100,108,109),3)
d.rectangle((98,66,109,77),fill=(43,48,49))
d.rectangle((100,68,107,75),fill=(12,15,16))
d.line((98,78,109,78),fill=(156,160,157))
d.rectangle((112,64,120,72),fill=(78,84,86))
d.rectangle((113,65,118,70),fill=(171,175,169))
d.line((114,69,117,66),fill=(67,72,73),width=1)
texture_path=ASSETS/'textures'/'item'/'magnum_44.png'
atlas.save(texture_path)

elements=[]
groups={}
def uid(): return str(uuid.uuid4())
def cube(name, fr, to, material='steel', rotation=None, origin=None, group='Rama', uv_sides=None):
    tiles={'steel':(0,0,64,64),'cylinder':(64,0,112,32),'dark':(64,32,96,64),
           'black':(96,32,112,48),'edge':(64,64,96,96),'bone':(0,64,32,112),
           'screw':(112,64,120,72),'muzzle':(96,64,112,80)}
    face={}
    dims=[to[i]-fr[i] for i in range(3)]
    for i,f in enumerate(['north','east','south','west','up','down']):
        tile=tiles[material]
        w,h = (dims[0],dims[1]) if f in ('north','south') else ((dims[2],dims[1]) if f in ('east','west') else (dims[0],dims[2]))
        tx,ty,tx1,ty1=tile
        w=max(1,min(tx1-tx,w*2)); h=max(1,min(ty1-ty,h*2))
        dx=(i*7+len(elements)*3)%max(1,int(tx1-tx-w+1))
        dy=(i*3+len(elements)*5)%max(1,int(ty1-ty-h+1))
        uv=[tx+dx,ty+dy,tx+dx+w,ty+dy+h]
        if material in ('screw','muzzle'): uv=list(tile)
        if uv_sides and f in uv_sides: uv=uv_sides[f]
        face[f]={'uv':[round(v,4) for v in uv], 'texture':0}
    e={'name':name,'box_uv':False,'rescale':False,'locked':False,'light_emission':0,
       'render_order':'default','allow_mirror_modeling':True,'from':fr,'to':to,
       'autouv':0,'color':{'Rama':0,'Beben':1,'Lufa':2,'Rekojesc':3,'Spust i kurek':4}.get(group,0),
       'origin':origin or [8,8,8],'faces':face,'type':'cube','uuid':uid()}
    if rotation: e['rotation']=rotation
    elements.append(e); groups.setdefault(group,[]).append(e['uuid'])
    return e

def octagonal_prism(name,x0,x1,y,z,r,material,group):
    b=r*(math.sqrt(2)-1)
    # The cross and two diagonal rectangles form a solid regular octagon.
    # End planes are stepped by tiny amounts to avoid coplanar overlap.
    parts=[cube(name+' / poziom',[x0,y-b,z-r],[x1,y+b,z+r],material,group=group)]
    parts.append(cube(name+' / pion',[x0+.002,y-r,z-b],[x1-.002,y+r,z+b],material,group=group))
    a=(r+b)/math.sqrt(2); c=(r-b)/math.sqrt(2)
    for j,angle in enumerate([45,-45]):
        parts.append(cube(name+' / faza '+str(j+1),[x0+.004,y-a,z-c],[x1-.004,y+a,z+c],material,
             rotation=[angle,0,0],origin=[(x0+x1)/2,y,z],group=group))
    if material == 'cylinder':
        # Project cylinder UVs in world X/Y. Each facet samples its own band
        # instead of repeating and squeezing the complete flute pattern.
        def u(x): return 64+(x-x0)/(x1-x0)*48
        def v(local_y, local_z, angle):
            world_y=y+(local_y-y)*math.cos(angle)-(local_z-z)*math.sin(angle)
            return 32*(y+r-world_y)/(2*r)
        for p in parts:
            fr,to=p['from'],p['to']
            angle=math.radians(p.get('rotation',[0,0,0])[0])
            for f in ('east','west'):
                p['faces'][f]['uv']=[0,16,16,32]
            for f in ('north','south'):
                zz=fr[2] if f=='north' else to[2]
                ux=[u(to[0]),u(fr[0])] if f=='north' else [u(fr[0]),u(to[0])]
                p['faces'][f]['uv']=[ux[0],v(to[1],zz,angle),ux[1],v(fr[1],zz,angle)]
            for f in ('up','down'):
                if not angle:
                    p['faces'][f]['uv']=[16,0,32,8]
                    continue
                yy=to[1] if f=='up' else fr[1]
                za,zb=(fr[2],to[2]) if f=='up' else (to[2],fr[2])
                p['faces'][f]['uv']=[u(fr[0]),v(yy,za,angle),u(to[0]),v(yy,zb,angle)]
            for face in p['faces'].values():
                face['uv']=[round(value,4) for value in face['uv']]

# Main silhouette. +X is the muzzle; Z is the width of the revolver.
cube('Dolna rama',[-.8,8.1,6.75],[7.2,9.45,9.25],group='Rama')
cube('Tyl ramy',[-.85,9.0,6.75],[.65,13.8,9.25],group='Rama')
cube('Mostek nad bebenkiem',[-.1,14.2,7.0],[7.15,14.8,9.0],group='Rama')
cube('Przedni slup ramy',[6.05,9.15,6.75],[7.45,14.25,9.25],group='Rama')
cube('Szyjka chwytu',[-1.65,7.35,6.8],[.5,10.5,9.2],rotation=[0,0,-22.5],origin=[0,9,8],group='Rama')
cube('Tylna oslona bebna',[-.1,9.55,5.9],[.65,14.1,10.1],'dark',group='Beben')
octagonal_prism('Beben',.65,5.95,11.8,8,2.65,'cylinder','Beben')
cube('Os bebna',[.0,11.45,7.62],[6.15,12.15,8.38],'dark',group='Beben')

octagonal_prism('Lufa',7.1,24.3,13.05,8,1.08,'steel','Lufa')
# A short, square recessed muzzle is readable at Minecraft item scale.
cube('Korona wylotu',[24.3,12.28,7.23],[24.34,13.82,8.77],'muzzle',group='Lufa')
cube('Pret pod lufa',[7.15,11.68,7.72],[19.25,12.2,8.28],'dark',group='Lufa')
cube('Koncowka preta',[18.65,11.58,7.67],[19.6,12.18,8.33],group='Lufa')
cube('Obejma preta',[8.55,11.55,7.5],[9.1,12.25,8.5],group='Lufa')
cube('Muszka',[22.15,14.1,7.68],[23.25,15.1,8.32],'dark',group='Lufa')
cube('Podstawa muszki',[21.85,14.0,7.5],[23.45,14.28,8.5],group='Lufa')
cube('Szczerbinka tyl',[.0,14.72,7.1],[1.3,15.0,7.6],'dark',group='Rama')
cube('Szczerbinka przod',[.0,14.72,8.4],[1.3,15.0,8.9],'dark',group='Rama')

# A continuous grip bend: shared pivot, flush side planes and continuous UVs.
# Adjacent strips touch without overlapping visible coplanar faces.
grip_bands=[
    (7.1,9.3,-1.55,1.25),
    (2.5,7.1,-1.65,1.15),
    (1.1,2.5,-1.85,1.4),
]
grip_origin=[-.1,9,8]
def grip_u(x): return (x+2.2)/3.85*32
def grip_v(y): return 64+(9.3-y)/8.2*48
for i,(y0,y1,x0,x1) in enumerate(grip_bands):
    ua,ub=grip_u(x0),grip_u(x1)
    va,vb=grip_v(y1),grip_v(y0)
    cube('Rekojesc / profil '+str(i+1),[x0,y0,6.42],[x1,y1,9.58],'bone',
         rotation=[0,0,-22.5],origin=grip_origin,group='Rekojesc',
         uv_sides={'north':[ub,va,ua,vb],'south':[32+ua,va,32+ub,vb],
                   'west':[1,va,6,vb],'east':[25,va,30,vb]})
cube('Metalowa stopka',[-1.87,1.04,6.40],[1.42,1.22,9.60],'dark',
     rotation=[0,0,-22.5],origin=grip_origin,group='Rekojesc')

# Open trigger guard, separate trigger and visible hammer spur.
cube('Kablak / tyl',[.45,5.8,7.52],[1.0,8.2,8.48],'dark',rotation=[0,0,22.5],origin=[.7,7.9,8],group='Spust i kurek')
cube('Kablak / dol',[1.4,5.45,7.52],[4.9,6.0,8.48],'dark',group='Spust i kurek')
cube('Kablak / przod',[4.9,5.9,7.52],[5.5,8.6,8.48],'dark',rotation=[0,0,-22.5],origin=[5.15,7.2,8],group='Spust i kurek')
cube('Spust / gora',[2.2,6.9,7.78],[2.66,8.4,8.22],'edge',rotation=[0,0,22.5],origin=[2.4,8.2,8],group='Spust i kurek')
cube('Spust / koniec',[2.48,6.65,7.78],[3.2,7.08,8.22],'edge',rotation=[0,0,-22.5],origin=[2.75,6.9,8],group='Spust i kurek')
cube('Kurek / nasada',[-1.35,12.3,7.5],[-.25,14.45,8.5],'dark',rotation=[0,0,22.5],origin=[-.55,13.0,8],group='Spust i kurek')
cube('Kurek / ostroga',[-2.6,14.1,7.4],[-1.0,14.7,8.6],rotation=[0,0,-22.5],origin=[-1.1,14.3,8],group='Spust i kurek')
for side,z0,z1 in [('L',6.69,6.77),('P',9.23,9.31)]:
    for i,(x,y) in enumerate([(0,9.55),(2.15,8.85),(3.35,9.05)]):
        cube('Sruba ramy '+side+str(i+1),[x-.26,y-.26,z0],[x+.26,y+.26,z1],'screw',group='Rama')

display={
 'gui':{'rotation':[0,0,0],'translation':[-1,0,0],'scale':[.52,.52,.52]},
 'ground':{'rotation':[0,0,0],'translation':[0,3,0],'scale':[.35,.35,.35]},
 'fixed':{'rotation':[0,180,0],'translation':[0,0,0],'scale':[.65,.65,.65]},
 'thirdperson_righthand':{'rotation':[0,-90,0],'translation':[0,2.5,1],'scale':[.7,.7,.7]},
 'thirdperson_lefthand':{'rotation':[0,90,0],'translation':[0,2.5,1],'scale':[.7,.7,.7]},
 'firstperson_righthand':{'rotation':[0,-90,7],'translation':[1,1.8,-2.5],'scale':[.65,.65,.65]},
 'firstperson_lefthand':{'rotation':[0,90,-7],'translation':[1,1.8,-2.5],'scale':[.65,.65,.65]},
 'head':{'rotation':[0,-90,0],'translation':[0,5,0],'scale':[.5,.5,.5]}
}
outliner=[{'name':name,'origin':[8,8,8],'color':i,'uuid':uid(),'export':True,'isOpen':False,'visibility':True,'children':ids}
          for i,(name,ids) in enumerate(groups.items())]
model={'meta':{'format_version':'4.10','model_format':'java_block','box_uv':False},
       'name':'magnum_44','model_identifier':'magnum_44','parent':'','credit':'Fallout New Vegas inspired - custom Minecraft fan model',
       'ambientocclusion':False,'front_gui_light':True,'resolution':{'width':128,'height':128},
       'elements':elements,'outliner':outliner,'textures':[{'path':'','name':'magnum_44.png','folder':'item','namespace':'fallout',
       'id':'0','particle':True,'render_mode':'default','visible':True,'mode':'bitmap','saved':True,
       'uuid':uid(),'source':'data:image/png;base64,'+base64.b64encode(texture_path.read_bytes()).decode(),
       'width':128,'height':128,'uv_width':128,'uv_height':128}], 'display':display}
(ROOT/'magnum_44.bbmodel').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')

def java_model():
    result={'credit':model['credit'],'texture_size':[128,128],'ambientocclusion':False,'gui_light':'front',
            'textures':{'0':'fallout:item/magnum_44','particle':'fallout:item/magnum_44'},'elements':[],'display':display}
    for e in elements:
        j={'name':e['name'],'from':e['from'],'to':e['to'],'faces':{}}
        if 'rotation' in e:
            axis=next(i for i,v in enumerate(e['rotation']) if v)
            j['rotation']={'angle':e['rotation'][axis],'axis':'xyz'[axis],'origin':e['origin']}
        for f,face in e['faces'].items():
            j['faces'][f]={'uv':[round(v/8,5) for v in face['uv']],'texture':'#0'}
        result['elements'].append(j)
    return result
(ASSETS/'models'/'item'/'magnum_44.json').write_text(json.dumps(java_model(),ensure_ascii=False,indent=2),encoding='utf-8')

readme='''MAGNUM .44 — MODEL DO MINECRAFT JAVA

Prosty model inspirowany zdjęciami rewolweru z Fallout: New Vegas.
Własna geometria i pikselowa tekstura; bez animacji.

POPRAWKI Z ZAZNACZONYCH REFERENCJI
Pręt pod lufą jest krótszy i schowany bliżej lufy.
Bęben ma trzy krótsze frezy z zaokrąglonymi końcami i spójne UV.
Usunięto śruby chwytu, wyrównano segmenty i teksturę rękojeści.
Kopia wcześniejszego projektu jest w folderze wersja_przed_poprawkami.

PLIKI
magnum_44.bbmodel — edytowalny projekt z osadzoną teksturą.
assets/fallout/models/item/magnum_44.json — model przedmiotu Java.
assets/fallout/textures/item/magnum_44.png — tekstura 128×128.

BLOCKBENCH ONLINE
Wejdź na https://web.blockbench.net/ i wybierz „Otwórz model”.
Otwórz magnum_44.bbmodel. Tekstura jest już w środku.
Grupy: Rama, Beben, Lufa, Rekojesc, Spust i kurek.

MINECRAFT
Skopiuj folder assets do swojego resource packa.
Identyfikator modelu: fallout:item/magnum_44.
To zestaw zasobów modelu, a nie kompletny resource pack do aktywowania.
Przypięcie do przedmiotu / CustomModelData / item_model zależy od wersji
Minecrafta i używanego pluginu; wymaga integracji w Twoim resource packu.
Ustawienia widoków przedmiotu są zapisane, ale wymagają sprawdzenia w grze.
Model nie dodaje mechaniki strzelania ani obrażeń.
'''
(ROOT/'CZYTAJ_MNIE.txt').write_text(readme,encoding='utf-8')
print(json.dumps({'cubes':len(elements),'texture':'128x128','project':str(ROOT/'magnum_44.bbmodel')},ensure_ascii=False))
