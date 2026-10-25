"""Render the actual textured bbmodel cubes without a browser or editor.

Orthographic, nearest-neighbour software rasterization with a depth buffer.
This is only a geometry/UV preview; it does not simulate Minecraft item poses.
"""
from pathlib import Path
from io import BytesIO
import argparse
import base64
import json
import math

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def rotation_matrix(angles):
    x, y, z = np.radians(angles)
    cx, cy, cz = np.cos([x, y, z])
    sx, sy, sz = np.sin([x, y, z])
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def textures_for(model):
    textures = {}
    for i, meta in enumerate(model.get('textures', [])):
        source = meta.get('source', '')
        if source.startswith('data:'):
            im = Image.open(BytesIO(base64.b64decode(source.split(',', 1)[1]))).convert('RGBA')
        else:
            path = meta.get('relative_path') or meta.get('path')
            if not path:
                raise ValueError(f'Texture {i} has no embedded image or path')
            path = Path(path)
            if not path.is_absolute():
                path = ROOT / path
            im = Image.open(path).convert('RGBA')
        item = (np.asarray(im), float(meta.get('uv_width') or model['resolution']['width']),
                float(meta.get('uv_height') or model['resolution']['height']))
        for key in (str(i), str(meta.get('id', i)), str(meta.get('uuid', i))):
            textures[key] = item
    return textures


def cube_faces(element):
    x0, y0, z0 = element['from']
    x1, y1, z1 = element['to']
    # Each quad is ordered as texture top-left, top-right, bottom-right,
    # bottom-left, following Minecraft/Blockbench cube UV orientation.
    quads = {
        'north': [[x1, y1, z0], [x0, y1, z0], [x0, y0, z0], [x1, y0, z0]],
        'south': [[x0, y1, z1], [x1, y1, z1], [x1, y0, z1], [x0, y0, z1]],
        'east': [[x1, y1, z1], [x1, y1, z0], [x1, y0, z0], [x1, y0, z1]],
        'west': [[x0, y1, z0], [x0, y1, z1], [x0, y0, z1], [x0, y0, z0]],
        'up': [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]],
        'down': [[x0, y0, z1], [x1, y0, z1], [x1, y0, z0], [x0, y0, z0]],
    }
    normals = {'north': [0, 0, -1], 'south': [0, 0, 1],
               'east': [1, 0, 0], 'west': [-1, 0, 0],
               'up': [0, 1, 0], 'down': [0, -1, 0]}
    rot = rotation_matrix(element.get('rotation', [0, 0, 0]))
    origin = np.asarray(element.get('origin', [0, 0, 0]), dtype=float)
    rescale = np.ones(3)
    if element.get('rescale'):
        angles = element.get('rotation', [0, 0, 0])
        for axis, angle in enumerate(angles):
            if angle:
                for j in range(3):
                    if j != axis:
                        rescale[j] = 1 / abs(math.cos(math.radians(angle)))
    for face, spec in element.get('faces', {}).items():
        if face not in quads or spec.get('texture') is None:
            continue
        points = ((np.asarray(quads[face], dtype=float) - origin) * rescale) @ rot.T + origin
        u0, v0, u1, v1 = spec.get('uv', [0, 0, 16, 16])
        uv = np.array([[u0, v0], [u1, v0], [u1, v1], [u0, v1]], dtype=float)
        # A clockwise UV rotation moves the original bottom-left to top-left.
        steps = (int(spec.get('rotation', 0)) // 90) % 4
        if steps:
            uv = np.roll(uv, steps, axis=0)
        yield points, rot @ np.asarray(normals[face]), uv, spec['texture'], element.get('shade', True)


def draw_triangle(canvas, depths, vertices, uv, texture, shade):
    height, width = depths.shape
    x0 = max(0, int(math.floor(vertices[:, 0].min())))
    y0 = max(0, int(math.floor(vertices[:, 1].min())))
    x1 = min(width - 1, int(math.ceil(vertices[:, 0].max())))
    y1 = min(height - 1, int(math.ceil(vertices[:, 1].max())))
    if x0 > x1 or y0 > y1:
        return
    a, b, c = vertices
    denominator = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if abs(denominator) < 1e-8:
        return
    ys, xs = np.mgrid[y0:y1+1, x0:x1+1]
    xs = xs + .5
    ys = ys + .5
    wa = ((b[1]-c[1])*(xs-c[0]) + (c[0]-b[0])*(ys-c[1])) / denominator
    wb = ((c[1]-a[1])*(xs-c[0]) + (a[0]-c[0])*(ys-c[1])) / denominator
    wc = 1-wa-wb
    z = wa*a[2] + wb*b[2] + wc*c[2]
    patch_z = depths[y0:y1+1, x0:x1+1]
    keep = (wa >= -1e-7) & (wb >= -1e-7) & (wc >= -1e-7) & (z > patch_z + 1e-7)
    if not keep.any():
        return
    tex, uv_width, uv_height = texture
    u = wa*uv[0, 0] + wb*uv[1, 0] + wc*uv[2, 0]
    v = wa*uv[0, 1] + wb*uv[1, 1] + wc*uv[2, 1]
    tx = np.clip(np.floor(u / uv_width * tex.shape[1]).astype(int), 0, tex.shape[1]-1)
    ty = np.clip(np.floor(v / uv_height * tex.shape[0]).astype(int), 0, tex.shape[0]-1)
    colors = tex[ty, tx]
    keep &= colors[:, :, 3] > 127
    patch_z[keep] = z[keep]
    rgb = np.clip(colors[:, :, :3].astype(float) * shade, 0, 255).astype(np.uint8)
    canvas[y0:y1+1, x0:x1+1][keep] = rgb[keep]


def render(model, path, camera=(0, 0, 1), size=(1200, 750), *,
           roll_degrees=0, padding=50, background_color=None, pixel_scale=None, anchor=None,
           light_direction=None):
    textures = textures_for(model)
    faces = []
    for element in model.get('elements', []):
        if element.get('visibility', True) and element.get('type', 'cube') == 'cube':
            faces.extend(cube_faces(element))
    if not faces:
        raise ValueError('No textured cubes found')
    view = unit(camera)
    right = unit(np.cross(view, [0, 1, 0]))  # +X barrel points left.
    up = unit(np.cross(right, view))
    basis = np.stack([right, -up, view])
    if roll_degrees:
        # Rotate the screen projection before framing; screen Y points down.
        angle = math.radians(roll_degrees)
        c, s = math.cos(angle), math.sin(angle)
        basis[:2] = np.array([[c, -s], [s, c]]) @ basis[:2]
    all_vertices = np.concatenate([face[0] for face in faces]) @ basis.T
    low, high = all_vertices[:, :2].min(axis=0), all_vertices[:, :2].max(axis=0)
    width, height = size
    if padding < 0 or 2 * padding >= min(width, height):
        raise ValueError('Padding must leave a positive image area')
    scale = min((width-2*padding)/(high[0]-low[0]), (height-2*padding)/(high[1]-low[1]))
    center = (low+high)/2
    if pixel_scale is not None:
        scale = float(pixel_scale)
    offset = np.array([width/2, height/2])-center*scale
    if anchor is not None:
        world_point, screen_point = anchor
        offset = np.asarray(screen_point)-(basis @ np.asarray(world_point))[:2]*scale
    if background_color is None:
        yy, xx = np.mgrid[:height, :width]
        bg = np.where(((xx//24+yy//24) % 2)[:, :, None], np.array([27, 30, 34]), np.array([24, 27, 31]))
    else:
        if len(background_color) != 3:
            raise ValueError('Background colour must contain three RGB channels')
        bg = np.empty((height, width, 3), dtype=np.uint8)
        bg[:] = background_color
    canvas = np.asarray(bg, dtype=np.uint8)
    depths = np.full((height, width), -np.inf)
    light = unit(light_direction if light_direction is not None else [-0.25, .75, 1])
    for points, normal, uv, texture_id, use_shading in faces:
        if normal @ view <= 1e-8:
            continue
        points = points @ basis.T
        points[:, :2] = points[:, :2]*scale + offset
        key = str(texture_id).removeprefix('#')
        if key not in textures:
            raise ValueError(f'Unknown texture reference {texture_id!r}')
        shading = .74 + .30*max(0, float(normal @ light)) if use_shading else 1.
        for triangle in ([0, 1, 2], [0, 2, 3]):
            draw_triangle(canvas, depths, points[triangle], uv[triangle], textures[key], shading)
    Image.fromarray(canvas).save(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_model', nargs='?', default=None)
    parser.add_argument('--model', dest='explicit_model', default=None)
    parser.add_argument('--prefix', default='preview')
    parser.add_argument('--suffix', default='')
    args = parser.parse_args()
    model_path = args.explicit_model or args.input_model or ROOT/'magnum_44.bbmodel'
    model = json.loads(Path(model_path).read_text(encoding='utf-8'))
    for name, camera in [('side', (0, 0, 1)), ('angle', (.23, .24, 1))]:
        target = ROOT/f'{args.prefix}_{name}{args.suffix}.png'
        render(model, target, camera=camera)
        print(target)
