"""Mover los dos lienzos laterales al paño contiguo hacia la entrada."""
from pathlib import Path

import bpy
from mathutils import Vector

scene = bpy.context.scene
source = Path(bpy.data.filepath)
assert source.name == "museo_portada_v23_arcadas_marcos.blend"
destination = source.with_name("museo_portada_v24_lienzos.blend")
if destination.exists():
    raise FileExistsError(destination)

def corners(obj):
    return [obj.matrix_world @ Vector(p) for p in obj.bound_box]

for title in ("The Finding of Moses", "Grand Canal with the Rialto Bridge, Venice"):
    canvas = scene.objects[title]
    frame = scene.objects["Marco a medida · " + title]
    center = sum(corners(canvas), Vector()) / 8
    pillars = sorted((o for o in scene.objects if o.name.startswith("Pilastra de caliza")
                      and o.location.x * center.x > 0 and o.location.y < center.y),
                     key=lambda o: o.location.y)
    left, right = pillars[-2:]
    low = max(p.y for p in corners(left))
    high = min(p.y for p in corners(right))
    target = (low + high) / 2
    lamps = [o for o in scene.objects if o.name.startswith("Luz de lienzo")
             and o.location.x * center.x > 0 and abs(o.location.y - center.y) < .01]
    lamp, = lamps
    for obj in (canvas, frame, lamp):
        obj.location.y += target - center.y
    bpy.context.view_layer.update()
    margin_a = min(p.y for p in corners(frame)) - low
    margin_b = high - max(p.y for p in corners(frame))
    assert margin_a > 0 and abs(margin_a - margin_b) < .001
    assert abs(lamp.location.y - target) < .001
    print(f"{title}: Y={target:.3f}, margen a cada pilastra={margin_a:.3f}")

bpy.ops.wm.save_as_mainfile(filepath=str(destination))
