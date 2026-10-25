"""Author an editable native Gaea graph. All terrain evaluation happens in Gaea."""
from pathlib import Path
import base64, copy, gzip, json, math, struct, uuid
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = json.loads((ROOT/'warsztat/node-schemas.json').read_text(encoding='utf-8-sig'))

def clean(obj):
    if isinstance(obj, dict):
        return {k:clean(v) for k,v in obj.items() if k not in ('$id','$ref')}
    if isinstance(obj, list): return [clean(v) for v in obj]
    return obj

project = clean(json.loads((ROOT/'warsztat/format-przyklad.terrain').read_text(encoding='utf-8-sig')))
asset = project['Assets']['$values'][0]
terrain = asset['Terrain']
nodes = {}
spec = {}

def node(ident, typ, name, x, y, links=None, **props):
    schema=SCHEMAS['QuadSpinner.Gaea.Nodes.'+typ+', Gaea.Nodes']
    n={'$id':f'n{ident}', '$type':schema['$type'], 'Id':ident, 'Name':name,
       'NodeSize':'Standard', 'Position':{'X':26000+x,'Y':26000+y}}
    n.update(props)
    ports=[]
    for p in schema['Ports']['$values']:
        if p['Name'].startswith('Input') and p['Name'] != 'Input2': continue
        q={'Name':p['Name'],'Type':p['Type'],'IsExporting':True,'Parent':{'$ref':f'n{ident}'}}
        if links and p['Name'] in links:
            src=links[p['Name']]
            fr, fp = src if isinstance(src,tuple) else (src,'Out')
            q['Record']={'From':fr,'To':ident,'FromPort':fp,'ToPort':p['Name'],'IsValid':True}
        ports.append(q)
    n['Ports']={'$values':ports}
    n['Modifiers']={'$values':[]}
    nodes[str(ident)]=n
    spec[ident]={'type':typ,'name':name,'inputs':links or {}}
    return ident

def curve(points, spacing=.003):
    a=np.asarray(points,float)
    if len(a)==1: a=np.vstack([a,a+[.00005,.00005]])
    t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(a,axis=0),axis=1))]
    tt=np.linspace(0,t[-1],max(2,int(t[-1]/spacing)+1))
    # Shape-preserving Hermite interpolation without external dependencies.
    sec=np.diff(a,axis=0)/np.diff(t)[:,None]
    deriv=np.zeros_like(a); deriv[0]=sec[0]; deriv[-1]=sec[-1]
    for i in range(1,len(a)-1):
        same=sec[i-1]*sec[i]>0
        for k in range(2):
            if same[k]: deriv[i,k]=2/(1/sec[i-1,k]+1/sec[i,k])
    idx=np.clip(np.searchsorted(t,tt)-1,0,len(t)-2)
    dt=t[idx+1]-t[idx]; u=((tt-t[idx])/dt)[:,None]
    b=(2*u**3-3*u**2+1)*a[idx]+(u**3-2*u**2+u)*dt[:,None]*deriv[idx]+(-2*u**3+3*u**2)*a[idx+1]+(u**3-u**2)*dt[:,None]*deriv[idx+1]
    return [{'X':round(float(p[0]),7),'Y':round(float(p[1]),7)} for p in b]

def stroke(points,radius,intensity,hardness=.25):
    return {'Points':curve(points),'Radius':radius,'Intensity':intensity,'Hardness':hardness}

def pack(strokes):
    b=json.dumps(strokes,separators=(',',':')).encode()
    return base64.b64encode(struct.pack('<I',len(b))+gzip.compress(b,mtime=0)).decode()

def draw(ident,name,x,y,strokes,soften=.6,height=1):
    if ident < 200:
        # Painter builds up repeated dabs. Compensate for sampling density so
        # broad foothills and thin summits keep genuinely different heights.
        strokes=copy.deepcopy(strokes)
        for s in strokes:
            pts=s['Points']; length=sum(math.hypot(b['X']-a['X'],b['Y']-a['Y']) for a,b in zip(pts,pts[1:]))
            support=min(1.1*s['Radius'],max(.008,length*.65))
            s['Intensity']*= (.30 if ident in (101,110) else (.60 if ident == 102 else .40)) if length > .05 else .75
    node(ident,'Draw',name,x,y,Soften=soften,Height=height,StrokeData=pack(strokes))
    return ident

def combine(ident,name,x,y,a,b,mode='Max',ratio=1,mask=None,color=False):
    links={'In':a,'Input2':b}
    if mask is not None: links['Mask']=mask
    node(ident,'Combine',name,x,y,links,PortCount=2,Mode=mode,Ratio=ratio,Output='Clamp',
         Enhance='None',**({'RenderIntentOverride':'Color'} if color else {}))
    return ident

# Closed, irregular perimeter. Broad feet and narrow high crests are independent paintings.
ring=[(.045,.055),(.18,.042),(.32,.061),(.47,.039),(.63,.05),(.79,.036),(.948,.052),
      (.96,.19),(.938,.34),(.96,.48),(.945,.65),(.96,.81),(.944,.95),
      (.78,.959),(.64,.94),(.47,.963),(.30,.942),(.16,.961),(.045,.949),
      (.056,.80),(.037,.65),(.055,.48),(.039,.32),(.056,.18),(.045,.055)]
draw(101,'01 PODNOZA - obwodka / Draw',0,0,[stroke(ring,.100,.31,.10)],soften=1.1)
ring_crests=[stroke(ring,.047,.63,.10)]
for x,y,h,r in [(.16,.047,.87,.043),(.33,.052,.74,.037),(.48,.041,.95,.045),
                (.67,.044,.83,.05),(.84,.043,.88,.04),(.954,.21,.85,.035),
                (.949,.40,.93,.038),(.949,.68,.84,.04),(.953,.87,.97,.04),
                (.75,.952,.84,.046),(.58,.957,.82,.042),(.36,.946,.91,.036),
                (.15,.95,.88,.04),(.044,.78,.92,.036),(.043,.58,.83,.046),
                (.046,.35,.93,.036),(.049,.15,.80,.04)]:
    ring_crests.append(stroke([(x-.009,y-.01),(x+.01,y+.012)],r,h,.1))
draw(102,'02 SZCZYTY - granica / Draw',0,180,ring_crests,soften=.8)
combine(103,'03 Zamkniety pierscien',330,80,101,102)

# Internal ranges echo the reference: crescent ridges, central spine, isolated teeth.
ridge_specs=[
 ([(.31,.145),(.39,.155),(.44,.198),(.395,.24)],.043,.31),
 ([(.65,.15),(.63,.23),(.72,.28),(.79,.28),(.79,.18)],.039,.40),
 ([(.42,.278),(.35,.31),(.43,.365),(.59,.395),(.71,.44),(.78,.42),(.78,.36)],.046,.48),
 ([(.32,.49),(.39,.46),(.47,.49),(.40,.56)],.04,.34),
 ([(.445,.53),(.39,.60),(.36,.66),(.40,.74),(.49,.77),(.55,.71),(.55,.60)],.035,.43),
 ([(.76,.57),(.70,.60),(.68,.66)],.033,.39),
 ([(.11,.49),(.18,.54),(.17,.64),(.115,.72),(.125,.81)],.037,.48),
 ([(.68,.80),(.71,.89)],.039,.43),
 ([(.18,.87),(.25,.91)],.028,.28)]
draw(110,'04 GRZBIETY wewnetrzne / Draw',0,440,
     [stroke(p,r*1.9,h*.45,.12) for p,r,h in ridge_specs],soften=1.5)
draw(111,'05 KORONY grzbietow / Draw',0,630,
     [stroke(p,r,h,.12) for p,r,h in ridge_specs],soften=.7)
combine(112,'06 Wewnetrzne masywy',330,500,110,111)
combine(113,'07 Wszystkie gory',660,220,103,112)

# Native procedural relief, constrained by the hand-painted ridge envelope.
node(120,'MountainRange','08 FAKTURA skal - seed',330,820,Scale=.36,Height=1,Seed=43712)
combine(121,'09 Skalne nierownosci',660,640,113,120,'Multiply',.70)
node(122,'Erosion2','10 EROZJA - delikatna',990,420,{'In':121},Duration=18.,Downcutting=.12,ErosionScale=900.,Seed=52502)
node(123,'Adjust','11 WYSOKOSC gor',1280,420,{'In':122},Multiply=.72,Autolevel=False)
node(124,'Constant','12 POZIOM DOLINY 50 m',660,1000,Height=50/300)
node(125,'Perlin','13 Pagorki dna doliny',330,1050,Frequency=.025,Seed=2137,Gain=.35)
node(126,'Adjust','14 Lagodne falowanie',660,1180,{'In':125},Multiply=.018,Autolevel=False)
combine(127,'15 Dno doliny',990,1000,124,126,'Add')
combine(128,'16 Gory + dno',1590,420,123,127,'Add')

# Route network: two large loops with crossing connections and arena spurs.
paths=[
 [(.52,.185),(.40,.105),(.22,.105),(.13,.16),(.13,.30),(.145,.38),(.25,.43),(.47,.45)],
 [(.52,.185),(.64,.105),(.78,.105),(.86,.16),(.868,.29),(.86,.39),(.84,.515),(.71,.54),(.60,.505),(.47,.45)],
 [(.145,.30),(.30,.267),(.43,.225),(.52,.185)],
 [(.52,.185),(.58,.265),(.71,.315),(.86,.34)],
 [(.47,.45),(.35,.55),(.24,.64),(.31,.745),(.455,.84),(.46,.895)],
 [(.47,.45),(.60,.535),(.62,.64),(.67,.70),(.59,.765),(.455,.84)],
 [(.24,.64),(.17,.75),(.15,.82),(.21,.85),(.31,.745)],
 [(.67,.70),(.77,.745),(.80,.80),(.745,.835)],
 [(.35,.55),(.27,.51)], [(.40,.105),(.30,.15),(.24,.205)],
 [(.78,.105),(.735,.205)], [(.47,.45),(.51,.375),(.50,.335)],
 [(.35,.55),(.44,.60),(.445,.65)]
]
draw(201,'17 SCIEZKI / Open Painter',990,1420,[stroke(p,.020,1,.74) for p in paths],soften=.4)
arenas=[('Boss',(.52,.185),.044),('Moby zachod',(.24,.205),.033),
        ('Moby wschod',(.735,.205),.034),('Moby srodek',(.50,.335),.032),
        ('Moby zachod 2',(.27,.51),.029),('Elita',(.445,.65),.032),
        ('Moby poludnie',(.745,.835),.032)]
arena_strokes=[]
for _,(x,y),r in arenas:
    arena_strokes.append(stroke([(x-r*.2,y),(x+r*.2,y)],r,1,.70))
draw(202,'18 POLANY MOBOW + BOSS / Draw',990,1620,arena_strokes,soften=.6)
draw(203,'19 START - poludnie / Draw',990,1820,[stroke([(.45,.895),(.47,.895)],.027,1,.65)],soften=.7)
combine(204,'20 Polany razem',1320,1660,202,203)
combine(205,'21 Przestrzen gry',1610,1340,201,204)
combine(206,'22 TEREN FINALNY',1940,530,128,127,'Blend',1,205)

# Color graph remains separate from height: green future forest, grey stone, pale trails, brown arenas.
def rgb(r,g,b): return {'R':r,'G':g,'B':b}
node(301,'Tint','23 PODLOZE LESNE',1940,1110,{'In':125},Start=rgb(.12,.21,.10),End=rgb(.31,.43,.16))
node(302,'Tint','24 CIEMNE SKALY',1940,910,{'In':206},Start=rgb(.13,.17,.18),End=rgb(.48,.51,.48))
node(303,'Slope','25 Skala na zboczach',2270,760,{'In':206},Range={'X':28.,'Y':90.},Falloff=12.)
combine(304,'26 Zielen + skaly',2590,970,301,302,'Blend',1,303,color=True)
node(305,'Tint','27 PIASKOWE SCIEZKI',2270,1330,{'In':125},Start=rgb(.58,.47,.28),End=rgb(.83,.74,.47))
combine(306,'28 Sciezki na terenie',2910,1150,304,305,'Blend',1,201,color=True)
node(307,'Tint','29 ZIEMIA AREN',2590,1610,{'In':125},Start=rgb(.28,.14,.075),End=rgb(.48,.29,.14))
combine(308,'30 KOLOR FINALNY',3220,1300,306,307,'Blend',1,202,color=True)

terrain.update({'Id':str(uuid.uuid4()),'Nodes':nodes,'Groups':{},'Notes':{},
 'GraphTabs':{'$values':[{'Name':'Dolina Cierni - uklad','Color':'Brass','ZoomFactor':.35,
 'ViewportLocation':{'X':25850.,'Y':25850.}}]},'Width':1024.,'Height':300.,'Ratio':300/1024})
terrain.pop('Metadata',None)
asset['Automation']={'Bindings':{'$values':[]},'Expressions':{},'VariablesEx':{},'Variables':{}}
asset['BuildDefinition'].update({'Resolution':1024,'BakeResolution':1024,'BucketResolution':1024,'OrganizeFiles':'NodeSubFolder'})
asset['State']={'BakeResolution':1024,'PreviewResolution':1024,'SelectedNode':206,
 'LockedNode':308,'UnderlayNode':206,
 'NodeBookmarks':{'$values':[]},'Viewport':{'Camera':{},'RenderMode':'Realistic','AmbientOcclusion':True,'Shadows':True}}
asset['BuildDefinition']['Destination']=str(ROOT/'eksport')
asset['BuildDefinition']['OrganizeFiles']='NodeSubFolder'
for ident,filename in [(206,'teren'),(308,'kolor'),(201,'sciezki'),(202,'areny'),(205,'przestrzen-gry'),(102,'szczyty')]:
    nodes[str(ident)]['SaveDefinition']={'Node':ident,'Filename':filename,'Format':'PNG8' if ident==308 else 'PNG16','IsEnabled':True,'DisabledInProfiles':{'$values':[]}}
asset['BuildProfiles']={}
project['Id']=uuid.uuid4().hex[:8]
project['Metadata']={'Name':'Dolina Cierni','Description':'Fantasy dolina 1024 x 1024. Native Draw: gory, sciezki, polany. Bez drzew. Wszystkie ksztalty edytowalne w Open Painter.',
 'Version':'2.3.1.0','ModifiedVersion':'2.3.1.0','DateCreated':'2026-10-05 18:40:00Z'}
dest=ROOT/'Dolina-Cierni.terrain'
dest.write_text(json.dumps(project,indent=2,ensure_ascii=False),encoding='utf-8')
(ROOT/'warsztat/uklad.json').write_text(json.dumps({'paths':paths,'arenas':arenas,'ring':ring,'nodes':spec},indent=2,ensure_ascii=False),encoding='utf-8')
print(f'{dest}: {len(nodes)} native nodes; {sum(len(p) for p in paths)} route control points; {len(arenas)} combat clearings')
