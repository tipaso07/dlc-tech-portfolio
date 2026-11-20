"""Ajustar los remates de la pared expositiva de v25 y actualizar su vista frontal."""
from pathlib import Path
import sys

import bpy
from mathutils import Vector


scene = bpy.context.scene
source = Path(bpy.data.filepath)
assert source.name == "museo_portada_v25_coleccion_final.blend"
destination = source.with_name("museo_portada_v26_remates.blend")
if destination.exists():
    raise FileExistsError(destination)
preview = Path(sys.argv[sys.argv.index("--") + 1])
group = bpy.data.collections["Selected works · pared editorial"]


def limits(obj):
    heights = [(obj.matrix_world @ Vector(p)).z for p in obj.bound_box]
    return min(heights), max(heights)


def fit_height(obj, bottom, top):
    old_bottom, old_top = limits(obj)
    obj.scale.z *= (top-bottom)/(old_top-old_bottom)
    bpy.context.view_layer.update()
    obj.location.z += bottom-limits(obj)[0]


# Los frisos continuos reciben los extremos de las cuatro pilastras.
rails = sorted((o for o in scene.objects if o.name.startswith("Friso de galería")),
               key=lambda o: limits(o)[0])
bottom = limits(rails[1])[1]
top = limits(rails[2])[0]
assert 1.7 < bottom < 1.8 and 4.5 < top < 4.7
pilasters = []
stripes = []
for obj in scene.objects:
    if obj.name.startswith(("Pilastra de fondo", "Filete de pilastra", "Capitel de fondo",
                            "Aplique ·", "Luz del aplique")):
        obj.location.x = (1 if obj.location.x > 0 else -1) * (1.5 if abs(obj.location.x)<3 else 4.5)
    if obj.name.startswith("Pilastra de fondo"):
        pilasters.append(obj)
        fit_height(obj,bottom,top)
    elif obj.name.startswith("Filete de pilastra"):
        stripes.append(obj)
        fit_height(obj,bottom+.045,top-.045)


def molding(name, x, width, height, profile, materials):
    """Un solo perfil continuo alrededor de los cuatro ingletes."""
    vertices = []
    faces = []
    for outset, y, _ in profile:
        for sx, sz in ((-1,-1),(1,-1),(1,1),(-1,1)):
            vertices.append((x+sx*(width/2+outset), y, 3.03+sz*(height/2+outset)))
    for k in range(len(profile)):
        following = (k+1) % len(profile)
        for j in range(4):
            end = (j+1) % 4
            faces.append((4*k+j,4*k+end,4*following+end,4*following+j))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for mat in materials:
        mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.material_index = profile[poly.index//4][2]
    obj = bpy.data.objects.new(name,mesh)
    group.objects.link(obj)
    return obj


old = [o for o in group.objects if o.name.startswith(("Travesaño","Montante"))]
assert len(old)==36 and len(pilasters)==len(stripes)==4
for obj in old:
    bpy.data.objects.remove(obj,do_unlink=True)
gold = bpy.data.materials["Filete · latón satinado"]
bronze = bpy.data.materials["Bronce cepillado"]
for x in (-3,0,3):
    molding("Marco continuo · bronce y latón",x,2.48,1.55,
            [(0,20.88,1),(.012,20.88,1),(.018,20.893,0),(.048,20.887,0),
             (.059,20.893,0),(.059,20.951,0),(0,20.951,0)], [bronze,gold])
    molding("Recuadro de latón",x,2.70,2.30,
            [(0,21.015,0),(0,20.988,0),(.012,20.988,0),(.012,21.015,0)],[gold])
bpy.context.view_layer.update()
assert all(abs(limits(o)[0]-bottom)<.001 and abs(limits(o)[1]-top)<.001 for o in pilasters)
assert all(bottom+.04<limits(o)[0] and limits(o)[1]<top-.04 for o in stripes)
assert (1.5-.19/2)-(2.70/2+.012)>.04

scene.frame_set(0)
scene.render.filepath="//coleccion_v26_frames/frame_"
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
scene.frame_set(108)
scene.objects["Rohan au Louvre"].hide_render=True
scene.render.engine="CYCLES"
scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.resolution_x,scene.render.resolution_y=1280,720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="JPEG"
scene.render.image_settings.quality=90
scene.render.filepath=str(preview)
bpy.ops.render.render(write_still=True)
