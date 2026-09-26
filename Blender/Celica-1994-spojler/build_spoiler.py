"""Blender 5.x: millimetre-controlled exterior pattern for a custom low spoiler.

Run Blender --background --factory-startup --python build_spoiler.py.
This is nominal exterior geometry, NOT a validated vehicle mounting design.
All project output is kept beside this script in JARVIS 1.0.
"""
from pathlib import Path
import json
import math
import struct
import hashlib

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "parametry.json").read_text(encoding="utf-8"))
D = P["design"]
OUT = ROOT / "eksporty"
PREVIEW = ROOT / "podglady"
WORK = ROOT / "robocze"
for directory in (OUT, PREVIEW, WORK):
    directory.mkdir(exist_ok=True)

MM = 0.001
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Celica - niski spojler K01"
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.unit_settings.length_unit = "MILLIMETERS"
scene.render.filepath = str(PREVIEW / "01-perspektywa.png")
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.resolution_x = 1800
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 80
scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("Swiat studia")
scene.world.color = (0.15, 0.15, 0.15)
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.48, 0.54, 0.65, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35


def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


model_coll = collection("01_MODEL - wzorzec powierzchni zewnetrznej 1do1")
source_coll = collection("02_PARAMETRYCZNE CZESCI - edytowalne zrodlo")
datum_coll = collection("03_BAZY - nominalne, bez otworow montazowych")
studio_coll = collection("04_STUDIO - nie eksportowac")
camera_coll = collection("05_KAMERY")


def move_to(obj, c):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    c.objects.link(obj)


def mat(name, colour, metallic=0.0, roughness=0.35):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*colour, 1.0)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*colour, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return m


paint = mat("Lakier grafitowy - podglad", (0.035, 0.053, 0.067), 0.60, 0.26)
paint.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.38
paint.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.19
floor_mat = mat("Studio - jasny szary", (0.46, 0.49, 0.52), 0.0, 0.78)


def mesh_object(name, vertices, faces, target=source_coll):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata([(x * MM, y * MM, z * MM) for x, y, z in vertices], [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.data.materials.append(paint)
    return obj


def box(name, cx, cy, zmin, sx, sy, height):
    v = [(cx + dx * sx/2, cy + dy * sy/2, zmin + zz * height)
         for zz in (0, 1) for dy in (-1, 1) for dx in (-1, 1)]
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
         (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return mesh_object(name, v, f)


def cubic(a, b, c, d, count=20):
    return [tuple((1-t)**3*a[j] + 3*(1-t)**2*t*b[j] +
                  3*(1-t)*t*t*c[j] + t**3*d[j] for j in (0, 1))
            for t in [i/count for i in range(1, count+1)]]


# Symmetric, rounded/tapered styling section; no aerodynamic performance claim.
half = D["blade_max_thickness_mm"] / 2
zc = D["overall_height_mm"] - half
y_le = -D["chord_mm"] / 2 + half
y_te = D["chord_mm"] / 2 - D["trailing_edge_thickness_mm"] / 2
te = D["trailing_edge_thickness_mm"] / 2
profile = [(y_le, zc + half), (68.0, zc + half)]
profile += cubic(profile[-1], (78.0, zc + half), (86.0, zc + te), (y_te, zc + te))
profile += [(y_te + te*math.cos(t), zc + te*math.sin(t))
            for t in [math.pi/2 - math.pi*i/16 for i in range(1, 17)]]
profile += cubic(profile[-1], (86.0, zc - te), (78.0, zc - half), (68.0, zc - half))
profile.append((y_le, zc-half))
profile += [(y_le + half*math.cos(t), zc + half*math.sin(t))
            for t in [-math.pi/2 - math.pi*i/32 for i in range(1, 32)]]
n = len(profile)
vertices = [(xx, yy, zz) for xx in (-D["span_mm"]/2, D["span_mm"]/2) for yy, zz in profile]
faces = [(i, (i+1)%n, n+(i+1)%n, n+i) for i in range(n)]
faces += [tuple(reversed(range(n))), tuple(range(n, 2*n))]
blade = mesh_object("Belka - 1320x180, maksymalnie 22mm", vertices, faces)
parts = [blade]
for side, sign in (("L", -1), ("P", 1)):
    cx = sign * D["support_centres_mm"] / 2
    parts.append(box("Wspornik_" + side, cx, 0, 6.0,
                     D["support_width_mm"], D["support_depth_mm"], zc-6.0))
    parts.append(box("Podstawa_" + side + " - styk nominalny", cx, 0, 0,
                     D["foot_width_mm"], D["foot_depth_mm"], D["foot_thickness_mm"]))

body = bpy.data.objects.new("SPOJLER K01 - pelny wzorzec, nie gotowy element drogowy", blade.data.copy())
model_coll.objects.link(body)
bpy.context.view_layer.objects.active = body
body.select_set(True)
for source in parts[1:]:
    union = body.modifiers.new("Polaczenie " + source.name, "BOOLEAN")
    union.operation = "UNION"
    union.solver = "EXACT"
    union.object = source
    bpy.ops.object.modifier_apply(modifier=union.name)

# Thin blade ends use 0.75mm; the substantial supports/feet use 3mm.
# Keep each value explicit instead of allowing a global shortest-edge clamp.
edge_bm = bmesh.new()
edge_bm.from_mesh(body.data)
weight_layer = edge_bm.edges.layers.float.new("bevel_weight_edge")
for edge in edge_bm.edges:
    a, b = (v.co for v in edge.verts)
    cap_edge = (abs(abs(a.x) - D["span_mm"]*MM/2) < 1e-7
                and abs(a.x-b.x) < 1e-7)
    edge[weight_layer] = (0.25 if cap_edge else 1.0) if edge.calc_face_angle() > math.radians(30) else 0.0
edge_bm.to_mesh(body.data)
edge_bm.free()
rounding = body.modifiers.new("Zaokraglenia - podpory 3mm, konce belki 0.75mm", "BEVEL")
rounding.width = D["edge_round_target_mm"] * MM
rounding.segments = 6
rounding.limit_method = "WEIGHT"
rounding.angle_limit = math.radians(30)
rounding.affect = "EDGES"
rounding.use_clamp_overlap = False
rounding.harden_normals = True
rounding.loop_slide = True
symmetry = body.modifiers.new("Symetria wzgledem osi samochodu", "MIRROR")
symmetry.use_axis[0] = True
symmetry.use_bisect_axis[0] = True
symmetry.use_clip = True
symmetry.merge_threshold = 0.001 * MM
for poly in body.data.polygons:
    poly.use_smooth = True
normals = body.modifiers.new("Normalne powierzchni", "WEIGHTED_NORMAL")
normals.keep_sharp = True
normals.weight = 50

for part in parts:
    part.hide_set(True)
    part.hide_render = True
source_coll.hide_render = True
source_coll.hide_viewport = True
body["Status"] = "WZORZEC / PROTOTYP GEOMETRII; mocowanie i wykonanie niezweryfikowane"
body["Wymiary_projektowe_mm"] = "1320 x 180 x 110"
body["Rozstaw_srodkow_podstaw_mm"] = D["support_centres_mm"]
body["Otwory_montazowe"] = "Nie wykonano: brak zweryfikowanej dokumentacji klapy"
body["Powierzchnie_styku"] = "Plaskie Z=0; wymagaja dopasowania do klapy"
body["Technologia"] = "Zewnetrzna pelna bryla wzorcowa; brak specyfikacji laminatu i wzmocnien"

for side, sign in (("L", -1), ("P", 1)):
    datum = bpy.data.objects.new("BAZA_" + side + " - sprawdzic na aucie", None)
    datum_coll.objects.link(datum)
    datum.empty_display_type = "PLAIN_AXES"
    datum.empty_display_size = 0.035
    datum.location = (sign * D["support_centres_mm"] * MM/2, 0, 0)
    datum.hide_render = True
    datum.hide_set(True)

depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
evaluated_mesh.calc_loop_triangles()
points = [body.matrix_world @ v.co for v in evaluated_mesh.vertices]
triangles = [tuple(t.vertices) for t in evaluated_mesh.loop_triangles]
bm = bmesh.new()
bm.from_mesh(evaluated_mesh)
nonmanifold = sum(not e.is_manifold for e in bm.edges)
inconsistent_winding = sum(not e.is_contiguous for e in bm.edges)
degenerate = sum(f.calc_area() < 1e-14 for f in bm.faces)
contact_area = sum(f.calc_area() for f in bm.faces if all(abs(v.co.z) < 1e-7 for v in f.verts)) / MM**2
volume = bm.calc_volume(signed=True)
dimensions = [(max(p[a] for p in points) - min(p[a] for p in points))/MM for a in range(3)]
minimum_z = min(p.z for p in points)/MM
assert nonmanifold == 0, f"Non-manifold edges: {nonmanifold}"
assert inconsistent_winding == 0, f"Inconsistent face winding: {inconsistent_winding}"
assert degenerate == 0, f"Degenerate faces: {degenerate}"
assert volume > 0, "Invalid orientation/volume"
for actual, target in zip(dimensions, (D["span_mm"], D["chord_mm"], D["overall_height_mm"])):
    assert abs(actual-target) < 0.08, (actual, target)
assert abs(minimum_z) < 0.01
assert contact_area > 20000, f"Insufficient planar contact datum area: {contact_area}"
bvh = BVHTree.FromPolygons(points, triangles, all_triangles=True)
symmetry_error_mm = max(bvh.find_nearest(Vector((-p.x, p.y, p.z)))[3] for p in points) / MM
assert symmetry_error_mm < 0.03, f"Left/right symmetry error: {symmetry_error_mm}"
overlap_candidates = [(i,j) for i,j in bvh.overlap(bvh)
                      if i < j and not set(triangles[i]).intersection(triangles[j])]
if overlap_candidates:
    (WORK / "overlap-debug.json").write_text(json.dumps([
        [[[round(c/MM,5) for c in points[v]] for v in triangles[t]] for t in pair]
        for pair in overlap_candidates], indent=2), encoding="utf-8")
assert not overlap_candidates, f"Non-adjacent triangle overlaps: {len(overlap_candidates)}"

# Count connected mesh components; Boolean union must produce one closed solid.
unseen = set(bm.verts)
components = 0
while unseen:
    components += 1
    todo = [unseen.pop()]
    while todo:
        vertex = todo.pop()
        for edge in vertex.link_edges:
            other = edge.other_vert(vertex)
            if other in unseen:
                unseen.remove(other)
                todo.append(other)
assert components == 1, f"Disconnected solids: {components}"
bm.free()

stl_path = OUT / "K01-wzorzec-1do1-MILIMETRY-nie-do-montazu.stl"
with stl_path.open("wb") as stream:
    stream.write(b"CELICA K01 | millimetres | NOMINAL EXTERIOR PATTERN | MOUNTS UNVERIFIED".ljust(80, b" "))
    stream.write(struct.pack("<I", len(triangles)))
    for tri in triangles:
        a, b, c = [points[i] / MM for i in tri]
        normal = (b-a).cross(c-a).normalized()
        stream.write(struct.pack("<12fH", *normal, *a, *b, *c, 0))

# Verify exported values, not only the mesh before export (STL is unitless).
blob = stl_path.read_bytes()
count = struct.unpack_from("<I", blob, 80)[0]
assert len(blob) == 84 + count*50
stl_low = [float("inf")]*3
stl_high = [-float("inf")]*3
for offset in range(84, len(blob), 50):
    values = struct.unpack_from("<12fH", blob, offset)
    for start in (3, 6, 9):
        for axis in range(3):
            value = values[start+axis]
            stl_low[axis] = min(stl_low[axis], value)
            stl_high[axis] = max(stl_high[axis], value)
stl_dimensions = [b-a for a,b in zip(stl_low, stl_high)]
assert all(abs(a-b) < 0.01 for a,b in zip(stl_dimensions, dimensions))
report = {
    "revision": "K01", "status": "nominal_geometry_checks_passed_not_vehicle_fit_approval",
    "dimensions_mm": dict(zip(("span", "chord", "height"), dimensions)),
    "stl_dimensions_mm": stl_dimensions,
    "connected_components": components, "non_manifold_edges": nonmanifold,
    "inconsistent_face_winding_edges": inconsistent_winding,
    "left_right_surface_symmetry_error_mm": symmetry_error_mm,
    "non_adjacent_triangle_overlap_candidates": len(overlap_candidates),
    "combined_flat_nominal_contact_area_mm2": contact_area,
    "degenerate_faces": degenerate, "triangles": count,
    "signed_pattern_volume_mm3": volume/(MM**3),
    "flat_contact_datum_min_z_mm": minimum_z,
    "stl_sha256": hashlib.sha256(blob).hexdigest(),
    "checks_not_performed": ["fit on actual car", "mount hole positions", "strength or fatigue",
                             "manufacturing wall thickness", "aerodynamic performance", "road approval"],
}
(ROOT / "kontrola-geometrii.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
evaluated.to_mesh_clear()


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat("-Z", "Y").to_euler()


def area(name, location, power, size, target, colour=(1,1,1), size_y=None):
    light = bpy.data.lights.new(name, "AREA")
    light.energy = power
    light.shape = "RECTANGLE"
    light.size = size
    light.size_y = size_y if size_y is not None else size
    light.color = colour
    obj = bpy.data.objects.new(name, light)
    studio_coll.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj


area("Softbox glowny", (-0.4,-0.75,1.05), 95, 1.45, (0,0,0.03), size_y=0.6)
area("Softbox krawedziowy", (0.3,0.50,0.80), 120, 1.4, (0,0,0.08), (0.72,0.83,1.0), 0.25)
area("Odbicie prawe", (1.25,-0.2,0.42), 45, 0.75, (0.25,0,0.05), (1.0,0.9,0.76), 0.6)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-0.0005))
floor = bpy.context.object
floor.name = "Podloze studia - nie jest klapa samochodu"
move_to(floor, studio_coll)
floor.data.materials.append(floor_mat)


def camera(name, location, target, ortho):
    c = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, c)
    camera_coll.objects.link(obj)
    obj.location = location
    c.type = "ORTHO"
    c.ortho_scale = ortho
    c.clip_start = 0.001
    c.clip_end = 1000
    aim(obj, target)
    return obj


hero = camera("01 Perspektywa", (1.55,-2.8,1.10), (0,0,0.055), 1.67)
front = camera("02 Przod - dwie podpory", (0,-3,0.055), (0,0,0.055), 1.54)
top = camera("03 Gora", (0,0,3), (0,0,0), 1.54)
side = camera("04 Profil", (3,0,0.055), (0,0,0.055), 0.235)
detail = camera("05 Detal polaczenia", (-1.0,-0.8,0.43), (-0.58,0,0.054), 0.36)
scene.camera = hero

notes = bpy.data.texts.new("PRZECZYTAJ - stan modelu K01")
notes.write("CELICA 1994 GT SPORT COUPE / PROJEKT WLASNY K01\n"
            "Model zewnetrzny w skali 1:1: 1320 x 180 x 110 mm.\n"
            "Wszystkie wymiary spojlera sa zalozeniami autorskimi, nie danymi OEM.\n"
            "Plaskie podstawy i rozstaw1218mm wymagaja pomiarow klapy. Brak otworow.\n"
            "Bryla jest pelnym wzorcem. Nie definiuje laminatu, scianek ani wzmocnien.\n"
            "STL ma wspolrzedne w MILIMETRACH i jest tylko do prototypu/przymiarki.\n"
            "Parametry: parametry.json; regeneracja: build_spoiler.py.\n"
            "Nie zapisuj plikow projektu poza JARVIS 1.0.\n")
script_text = bpy.data.texts.load(str(ROOT / "build_spoiler.py"))
script_text.name = "build_spoiler.py - kopia zrodlowa"
bpy.ops.object.select_all(action="DESELECT")
body.hide_set(False)
body.select_set(True)
bpy.context.view_layer.objects.active = body
for screen in bpy.data.screens:
    for area_ui in screen.areas:
        if area_ui.type == "VIEW_3D":
            space = area_ui.spaces.active
            space.clip_start = 0.001
            space.clip_end = 1000
            space.shading.type = "MATERIAL"
            space.overlay.show_overlays = False
            space.region_3d.view_perspective = "CAMERA"
scene.camera = hero
blend_path = ROOT / "Celica-1994-spojler-K01.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

for cam, filename, resolution in (
    (hero, "01-perspektywa.png", (1800,1200)),
    (front, "02-przod.png", (1800,650)),
    (top, "03-gora.png", (1800,650)),
    (side, "04-profil.png", (1200,850)),
    (detail, "05-detal.png", (1400,1050)),
):
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.filepath = str(PREVIEW / filename)
    bpy.ops.render.render(write_still=True)
print("PROJECT_SAVED", blend_path)
print("GEOMETRY", json.dumps(report))
