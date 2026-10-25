"""K02 dimension drawing; nominal geometry, no vehicle fitting approval."""
from pathlib import Path
import json, math
from html import escape
ROOT=Path(__file__).resolve().parent.parent
P=json.loads((ROOT/'parametry.json').read_text(encoding='utf-8-sig'));D=P['design']
w=json.loads((ROOT/'wymiary.json').read_text(encoding='utf-8-sig'))
w['revision']='K02'
w['status']='autorski_sportowy_wzorzec_powierzchni_zewnetrznej_do_prob_dopasowania'
w['authored_design_dimensions_mm']={
 'overall_span_x':D['span_mm'],'overall_depth_y':D['overall_depth_mm'],'overall_height_z':D['overall_height_mm'],
 'blade_span_x':D['blade_span_mm'],'blade_chord_y':D['chord_mm'],'blade_max_thickness':D['blade_max_thickness_mm'],
 'blade_max_thickness_z_range':[D['blade_top_z_mm']-D['blade_max_thickness_mm'],D['blade_top_z_mm']],
 'trailing_edge_thickness_before_edge_rounding':D['trailing_edge_thickness_mm'],
 'support_and_foot_centre_spacing':D['support_centres_mm'],
 'support_and_foot_x_centres':[-D['support_centres_mm']/2,D['support_centres_mm']/2],
 'support_width_x':D['support_width_mm'],'support_outline_yz':D['support_outline_yz_mm'],
 'support_styling_relief_outline_yz_before_corner_rounding':D['support_relief_yz_mm'],
 'support_styling_relief_corner_radius_yz':D['support_relief_corner_radius_mm'],
 'foot_width_x':D['foot_width_mm'],'foot_depth_y':D['foot_depth_mm'],
 'foot_thickness_z':D['foot_thickness_mm'],'foot_centre_y':D['foot_centre_y_mm'],
 'endplate_thickness_x':D['endplate_thickness_mm'],
 'endplate_x_centres':[-D['endplate_centres_mm']/2,D['endplate_centres_mm']/2],
 'endplate_outline_yz':D['endplate_outline_yz_mm'],
 'edge_rounds':{'blade':D['blade_edge_round_mm'],'supports':D['support_edge_round_mm'],
 'feet':D['foot_edge_round_mm'],'endplates':D['endplate_edge_round_mm']},'flat_contact_datum_z':0}
w['design_provenance']='Wszystkie wymiary spojlera sa zalozeniami SPORT K02, nie danymi OEM. Obrysy czesci sa nominalne, przed lokalnym zaokragleniem krawedzi.'
w['datum']={'origin':'Na osi symetrii samochodu, Z=0; srodki podstaw maja Y=-12 mm',
 'positive_x':'W poprzek auta, w prawo modelu','positive_y':'Ku tylowi auta','positive_z':'W gore'}
w['manufacturing']['current_geometry']='Jedna polaczona pelna bryla wzorcowa z wycieciami stylistycznymi w podporach'
w['manufacturing']['support_styling_openings_included']=True
w['manufacturing']['openings_are_mount_holes']=False
w['export']['expected_envelope_mm']=[D['span_mm'],D['overall_depth_mm'],D['overall_height_mm']]
w['export']['stl_file']='eksporty/K02-sport-wzorzec-1do1-MILIMETRY.stl'
(ROOT/'wymiary.json').write_text(json.dumps(w,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

svg=[]
def add(s):svg.append(s)
def text(x,y,s,cl='small',anchor=None):
 add(f'<text class="{cl}" x="{x:g}" y="{y:g}"'+(f' text-anchor="{anchor}"' if anchor else '')+'>'+escape(str(s))+'</text>')
def line(x1,y1,x2,y2,cl='ext'):add(f'<line class="{cl}" x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}"/>')
def rect(x,y,w,h,cl='part'):add(f'<rect class="{cl}" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"/>')
def poly(points,cl='part'):add(f'<polygon class="{cl}" points="'+' '.join(f'{x:g},{y:g}' for x,y in points)+'"/>')
def hdim(x1,x2,y,s):line(x1,y,x2,y,'dim');text((x1+x2)/2,y-9,s,'num','middle')
def vdim(x,y1,y2,s):
 line(x,y1,x,y2,'dim');add(f'<text class="num" text-anchor="middle" transform="translate({x+25:g} {(y1+y2)/2:g}) rotate(-90)">{escape(str(s))}</text>')
def rounded(outline,r):
 result=[]
 for i,p in enumerate(outline):
  prev,nxt=outline[i-1],outline[(i+1)%len(outline)]
  u=[prev[j]-p[j] for j in (0,1)];v=[nxt[j]-p[j] for j in (0,1)]
  ul=math.hypot(*u);vl=math.hypot(*v);u=[a/ul for a in u];v=[a/vl for a in v]
  angle=math.acos(sum(a*b for a,b in zip(u,v)));t=r/math.tan(angle/2)
  bis=[u[j]+v[j] for j in (0,1)];bl=math.hypot(*bis)
  c=[p[j]+bis[j]/bl*r/math.sin(angle/2) for j in (0,1)]
  a=[p[j]+u[j]*t-c[j] for j in (0,1)];b=[p[j]+v[j]*t-c[j] for j in (0,1)]
  start,end=math.atan2(a[1],a[0]),math.atan2(b[1],b[0]);sweep=(end-start+math.pi)%(2*math.pi)-math.pi
  result += [(c[0]+r*math.cos(start+sweep*j/8),c[1]+r*math.sin(start+sweep*j/8)) for j in range(9)]
 return result
add('''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 1680 1188">
<title>Celica 1994 — sportowy spojler K02, wymiary nominalne</title>
<desc>Wymiary mm: 1320 na 244 na 210. Skrzydło 1310 na 220, grubość 18. Dwie podpory o rozstawie 800 i kanciaste płetwy boczne.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M10 5 L0 0 L0 10 Z" fill="#22677a"/></marker>
<style>
text{font-family:"DejaVu Sans",Arial,sans-serif;fill:#182b35}
.title{font-size:34px;font-weight:700}.sub{font-size:19px;fill:#54636a}.section{font-size:21px;font-weight:700;letter-spacing:1px}
.small{font-size:17px}.tiny{font-size:15px;fill:#54636a}.note{font-size:17px}
.part{fill:#e9eef0;stroke:#243f4a;stroke-width:2;stroke-linejoin:round}
.plate{fill:#ccd8de;stroke:#243f4a;stroke-width:2;stroke-linejoin:round}
.hole{fill:#fff;stroke:#243f4a;stroke-width:2;stroke-linejoin:round}
.hidden{fill:none;stroke:#718894;stroke-width:1.6;stroke-dasharray:7 5}
.axis{fill:none;stroke:#889da6;stroke-width:1.2;stroke-dasharray:16 5 3 5}
.dim{fill:none;stroke:#22677a;stroke-width:1.4;marker-start:url(#arrow);marker-end:url(#arrow)}
.ext{fill:none;stroke:#8299a3;stroke-width:1.1}.leader{fill:none;stroke:#22677a;stroke-width:1.5}
.num{font-size:20px;font-weight:600;fill:#22677a;paint-order:stroke;stroke:#fff;stroke-width:7px;stroke-linejoin:round}
.rule{stroke:#d8e1e5;stroke-width:1.5}</style></defs>
<rect width="1680" height="1188" fill="white"/><rect x="28" y="28" width="1624" height="1132" fill="none" stroke="#ccd8dd"/>
<rect x="28" y="28" width="12" height="110" fill="#22677a"/>''')
text(65,78,'CELICA 1994 / SPOJLER SPORT K02','title')
text(65,110,'Wzorzec powierzchni zewnętrznej • wymiary nominalne • jednostki: mm','sub')
text(1610,71,'REWIZJA K02','small','end');text(1610,101,'Wydruk nie jest szablonem 1:1','tiny','end');line(65,135,1615,135,'rule')

s=.9;cx=840;base=412;X=lambda x:cx+s*x;Z=lambda z:base-s*z
text(65,168,'01 / PRZÓD','section');text(65,190,'X–Z','tiny')
for sign in (-1,1):
 px=sign*D['support_centres_mm']/2
 rect(X(px-D['support_width_mm']/2),Z(163),D['support_width_mm']*s,(163-6)*s)
 rect(X(px-D['foot_width_mm']/2),Z(8),D['foot_width_mm']*s,8*s)
rect(X(-D['blade_span_mm']/2),Z(D['blade_top_z_mm']),D['blade_span_mm']*s,D['blade_max_thickness_mm']*s)
for sign in (-1,1):
 ex=sign*D['endplate_centres_mm']/2
 rect(X(ex-D['endplate_thickness_mm']/2),Z(210),D['endplate_thickness_mm']*s,88*s,'plate')
for px in (-400,400):line(X(px),Z(184),X(px),449,'axis')
line(cx,219,cx,419,'axis');line(230,base,1450,base)
line(X(-660),220,X(-660),195);line(X(660),220,X(660),195);hdim(X(-660),X(660),203,D['span_mm'])
line(1445,Z(210),1522,Z(210));line(1445,base,1522,base);vdim(1510,Z(210),base,D['overall_height_mm'])
hdim(X(-400),X(400),438,'800 — rozstaw osi podpór');text(cx,465,'Osi X: −400 / +400 • płaskie podstawy na Z=0','tiny','middle')
text(280,376,'Dwie pochylone podpory','tiny');text(880,376,'Skrzydło: góra Z=174, grubość maks. 18','tiny');line(65,486,1615,486,'rule')

text(65,517,'02 / GÓRA','section');text(65,539,'X–Y','tiny');cy=649;Y=lambda y:cy+s*y
rect(X(-655),Y(-110),1310*s,220*s)
for sign in (-1,1):
 px=sign*400;rect(X(px-40),Y(-83),80*s,142*s,'hidden');rect(X(px-9),Y(-65),18*s,121*s,'hidden')
 ex=sign*657;rect(X(ex-3),Y(-122),6*s,244*s,'plate');line(X(px),530,X(px),780,'axis')
line(cx,530,cx,585,'axis');line(cx,700,cx,767,'axis');text(cx,612,'SKRZYDŁO 1310 × 220','section','middle')
text(cx,645,'Linie przerywane: podpory i podstawy pod skrzydłem','tiny','middle')
text(cx,677,'2 podstawy: 80 × 142 × 8 • środki Y=−12','small','middle')
line(1446,Y(-122),1522,Y(-122));line(1446,Y(122),1522,Y(122));vdim(1510,Y(-122),Y(122),244)
line(1438,Y(-110),1473,Y(-110));line(1438,Y(110),1473,Y(110));vdim(1461,Y(-110),Y(110),220)
line(X(-440),765,X(-440),795);line(X(-360),765,X(-360),795);hdim(X(-440),X(-360),788,80);text(550,793,'szerokość podstawy','tiny')
line(1160,768,1160,798,'leader');add('<path d="M1160 798 l-5 -8 m5 8 l5 -8" class="leader"/>');text(1190,789,'+Y: tył auta','tiny')
line(65,815,1615,815,'rule')

text(65,848,'03 / BOK','section');text(65,870,'Y–Z · płetwa zasłania część podpory','tiny')
text(590,848,'04 / PODPORA','section');text(590,870,'Płetwa pominięta dla czytelności','tiny')
side_s=.93;bz=1081
def side(centre,show_plate):
 T=lambda yz:(centre+yz[0]*side_s,bz-yz[1]*side_s)
 poly([T(p) for p in D['support_outline_yz_mm']])
 poly([T(p) for p in rounded(D['support_relief_yz_mm'],D['support_relief_corner_radius_mm'])],'hole')
 rect(centre+(-12-71)*side_s,bz-8*side_s,142*side_s,8*side_s)
 def pt(y,z):return f'{centre+y*side_s:g},{bz-z*side_s:g}'
 profile=f'M{pt(-101,174)} L{pt(68,174)} C{pt(89,174)} {pt(104,167)} {pt(108,167)} A{2*side_s:g},{2*side_s:g} 0 0 1 {pt(108,163)} C{pt(104,163)} {pt(89,156)} {pt(68,156)} L{pt(-101,156)} A{9*side_s:g},{9*side_s:g} 0 0 1 {pt(-101,174)} Z'
 add(f'<path class="part" d="{profile}"/>')
 if show_plate:poly([T(p) for p in D['endplate_outline_yz_mm']],'plate')
 line(centre-132*side_s,bz,centre+132*side_s,bz)
 return T
T=side(298,True)
for y in (-122,122):line(T((y,122))[0],bz-110,T((y,122))[0],1116)
hdim(T((-122,0))[0],T((122,0))[0],1106,244);text(161,1053,'przód','tiny');text(398,1053,'tył','tiny')
T2=side(760,False);fy1=760-83*side_s;fy2=760+59*side_s
line(fy1,bz+4,fy1,1116);line(fy2,bz+4,fy2,1116);hdim(fy1,fy2,1106,142)
line(851,bz-8*side_s,894,bz-8*side_s);line(851,bz,894,bz);text(892,bz-15,'8','num')
text(592,985,'Wycięcie R4','tiny');text(592,1005,'stylistyczne','tiny');line(690,992,T2((8,88))[0],T2((8,88))[1],'leader')
text(895,944,'18 max.','num');text(881,966,'grubość','tiny');text(881,985,'skrzydła','tiny');line(882,940,T2((45,165))[0],T2((45,165))[1],'leader')
add('<rect x="1014" y="846" width="601" height="267" rx="8" fill="#f1f5f6"/>');text(1036,879,'ZAŁOŻENIA I ZAKRES','section')
for yy,txt in [(909,'Płetwy: grubość 6; podpory: grubość 18.'),(937,'Promienie krawędzi: skrzydło 0,6; podpory 1,5;'),(962,'podstawy 2; płetwy 1. Rzuty uproszczone.'),(990,'Wycięcia podpór nie służą do mocowania.'),(1018,'Wymiary autorskie; podstawy wymagają przymiarki.'),(1046,'Brak projektu mocowań, ścianek i wzmocnień.')]:text(1036,yy,txt,'note')
text(1036,1084,'Referencja: Celica GT Sport Coupe USA 1994 / ST204','tiny');line(65,1130,1615,1130,'rule')
text(65,1153,'K02 • WZORZEC / PROTOTYP • brak otworów montażowych • dopasowanie i konstrukcja niezweryfikowane','small')
text(1612,1153,'Arkusz 1 / 1','tiny','end');add('</svg>')
(ROOT/'rysunek-wymiarowy-K02.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')
print('Updated K02 dimension drawing and provenance.')
