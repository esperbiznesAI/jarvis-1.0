"""Deterministic 512-block WorldPainter test terrain; run without arguments.

Heightmap samples use PNG unsigned 16-bit values: world_y = sample / 257.
All outputs are written beside this generator. No external input or randomness.
"""
from collections import deque
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
SIZE = 512
WATER = 62.0


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def components(mask):
    """Four-connected components, returned as lists of (row, column)."""
    seen = np.zeros(mask.shape, dtype=bool)
    result = []
    for yy, xx in np.argwhere(mask):
        yy, xx = int(yy), int(xx)
        if seen[yy, xx]:
            continue
        seen[yy, xx] = True
        queue = deque([(yy, xx)])
        part = []
        while queue:
            row, col = queue.popleft()
            part.append((row, col))
            for rr, cc in ((row - 1, col), (row + 1, col),
                           (row, col - 1), (row, col + 1)):
                if (0 <= rr < SIZE and 0 <= cc < SIZE
                        and mask[rr, cc] and not seen[rr, cc]):
                    seen[rr, cc] = True
                    queue.append((rr, cc))
        result.append(part)
    return result


def main():
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float64)
    meadow = (71.0 + 1.25 * np.sin(x / 101.0 + 0.4)
              + 1.00 * np.cos(y / 116.0 + 0.7)
              + 0.65 * np.sin((x + y) / 158.0))
    mountains = np.zeros_like(meadow)
    specs = [(140, 170, 107.0, 127.0, 155.0, 0.3),
             (375, 305, 110.0, 126.0, 175.0, 1.4)]
    for cx, cy, rx, ry, peak, phase in specs:
        dx, dy = (x - cx) / rx, (y - cy) / ry
        radius = np.hypot(dx, dy)
        angle = np.arctan2(dy, dx)
        # Broad radial ridges and asymmetric slopes, fading at the summit.
        ridge_fade = 1.0 - np.exp(-np.square(radius / 0.18))
        warp = (1.0 + 0.08 * dx / (1.0 + np.abs(dx))
                - 0.06 * dy / (1.0 + np.abs(dy))
                + ridge_fade * (0.075 * np.cos(3.0 * angle + phase)
                                + 0.035 * np.sin(5.0 * angle - phase)))
        radial = radius * warp
        profile = np.square(np.maximum(1.0 - radial ** 1.4, 0.0))
        mountains = np.maximum(mountains, (peak - meadow[cy, cx]) * profile)
    height = meadow + mountains

    # Exactly one north/south channel. The bed never rises above the water.
    center = (255.0 + 18.0 * np.sin(2.0 * np.pi * y / 460.0 + 0.4)
              + 7.0 * np.sin(2.0 * np.pi * y / 185.0 - 0.6))
    distance = np.abs(x - center)
    half_width = 7.5 + 1.5 * np.sin(2.0 * np.pi * y / 290.0 + 0.7)
    bed = 56.7 + 1.1 * np.sin(2.0 * np.pi * y / 211.0)
    channel = bed + (WATER - bed) * np.minimum(distance / half_width, 1.0) ** 4
    banks = WATER + (70.0 - WATER) * smoothstep((distance - half_width) / 9.0)
    valley_mix = smoothstep((distance - half_width - 9.0) / 23.0)
    valley = 70.0 * (1.0 - valley_mix) + height * valley_mix
    height = np.where(distance <= half_width, channel,
                      np.where(distance <= half_width + 9.0, banks, valley))

    encoded = np.rint(height * 257.0).astype(np.uint16)
    decoded = encoded.astype(np.float64) / 257.0
    gy, gx = np.gradient(decoded)
    slope = np.hypot(gx, gy)
    terrain = np.zeros((SIZE, SIZE), dtype=np.uint8)
    terrain[(decoded >= 111.0) | ((decoded > 91.0) & (slope > 1.25))] = 1
    terrain[distance <= half_width + 4.5] = 2
    frost = np.where(decoded >= 148.0, 255, 0).astype(np.uint8)

    flooded = decoded < WATER
    river_parts = components(flooded)
    mountain_parts = components(decoded >= 100.0)
    summit_candidates = decoded > 100.0
    padded = np.pad(decoded, 1, mode='edge')
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            if oy or ox:
                summit_candidates &= decoded >= padded[1 + oy:1 + oy + SIZE,
                                                        1 + ox:1 + ox + SIZE]
    summit_parts = components(summit_candidates)
    assert len(river_parts) == 1, 'River must be a single connected flooded region'
    river_rows = [p[0] for p in river_parts[0]]
    assert min(river_rows) == 0 and max(river_rows) == SIZE - 1
    assert not flooded[:, 0].any() and not flooded[:, -1].any()
    assert len(mountain_parts) == 2 and len(summit_parts) == 2
    assert np.all(decoded[distance > half_width + 9.0] >= 68.0)
    assert np.all(frost[flooded] == 0)

    products = {'heightmap.png': Image.fromarray(encoded),
                'terrain-mask.png': Image.fromarray(terrain),
                'frost-mask.png': Image.fromarray(frost)}
    for name, img in products.items():
        img.save(OUT / name)
    # Read the exported PNG back: validation concerns the deliverable itself.
    with Image.open(OUT / 'heightmap.png') as img:
        assert img.size == (SIZE, SIZE)
        assert np.array_equal(np.asarray(img), encoded)

    peaks = []
    for part in summit_parts:
        row, col = max(part, key=lambda p: decoded[p])
        peaks.append({'x': col, 'z': row, 'height': round(float(decoded[row, col]), 4)})
    peaks.sort(key=lambda p: p['x'])
    width = flooded.sum(axis=1)
    metadata = {
        'name': 'Twin mountains and one river',
        'dimensions_blocks': {'width': SIZE, 'length': SIZE},
        'deterministic': True,
        'coordinates': 'PNG column = x, PNG row = z; top is north',
        'heightmap': {
            'file': 'heightmap.png', 'format': '16-bit unsigned grayscale PNG',
            'mapping': 'world_height = PNG_sample / 257; 0..65535 maps to 0..255',
            'worldpainter_import': {'image_low': 0, 'world_low': 0,
                                    'image_high': 65535, 'world_high': 255,
                                    'water_level': int(WATER), 'scale_percent': 100},
            'minimum': round(float(decoded.min()), 4),
            'maximum': round(float(decoded.max()), 4),
            'meadow_base_range': [round(float(meadow.min()), 4),
                                  round(float(meadow.max()), 4)]},
        'terrain_mask': {'file': 'terrain-mask.png', 'format': '8-bit grayscale PNG',
                         'values': {'0': 'grass', '1': 'rock', '2': 'sand or gravel banks and bed'}},
        'frost_mask': {'file': 'frost-mask.png', 'format': '8-bit grayscale PNG',
                       'values': {'0': 'no frost', '255': 'summit frost'},
                       'height_threshold': 148.0},
        'validation': {
            'exported_png_roundtrip': True,
            'mountain_components_at_height_100': len(mountain_parts),
            'local_maximum_regions_above_height_100': len(summit_parts),
            'peaks': peaks,
            'flooded_components_4_connected': len(river_parts),
            'river_touches_north': True, 'river_touches_south': True,
            'river_touches_east_or_west': False,
            'flooded_pixels': int(flooded.sum()),
            'river_width_per_row_blocks': {'min': int(width.min()), 'max': int(width.max())},
            'no_other_flooded_pools': True,
            'terrain_mask_values': [int(v) for v in np.unique(terrain)],
            'frost_mask_values': [int(v) for v in np.unique(frost)]},
        'sha256': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                   for name in products}}
    (OUT / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metadata['validation'], indent=2))


if __name__ == '__main__':
    main()
