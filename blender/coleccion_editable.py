"""Preparar el recorrido de la colección y sus tres encuadres web en la v24."""
from math import pi
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

scene = bpy.context.scene
source = Path(bpy.data.filepath)
assert source.name == "museo_portada_v24_lienzos.blend"
destination = source.with_name("museo_portada_v25_coleccion_final.blend")
if destination.exists():
    raise FileExistsError(destination)
assets = Path(sys.argv[sys.argv.index("--") + 1])
assets.mkdir(parents=True, exist_ok=True)
group = bpy.data.collections.new("Selected works · pared editorial")
scene.collection.children.link(group)

def center(obj):
    return sum((obj.matrix_world @ Vector(p) for p in obj.bound_box), Vector()) / 8

def finish(name, rgb, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Roughness"].default_value = roughness
    return mat

ink = finish("Grafito ciruela · seda", (.034, .023, .030), .82)
ground = finish("Lienzo crudo · fondo", (.45, .344, .265), .91)
gold = bpy.data.materials["Filete · latón satinado"]
bronze = bpy.data.materials["Bronce cepillado"]

def block(name, location, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.transform(Matrix.Diagonal(Vector((*size, 1))))
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    group.objects.link(obj)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Arista satinada", "BEVEL")
    bevel.width = min(.012, min(size) / 4)
    bevel.segments = 3
    obj.modifiers.new("Planos", "WEIGHTED_NORMAL")
    return obj

def border(x, z, width, height, y, thickness, mat):
    for sign in (-1, 1):
        block("Travesaño", (x,y,z+sign*(height+thickness)/2),
              (width+2*thickness,.042,thickness),mat)
        block("Montante", (x+sign*(width+thickness)/2,y,z),
              (thickness,.042,height),mat)

moses = scene.objects["The Finding of Moses"]
rohan = scene.objects["Rohan au Louvre"]
original = center(rohan)
placement = (Matrix.Translation(center(moses)) @ Matrix.Rotation(pi/2, 4, "Z")
             @ Matrix.Translation(-original))
assert center(moses).x < 0
for obj in (rohan, scene.objects["Marco a medida · Rohan au Louvre"]):
    obj.matrix_world = placement @ obj.matrix_world
for title in ("The Finding of Moses","The Feast of the Gods","Portrait of a Young Man in Red"):
    for name in (title,"Marco a medida · "+title):
        bpy.data.objects.remove(scene.objects[name], do_unlink=True)
for obj in list(scene.objects):
    if obj.name.startswith("Cartela ·"):
        bpy.data.objects.remove(obj, do_unlink=True)

wall = next(obj for obj in scene.objects if obj.name.startswith("Muro de exposición"))
wall.data = wall.data.copy()
wall.data.materials[0] = ink
slots = []
for obj in scene.objects:
    if obj.name.startswith(("Pilastra de fondo","Filete de pilastra","Capitel de fondo",
                            "Aplique ·","Luz del aplique")) and abs(obj.location.x)<2:
        obj.location.x = 1.48 if obj.location.x > 0 else -1.48
for x in (-3, 0, 3):
    border(x,3.04,2.76,2.51,20.994,.014,gold)
    slots.append(block("Lienzo editable", (x,20.944,3.03),(2.48,.05,1.55),ground))
    border(x,3.03,2.48,1.55,20.914,.065,bronze)
    border(x,3.03,2.48,1.55,20.88,.014,gold)

cam = bpy.data.objects.new("Camera_Coleccion", bpy.data.cameras.new("Colección editorial"))
group.objects.link(cam)
for frame, label, position, target, lens in (
    (1,"The Collection",(0,7.30,2.98),(0,9,2.22),30),
    (46,"Bóveda",(0,7.65,2.78),(0,14,7.35),19),
    (75,"Pared de proyectos",(0,10.1,3.48),(0,21,3.58),30),
    (108,"Selected works · frontal",(0,12.04,3.03),(0,21,3.03),34),
):
    cam.location = position
    cam.rotation_euler = (Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.lens = lens
    for path in ("location","rotation_euler"):
        cam.keyframe_insert(data_path=path, frame=frame)
    cam.data.keyframe_insert(data_path="lens", frame=frame)
    # El recorrido de la v24 sigue disponible en su archivo original.
    if frame == 1:
        for marker in list(scene.timeline_markers):
            if marker.frame > 0:
                scene.timeline_markers.remove(marker)
    marker = scene.timeline_markers.new(label, frame=frame)
    if frame == 1:
        marker.camera = cam

scene.frame_end = 108
scene.frame_set(108)
for obj in slots:
    for corner in obj.bound_box:
        p = world_to_camera_view(scene, cam, obj.matrix_world @ Vector(corner))
        assert .02 < p.x < .98 and .03 < p.y < .97, (obj.name, p)
    direction = center(obj)-cam.location
    hit = scene.ray_cast(bpy.context.evaluated_depsgraph_get(), cam.location, direction.normalized())
    assert hit[4] == obj, (obj.name, hit[4])

# Registrar la abertura interior en coordenadas normalizadas del último plano.
import json
rects = []
for x in (-3,0,3):
    a,b = [world_to_camera_view(scene,cam,Vector((x+i*1.24,20.88,3.03+i*.775))) for i in (-1,1)]
    rects.append(dict(left=a.x,top=1-b.y,width=b.x-a.x,height=b.y-a.y))
(assets/"frames.json").write_text(json.dumps(rects, indent=2),encoding="utf-8")
scene.frame_set(0)
scene.render.filepath = "//coleccion_v25_frames/frame_"
bpy.ops.wm.save_as_mainfile(filepath=str(destination))

# Fotogramas de muestra para la web, con el arte temporal fuera de la exportación.
rohan.hide_render = True
scene.render.engine = "CYCLES"
scene.cycles.samples = 5
scene.cycles.use_denoising = True
scene.render.resolution_x,scene.render.resolution_y = 1280,720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 90
for frame, name in ((1,"atril"),(46,"boveda"),(108,"pared")):
    scene.frame_set(frame)
    scene.render.filepath = str(assets/(name+".jpg"))
    bpy.ops.render.render(write_still=True)
