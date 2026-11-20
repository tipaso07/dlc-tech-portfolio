"""Preparar el recorrido de la colección a partir del exterior v19."""
from pathlib import Path
from math import radians
import bmesh
import bpy
from mathutils import Vector

s = bpy.context.scene
source = Path(bpy.data.filepath)
assert source.name == "museo_portada_v19_esquinas.blend"
destination = source.with_name("museo_portada_v20_entrada_galeria.blend")
if destination.exists():
    raise FileExistsError(destination)

def collection(name):
    group = bpy.data.collections.new(name)
    s.collection.children.link(group)
    return group

doors = collection("Entrada · carpintería original")
hall = collection("Vestíbulo · arquitectura")
exhibit = collection("Colección · atril y marcos")
rig = collection("Recorrido · cámaras e iluminación")

def mesh(name, polygons, mat, group):
    data = bpy.data.meshes.new(name)
    verts, faces = [], []
    for poly in polygons:
        faces.append(tuple(range(len(verts), len(verts) + len(poly))))
        verts.extend(poly)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    data.materials.append(mat)
    return obj

def finish(name, rgb, roughness, metal=0, grain=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    tree = mat.node_tree
    shader = tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*rgb, 1)
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = roughness
    if grain:
        noise = tree.nodes.new("ShaderNodeTexNoise")
        coord = tree.nodes.new("ShaderNodeTexCoord")
        tree.links.new(coord.outputs["Object"], noise.inputs["Vector"])
        noise.inputs["Scale"].default_value = grain
        bump = tree.nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = .013
        bump.inputs["Strength"].default_value = .23
        tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat

bronze = finish("Bronce cepillado", (.42,.23,.094), .34, .72, 65)
gilt = finish("Filete · latón satinado", (.67,.44,.18), .32,.64)
wall = finish("Estuco de cal · tierra rosada", (.36,.20,.15), .87, grain=30)
floor = finish("Caliza apomazada", (.43,.32,.24), .52, grain=45)
plum = finish("Granate · piedra pulida", (.105,.042,.055), .31, grain=16)
felt = finish("Lienzo · verde laguna", (.044,.099,.086), .91, grain=85)
rug = finish("Lana · burdeos", (.22,.033,.056), .94, grain=140)
thread = finish("Seda · oro viejo", (.52,.34,.15), .72, grain=96)
ivory = finish("Seda · crudo", (.72,.59,.44), .79)
wood = bpy.data.materials["Nogal aceitado"]

def box(name, location, size, mat, group=hall, bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    for vertex in obj.data.vertices:
        for i in range(3):
            vertex.co[i] *= size[i]
    obj.users_collection[0].objects.unlink(obj)
    group.objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        edge = obj.modifiers.new("Canto", "BEVEL")
        edge.width = min(bevel, min(size)/4)
        edge.segments = 3
        obj.modifiers.new("Normales", "WEIGHTED_NORMAL")
    return obj

def hinge(side):
    obj = bpy.data.objects.new("Bisagra " + ("izquierda" if side < 0 else "derecha"), None)
    doors.objects.link(obj)
    obj.location = (side*1.75,2.79,1.06)
    obj.empty_display_size = .12
    return obj

pivots = {side:hinge(side) for side in (-1,1)}
def attach(obj, side):
    bpy.context.view_layer.update()
    matrix = obj.matrix_world.copy()
    obj.parent = pivots[side]
    obj.matrix_world = matrix

# Las piezas históricas están agrupadas por material. Extraer sólo las caras
# del portal y conservar in situ el montante de arco situado sobre las hojas.
lintel = 3.94
for name in ("Postes de amarre","Piedra en sombra","Hierro patinado"):
    original = s.objects[name]
    bm = bmesh.new()
    bm.from_mesh(original.data)
    pieces = {-1:[],1:[]}
    remove = []
    for face in bm.faces:
        c = face.calc_center_median()
        pts = [v.co.copy() for v in face.verts]
        if name == "Piedra en sombra" and abs(c.y-3)<.001 and face.calc_area()>350:
            remove.append(face)
            for x0,x1,z0,z1 in ((-21,-1.75,1,9),(1.75,24,1,9),(-1.75,1.75,lintel,9)):
                corners = [(x0,3,z0),(x1,3,z0),(x1,3,z1),(x0,3,z1)]
                mesh("Muro original · vano", [corners], original.active_material, doors)
            continue
        if not all(abs(p.x)<1.81 and 2.34<p.y<2.86 and 1.04<p.z<5.3 for p in pts):
            continue
        # Recortar los montantes y la tabla posterior a la altura del dintel.
        if max(p.z for p in pts) > lintel+.04:
            for v in face.verts:
                if v.co.z < lintel:
                    v.co.z = lintel
            continue
        if name=="Hierro patinado" and c.y>2.6:
            if c.z < lintel:
                remove.append(face)
            continue
        side = -1 if c.x<0 else 1
        pieces[side].append(pts)
        remove.append(face)
    for side, polys in pieces.items():
        if not polys:
            raise RuntimeError(f"Falta carpintería {name} {side}")
        obj = mesh(name+" · hoja", polys, wood if name=="Postes de amarre" else original.active_material, doors)
        attach(obj, side)
    bmesh.ops.delete(bm,geom=remove,context="FACES")
    bm.to_mesh(original.data)
    bm.free()

for side,pivot in pivots.items():
    attach(box("Bastidor de nogal",(side*.875,2.815,2.50),(1.742,.085,2.865),wood,doors),side)
    for z in (1.48,3.48):
        attach(box("Herraje de hoja",(side*1.48,2.594,z),(.46,.03,.068),bronze,doors),side)
    for frame,angle in ((1,0),(14,0),(72,92)):
        pivot.rotation_euler.z = radians(-side*angle)
        pivot.keyframe_insert(data_path="rotation_euler",frame=frame)

box("Pavimento interior",(0,8.7,1.059),(11,11.4,.038),floor)
box("Techo casetonado",(0,8.7,5.38),(11,11.4,.18),wall)
for side in (-1,1):
    x = side*5.42
    box("Estuco lateral",(x,8.7,3.22),(.16,11.4,4.3),wall)
    box("Zócalo lateral",(x-side*.105,8.7,1.36),(.10,11.4,.56),plum)
    box("Cornisa lateral",(x-side*.12,8.7,5.05),(.19,11.4,.13),bronze)
for y in (4,6.5,9,11.5,14):
    box("Viga tallada",(0,y,5.18),(10.8,.19,.18),wood)
box("Muro de exposición",(0,14.25,3.20),(10.85,.17,4.25),wall)
box("Zócalo de exposición",(0,14.10,1.35),(10.8,.12,.53),plum)
box("Tapiz corredor",(0,6.29,1.092),(2.44,6.3,.024),rug)
for side in (-1,1):
    for x,w,mat in ((1.16,.016,ivory),(1.05,.042,thread),(.93,.025,felt)):
        box("Orla tejida",(side*x,6.29,1.105),(w,6.17,.002),mat,bevel=0)

def diamond(x,y,r,mat,z):
    quads = []
    points = [(0,1),(1,0),(0,-1),(-1,0)]
    for a,b in zip(points,points[1:]+points[:1]):
        quads.append([(x+k*i,y+k*j,z) for (i,j),k in ((a,r),(a,r*.86),(b,r*.86),(b,r))])
    mesh("Bordado · losange",quads,mat,hall)
for i in range(8):
    for x in (-.7,.7):
        diamond(x,3.65+i*.75,.19,thread,1.106)

box("Atril · basamento",(0,9,1.17),(1.14,.76,.18),plum,exhibit,.045)
box("Atril · plinto",(0,9,1.29),(.89,.59,.07),bronze,exhibit)
box("Atril · pedestal",(0,9,1.72),(.44,.32,.81),plum,exhibit,.045)
desk = box("Atril · tablero",(0,9,2.23),(1.64,.94,.09),bronze,exhibit,.035)
desk.rotation_euler.x = radians(34)
def on_desk(obj, offset):
    obj.parent = desk
    obj.location = offset
plate = box("Atril · placa esmaltada",(0,0,0),(1.55,.85,.024),felt,exhibit)
on_desk(plate,(0,0,.05))
for words,y,size in (("THE COLLECTION",.086,.135),("SEBASTIÁN DÍAZ",-.125,.102)):
    font = bpy.data.curves.new(words,"FONT")
    font.body, font.align_x, font.size = words,"CENTER",size
    font.extrude = .0008
    lettering = bpy.data.objects.new(words,font)
    exhibit.objects.link(lettering)
    font.materials.append(ivory)
    on_desk(lettering,(0,y,.064))

for x,w,h in ((-3,1.68,1.38),(0,2.65,1.83),(3,1.68,1.38)):
    z = 3.02
    box("Fondo de exposición",(x,14.075,z),(w,.105,h),felt,exhibit)
    for side in (-1,1):
        box("Marco · montante",(x+side*(w/2+.035),14.01,z),(.07,.13,h+.14),bronze,exhibit)
        box("Marco · travesaño",(x,14.01,z+side*(h/2+.035)),(w,.13,.07),bronze,exhibit)
        box("Filete interior",(x+side*(w/2-.014),13.997,z),(.018,.018,h),gilt,exhibit)

def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def light(name,pos,target,power,size,color):
    data = bpy.data.lights.new(name,"AREA")
    data.energy, data.shape, data.size, data.color = power,"DISK",size,color
    obj = bpy.data.objects.new(name,data)
    rig.objects.link(obj)
    obj.location = pos
    aim(obj,target)

light("Luz del umbral",(0,5,4.75),(0,3,1.7),180,2,(1,.78,.59))
light("Luz del atril",(-1.8,7.7,4.85),(0,9,2),265,1.6,(1,.84,.66))
light("Relleno lateral",(4,8,4),(0,9,2),130,2.8,(.82,.89,1))
for x in (-3,0,3):
    light("Baño de pared",(x,12.7,4.8),(x,14,2.9),155,1,(1,.84,.67))

hero = s.camera
hero.name = "Camera_Hero"
shots = [
    (1,"DoorArrival",(1.45,-4.0,2.86),(0,2.8,2.78),31),
    (54,None,(1.24,.56,2.63),(0,3.9,2.54),26),
    (70,"Threshold",(.12,1.38,2.54),(0,8.9,2.36),28),
    (112,None,(0,5.85,2.62),(0,9,2.23),33),
    (150,"Lectern",(0,7.30,2.98),(0,9,2.22),42),
    (169,None,(0,7.30,2.98),(0,9,2.22),42),
    (202,None,(1.62,8.52,2.72),(.46,12.35,2.89),31),
    (244,"SelectedWorks",(1,9.78,2.70),(.45,14.1,3.02),18),
    (264,None,(1,9.78,2.70),(.45,14.1,3.02),18)]

def camera(name):
    data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name,data)
    rig.objects.link(cam)
    return cam

travel = camera("Camera_Recorrido")
for frame,name,pos,target,lens in shots:
    travel.location = pos
    aim(travel,target)
    travel.data.lens = lens
    travel.keyframe_insert(data_path="location",frame=frame)
    travel.keyframe_insert(data_path="rotation_euler",frame=frame)
    travel.data.keyframe_insert(data_path="lens",frame=frame)
    if name:
        still = camera("Camera_"+name)
        still.location, still.rotation_euler, still.data.lens = pos,travel.rotation_euler,lens
        s.timeline_markers.new(name,frame=frame)
s.camera = travel
s.frame_end = 264
s.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_perspective = "CAMERA"
            area.spaces.active.shading.color_type = "MATERIAL"
            area.spaces.active.overlay.show_overlays = False

# Comprobar en la geometría evaluada que el hueco deja pasar tres rayos
# a la altura de una persona, y que el recorrido no atraviesa superficies.
def ray(origin, direction, distance):
    hit,_,_,_,obj,_ = s.ray_cast(bpy.context.evaluated_depsgraph_get(),
                                  Vector(origin),Vector(direction).normalized(),distance=distance)
    return obj.name if hit else None

s.frame_set(1)
assert ray((.5,1.4,2.5),(0,1,0),2)
s.frame_set(75)
for x in (-.65,0,.65):
    hit = ray((x,1.4,2.5),(0,1,0),3)
    assert not hit, (x,hit)
last = None
for frame in range(1,265):
    s.frame_set(frame)
    pos = travel.matrix_world.translation.copy()
    if last and (pos-last).length>.00001:
        hit = ray(last,pos-last,(pos-last).length+.025)
        assert not hit, (frame,hit)
    last = pos
s.frame_set(1)
s.render.filepath = "//museo_entrada_v20_frames/frame_"
bpy.ops.wm.save_as_mainfile(filepath=str(destination))
print("Validado umbral y recorrido de 264 cuadros:",destination)
