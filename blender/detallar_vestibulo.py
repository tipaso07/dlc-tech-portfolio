"""Desde la v20, preparar el interior con obras temporales empaquetadas."""
from pathlib import Path
from math import cos, sin, pi
import bpy
from mathutils import Vector

s = bpy.context.scene
source = Path(bpy.data.filepath)
assert source.name == "museo_portada_v20_entrada_galeria.blend"
out = source.with_name("museo_portada_v21_sala_veneciana.blend")
if out.exists():
    raise FileExistsError(out)

def collection(name):
    result = bpy.data.collections.new(name)
    s.collection.children.link(result)
    return result

detail = collection("Sala · intarsia, estucos y apliques")
art = collection("Obras temporales · ocultar al instalar proyectos")
materials = bpy.data.materials
gold = materials["Filete · latón satinado"]
brass = materials["Bronce cepillado"]
plum = materials["Granate · piedra pulida"]
wood = materials["Nogal aceitado"]
cream = materials["Caliza apomazada"]
green = materials["Lienzo · verde laguna"]

def material(name, color):
    m = materials.new(name)
    m.diffuse_color = (*color,1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color,1)
    return m,p

def marble(name, color, vein):
    mat, shader = material(name,color)
    tree = mat.node_tree
    tex = tree.nodes.new("ShaderNodeTexCoord")
    wave = tree.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 1.4
    wave.inputs["Distortion"].default_value = 8
    wave.inputs["Detail Scale"].default_value = .8
    tree.links.new(tex.outputs["Object"],wave.inputs["Vector"])
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*vein,1)
    ramp.color_ramp.elements[1].position = .095
    ramp.color_ramp.elements[1].color = (*color,1)
    tree.links.new(wave.outputs["Fac"],ramp.inputs[0])
    tree.links.new(ramp.outputs[0],shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = .36
    return mat

light_stone = marble("Intarsia · avorio",(.55,.43,.31),(.33,.26,.21))
dark_stone = marble("Intarsia · verde antico",(.074,.135,.113),(.27,.31,.21))
red_stone = marble("Intarsia · rosso Verona",(.32,.137,.095),(.53,.31,.19))

def geometry(name, vertices, faces, group, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],faces)
    data.update()
    o = bpy.data.objects.new(name,data)
    group.objects.link(o)
    data.materials.append(mat)
    return o

def box(name, pos, size, mat, group=detail):
    vx = [(a*size[0]/2,b*size[1]/2,c*size[2]/2) for c in (-1,1)
          for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    o = geometry(name,vx,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],group,mat)
    o.location = pos
    mod = o.modifiers.new("Cantos pulidos","BEVEL")
    mod.width = min(.015,min(size)*.2)
    mod.segments = 2
    o.modifiers.new("Normales","WEIGHTED_NORMAL")
    return o

# Octágonos y tacos comparten un lecho de juntas. La cara superior queda
# entre el pavimento v20 y el envés del tapiz.
vertices, faces, slots = [],[],[]
def tile(points, slot):
    faces.append(tuple(range(len(vertices),len(vertices)+len(points))))
    vertices.extend((x,y,1.0793) for x,y in points)
    slots.append(slot)

pitch,half,corner = .78,.386,.11
for i in range(-6,7):
    for j in range(14):
        x,y = i*pitch,3.54+j*pitch
        octagon = [(-half+corner,-half),(half-corner,-half),(half,-half+corner),
                   (half,half-corner),(half-corner,half),(-half+corner,half),
                   (-half,half-corner),(-half,-half+corner)]
        tile([(x+a,y+b) for a,b in octagon],int((i+j)%2==0))
        if i<6 and j<13:
            cx,cy=x+pitch/2,y+pitch/2
            tile([(cx,cy-corner),(cx+corner,cy),(cx,cy+corner),(cx-corner,cy)],2)
tiles=geometry("Pavimento · octágonos y tacos de mármol",vertices,faces,detail,light_stone)
tiles.data.materials.append(red_stone)
tiles.data.materials.append(dark_stone)
for face,slot in zip(tiles.data.polygons,slots):
    face.material_index=slot
for side in (-1,1):
    box("Cenefa perimetral",(side*5.15,8.65,1.081),(.14,10.98,.003),dark_stone)
    box("Listelo de pavimento",(side*5.04,8.65,1.083),(.026,10.98,.002),gold)
    x=side*5.25
    for y in (4.3,7.5,10.7,13.6):
        box("Pilastra de caliza",(x,y,3.23),(.20,.32,3.62),cream)
        box("Basa escalonada",(x-side*.04,y,1.49),(.32,.46,.60),red_stone)
        box("Capitel moldurado",(x-side*.04,y,4.88),(.34,.49,.19),cream)
        box("Collarino",(x-side*.03,y,4.72),(.27,.4,.048),gold)
    for z in (1.68,2.02,4.59):
        box("Moldura lateral",(side*5.302,8.72,z),(.09,11.12,.065),brass)
for x in (-4.62,-1.72,1.72,4.62):
    box("Pilastra de fondo",(x,14.04,3.29),(.19,.17,3.28),cream)
    box("Filete de pilastra",(x,13.947,3.29),(.034,.02,3.21),gold)
    box("Capitel de fondo",(x,14.01,4.89),(.34,.23,.17),cream)
for z,h,mat in ((1.69,.08,red_stone),(1.75,.025,gold),(4.65,.1,wood),(4.73,.035,gold),(5.01,.17,cream)):
    box("Friso de galería",(0,14.034,z),(10.68,.18,h),mat)
for x in (-3.75,-1.25,1.25,3.75):
    box("Nervio de artesonado",(x,8.7,5.23),(.115,11.05,.11),wood)

opal, shader = material("Alabastro cálido",(.87,.64,.38))
shader.inputs["Emission Color"].default_value=(1,.62,.32,1)
shader.inputs["Emission Strength"].default_value=1.4
for x in (-4.6, -1.72,1.72,4.6):
    box("Aplique · florón",(x,13.905,3.62),(.21,.09,.32),brass)
    box("Aplique · brazo",(x,13.77,3.56),(.062,.24,.065),brass)
    box("Aplique · taza",(x,13.65,3.62),(.20,.18,.075),gold)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=(x,13.65,3.81))
    globe=bpy.context.object
    globe.name="Aplique · tulipa de alabastro"
    globe.users_collection[0].objects.unlink(globe)
    detail.objects.link(globe)
    globe.scale=(.105,.092,.17)
    globe.data.materials.append(opal)
    for p in globe.data.polygons:
        p.use_smooth=True
    bulb=bpy.data.lights.new("Luz del aplique","POINT")
    bulb.energy,bulb.color,bulb.shadow_soft_size=12,(1,.70,.45),.18
    o=bpy.data.objects.new(bulb.name,bulb)
    detail.objects.link(o)
    o.location=(x,13.42,3.88)

images_dir=source.parent/"referencias_galeria_v21"
works=[
    (-3,1.68,1.38,"retrato.jpg","Portrait of a Young Man in Red","Giovanni Bellini",
     "https://www.nga.gov/artworks/36-portrait-young-man-red",(0,1)),
    (0,2.65,1.83,"festin.jpg","The Feast of the Gods","Giovanni Bellini · Titian",
     "https://www.nga.gov/artworks/1138-feast-gods",(0,1)),
    (3,1.68,1.38,"rohan.jpg","Rohan au Louvre","Hirohiko Araki",
     "https://boutique.louvre.fr/fr/product/1869-rohan-au-louvre.html",(108/728,637/728))]
for x,w,h,file,title,author,url,(u0,u1) in works:
    img=bpy.data.images.load(str(images_dir/file))
    assert min(img.size)>300, file
    img.pack()
    mat,p=material(title,(.55,.46,.34))
    tree=mat.node_tree
    tex=tree.nodes.new("ShaderNodeTexImage")
    tex.image=img
    tree.nodes.active=tex
    tree.links.new(tex.outputs["Color"],p.inputs["Base Color"])
    p.inputs["Roughness"].default_value=.79
    ratio=img.size[0]*(u1-u0)/img.size[1]
    height=min(h-.07,(w-.07)/ratio)
    width=height*ratio
    o=geometry(title,[(x+a*width/2,14.009,3.02+b*height/2)
                      for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))],[(0,1,2,3)],art,mat)
    uv=o.data.uv_layers.new(name="Reproducción")
    for loop,point in zip(uv.data,((u0,0),(u1,0),(u1,1),(u0,1))):
        loop.uv=point
    o["Autor"],o["Fuente"]=author,url
    box("Cartela · "+title,(x,14.046,3.02-h/2-.24),(1.34,.08,.20),brass,art)
    font=bpy.data.curves.new(title+" · cartela","FONT")
    font.body=title+"\n"+author
    font.align_x,font.align_y,font.size="CENTER","CENTER",.068
    label=bpy.data.objects.new("Cartela · inscripción",font)
    art.objects.link(label)
    label.location=(x,13.999,3.02-h/2-.24)
    label.rotation_euler.x=pi/2
    font.materials.append(materials["Seda · crudo"])

s.frame_set(244)
graph=bpy.context.evaluated_depsgraph_get()
for x,_,_,_,title,*_rest in works:
    origin=s.camera.matrix_world.translation
    direction=Vector((x,14.009,3.02))-origin
    hit,_,_,_,obj,_=s.ray_cast(graph,origin,direction.normalized())
    assert hit and obj.name==title,(title,obj)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=="VIEW_3D":
            a.spaces.active.shading.color_type="TEXTURE"
s.render.filepath="//museo_sala_v21_frames/frame_"
bpy.ops.wm.save_as_mainfile(filepath=str(out))
