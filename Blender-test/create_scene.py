from pathlib import Path
import json
import sys

import bpy
from mathutils import Vector


OUTPUT = Path(__file__).resolve().parent / "test.blend"
EXPECTED = {"Podłoga", "Sześcian", "Kula"}


def verify_scene():
    objects = list(bpy.context.scene.objects)
    if {obj.name for obj in objects} != EXPECTED:
        raise RuntimeError("Zapisana scena nie zawiera oczekiwanych obiektów.")
    if not all(obj.type == "MESH" for obj in objects):
        raise RuntimeError("Obiekty sceny muszą być siatkami.")
    expected_geometry = {"Podłoga": (4, 1), "Sześcian": (8, 6)}
    for name, counts in expected_geometry.items():
        mesh = bpy.data.objects[name].data
        if (len(mesh.vertices), len(mesh.polygons)) != counts:
            raise RuntimeError(f"Niepoprawna geometria: {name}")
    if len(bpy.data.objects["Kula"].data.vertices) < 100:
        raise RuntimeError("Niepoprawna geometria kuli.")
    if not OUTPUT.is_file() or OUTPUT.stat().st_size == 0:
        raise RuntimeError("Plik nie został zapisany.")
    print(json.dumps({
        "status": "OK",
        "file": str(OUTPUT),
        "bytes": OUTPUT.stat().st_size,
        "objects": sorted(obj.name for obj in objects),
    }, ensure_ascii=True))


def material(name, color):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = 0.55
    return result


if "--verify" in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
    verify_scene()
else:
    if OUTPUT.exists():
        raise FileExistsError(f"Plik już istnieje: {OUTPUT}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Podłoga"
    floor.data.materials.append(material("Szara podłoga", (0.22, 0.27, 0.33)))

    bpy.ops.mesh.primitive_cube_add(size=2, location=(-2, 0, 1))
    cube = bpy.context.object
    cube.name = "Sześcian"
    cube.data.materials.append(material("Niebieski sześcian", (0.06, 0.32, 0.8)))

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=48, ring_count=24, radius=1, location=(2, 0, 1)
    )
    sphere = bpy.context.object
    sphere.name = "Kula"
    sphere.data.materials.append(material("Pomarańczowa kula", (0.95, 0.27, 0.045)))
    for polygon in sphere.data.polygons:
        polygon.use_smooth = True

    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.ops.object.select_all(action="DESELECT")
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube

    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.shading.type = "SOLID"
                space.shading.color_type = "MATERIAL"
                space.overlay.show_floor = False
                space.region_3d.view_location = (0, 0, 0.5)
                space.region_3d.view_rotation = Vector((8, -11, 9)).to_track_quat("Z", "Y")
                space.region_3d.view_distance = 14
                space.region_3d.view_perspective = "PERSP"

    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    verify_scene()
