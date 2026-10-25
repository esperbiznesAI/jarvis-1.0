"""Read-only geometry QA for native Gaea exports from Dolina Cierni.

Example: python sprawdz_teren.py --height <terrain.png> --paths <paths.png>
  --arenas <arenas.png> [--space <combined-play-space.png>] [--report <json>]

PNG height samples are interpreted in their declared bit depth, never stretched
to the observed min/max. Normalized height 1.0 means Y300. The default prints
JSON only. Use --report explicitly to save the report after the native export.
"""
from pathlib import Path
from collections import deque
import argparse
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter

N = 1024


def read_gray(path, flip=False):
    path = Path(path)
    with Image.open(path) as im:
        arr = np.asarray(im)
        mode = im.mode
        if arr.shape != (N, N):
            raise ValueError(f'{path.name}: expected grayscale 1024x1024, got {arr.shape}')
        if arr.dtype.kind == 'f':
            normalized = arr.astype(np.float32)
            bits = 'float'
        else:
            # Pillow loads 16-bit PNG as I or I;16, sometimes using int32.
            bits = 8 if mode in ('1', 'L', 'P') else 16
            normalized = arr.astype(np.float32)/(255 if bits == 8 else 65535)
        if not np.isfinite(normalized).all() or normalized.min() < 0 or normalized.max() > 1.00001:
            raise ValueError(f'{path.name}: invalid normalized range')
    if flip:
        normalized = normalized[::-1].copy()
    return normalized, {'file':str(path.resolve()), 'mode':mode, 'bits':bits,
                        'sample_min':float(normalized.min()), 'sample_max':float(normalized.max()),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def xy(point):
    return tuple(int(np.clip(round(v*(N-1)), 0, N-1)) for v in point)


def near_disk(x, z, r):
    z0,z1=max(0,z-r),min(N,z+r+1)
    x0,x1=max(0,x-r),min(N,x+r+1)
    zz,xx=np.ogrid[z0:z1,x0:x1]
    return (slice(z0,z1),slice(x0,x1)), (xx-x)**2+(zz-z)**2 <= r*r


def flood(mask, levels, seed, radius=12, step=1):
    x,z=seed
    sl,disc=near_disk(x,z,radius)
    sz,sx=np.nonzero(mask[sl]&disc)
    seen=np.zeros(mask.shape,bool)
    if not len(sx):
        return seen, None
    sx=sx+sl[1].start;sz=sz+sl[0].start
    i=np.argmin((sx-x)**2+(sz-z)**2)
    z,x=int(sz[i]),int(sx[i]);seen[z,x]=True
    chosen_seed={'x':x,'z':z,'height':int(levels[z,x])}
    q=deque([(z,x)])
    while q:
        z,x=q.popleft();height=int(levels[z,x])
        for dz,dx in ((-1,0),(1,0),(0,-1),(0,1)):
            nz,nx=z+dz,x+dx
            if 0<=nz<N and 0<=nx<N and mask[nz,nx] and not seen[nz,nx] and abs(int(levels[nz,nx])-height)<=step:
                seen[nz,nx]=True;q.append((nz,nx))
    return seen, chosen_seed


def reached_near(seen,point,radius=8):
    x,z=xy(point);sl,disc=near_disk(x,z,radius)
    return bool(np.any(seen[sl]&disc))


def escape_count(seen):
    return int(seen[0].sum()+seen[-1].sum()+seen[1:-1,0].sum()+seen[1:-1,-1].sum())


def describe(values):
    return {str(q):float(np.percentile(values,q)) for q in [0,5,50,95,99,100]} if values.size else None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--height',type=Path,required=True)
    parser.add_argument('--paths',type=Path,required=True)
    parser.add_argument('--arenas',type=Path,required=True)
    parser.add_argument('--space',type=Path)
    parser.add_argument('--layout',type=Path,default=Path(__file__).with_name('uklad.json'))
    parser.add_argument('--height-scale',type=float,default=300)
    parser.add_argument('--flip-y',action='store_true')
    parser.add_argument('--floor-ceiling',type=float,default=70)
    parser.add_argument('--mask-threshold',type=float,default=.35)
    parser.add_argument('--report',type=Path)
    a=parser.parse_args()
    h,hmeta=read_gray(a.height,a.flip_y);h*=a.height_scale
    paths,pmeta=read_gray(a.paths,a.flip_y)
    arenas,ameta=read_gray(a.arenas,a.flip_y)
    layout=json.loads(a.layout.read_text(encoding='utf-8-sig'))
    space=np.maximum(paths,arenas)
    smeta=None
    if a.space:
        supplied,smeta=read_gray(a.space,a.flip_y)
        space=np.maximum(space,supplied)
    # Native start Draw is separate from arena Draw; include its known clearing.
    start=(.46,.895);start_xy=xy(start)
    sl,disc=near_disk(*start_xy,19)
    space[sl]=np.maximum(space[sl],disc.astype(np.float32))
    levels=np.floor(h+.5).astype(np.int16)
    dz,dx=np.gradient(h)
    slope=np.degrees(np.arctan(np.hypot(dx,dz)))
    low=h<=a.floor_ceiling
    gameplay=(space>=a.mask_threshold)&low
    seen,seed=flood(gameplay,levels,start_xy)
    seen_low,_=flood(low,levels,start_xy)
    # 9x9 inner core guarantees eight clear blocks around a route centre;
    # explicitly test it instead of accepting one-pixel connections.
    wide=np.asarray(Image.fromarray((gameplay*255).astype(np.uint8)).filter(ImageFilter.MinFilter(9)))>0
    seen_wide,_=flood(wide,levels,start_xy,radius=16)
    zero_levels=np.zeros_like(levels)
    seen_mask,_=flood(space>=a.mask_threshold,zero_levels,start_xy)

    arena_checks=[]
    for name,point,radius in layout['arenas']:
        x,z=xy(point);sl,disc=near_disk(x,z,max(5,int(radius*(N-1)*.5)))
        fraction=float(np.mean(seen[sl][disc]))
        arena_checks.append({'name':name,'x':x,'z':z,'height_at_centre':float(h[z,x]),
            'connected_on_mask':reached_near(seen_mask,point),
            'connected_by_low_terrain':reached_near(seen_low,point),
            'connected_by_painted_route':reached_near(seen,point),
            'connected_with_8block_clearance':reached_near(seen_wide,point,radius=12),
            'inner_arena_reachable_fraction':fraction,
            'inner_height_percentiles':describe(h[sl][disc]),
            'inner_slope_percentiles':describe(slope[sl][disc])})
    endpoints=[]
    for i,path in enumerate(layout['paths'],1):
        for position,point in [('start',path[0]),('end',path[-1])]:
            x,z=xy(point)
            endpoints.append({'route':i,'position':position,'x':x,'z':z,
                              'connected_mask':reached_near(seen_mask,point),
                              'connected_low_painted_route':reached_near(seen,point)})

    # A border may lie outside the mountain crest. Test escape from the interior
    # at several height ceilings instead of demanding high map-edge pixels.
    escape={}
    for ceiling in sorted(set([a.floor_ceiling,85.,100.])):
        reachable=seen_low if ceiling==a.floor_ceiling else flood(h<=ceiling,levels,start_xy)[0]
        escape[str(ceiling)]={'reachable_edge_pixels':escape_count(reachable),
                              'interior_connected_cells':int(reachable.sum())}
    crest=[]
    ring=np.asarray(layout['ring'],float)
    for p,q in zip(ring[:-1],ring[1:]):
        length=np.linalg.norm(q-p)
        for t in np.linspace(0,1,max(2,int(length*(N-1)/3)),endpoint=False):
            x,z=xy(p+(q-p)*t)
            # Sample a local maximum: procedural erosion may shift the crest
            # away from its nominal Draw axis by a few blocks.
            sl,_=near_disk(x,z,12)
            crest.append(float(h[sl].max()))
    path_core=(paths>.75)&(arenas<.5)
    checks={
        'height_range_within_0_300':bool(h.min()>=0 and h.max()<=a.height_scale+.001),
        'spawn_has_flat_route_seed':seed is not None,
        'all_arenas_connected_mask':all(x['connected_on_mask'] for x in arena_checks),
        'all_arenas_connected_low_painted_route':all(x['connected_by_painted_route'] for x in arena_checks),
        'all_route_endpoints_connected':all(x['connected_low_painted_route'] for x in endpoints),
        'all_arenas_8block_clearance':all(x['connected_with_8block_clearance'] for x in arena_checks),
        'inner_arenas_90pct_reachable':all(x['inner_arena_reachable_fraction']>=.9 for x in arena_checks),
        'inner_arena_slope_p95_below_12deg':all(x['inner_slope_percentiles']['95']<=12 for x in arena_checks),
        'route_core_height_p95_below_floor_ceiling':bool(path_core.any() and np.percentile(h[path_core],95)<=a.floor_ceiling),
        'no_flat_escape_to_map_edge':escape[str(a.floor_ceiling)]['reachable_edge_pixels']==0,
        'ring_has_no_low_gap_below_Y85':bool(min(crest)>=85),
    }
    report={'project':'Dolina Cierni','size':[N,N],'height_scale':a.height_scale,
            'status':'passed' if all(checks.values()) else 'needs_review',
            'checks':checks,'height_percentiles':describe(h),'route_core_height_percentiles':describe(h[path_core]),
            'route_core_slope_percentiles':describe(slope[path_core]),
            'spawn':seed,'flat_route_connected_cells':int(seen.sum()),
            'all_low_terrain_connected_cells':int(seen_low.sum()),
            'wide_route_connected_cells':int(seen_wide.sum()),
            'arenas':arena_checks,'route_endpoints':endpoints,
            'edge_escape_by_height_ceiling':escape,'perimeter_local_crest_height_percentiles':describe(np.asarray(crest)),
            'inputs':{'height':hmeta,'paths':pmeta,'arenas':ameta,'space':smeta,'layout':str(a.layout.resolve())},
            'thresholds':{'floor_ceiling':a.floor_ceiling,'mask_threshold':a.mask_threshold,
                          'max_adjacent_rounded_height_step':1,'min_route_clearance_blocks':8},
            'limits':['Heightfield and mask analysis, not a live Minecraft test.',
                      'A high continuous terrain ring is a visual/gameplay barrier; it does not prevent digging, building or flight.',
                      'No min-max normalization or inferred gamma correction applied. Validate native PNG height encoding separately.']}
    text=json.dumps(report,indent=2,ensure_ascii=False)
    if a.report:
        a.report.write_text(text,encoding='utf-8')
    print(text)
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
