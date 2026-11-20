"""Ampliar la galería v21 y documentar las cámaras evaluadas de la v22."""
import bpy
import bmesh
from math import cos, sin, pi, degrees
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

s = bpy.context.scene
src = Path(bpy.data.filepath)
assert src.name == "museo_portada_v21_sala_veneciana.blend"
dest = src.with_name("museo_portada_v22_boveda.blend")
notes = src.with_name("ubicaciones.md")
if dest.exists() or notes.exists():
    raise FileExistsError("Revisar v22 y ubicaciones.md antes de volver a ejecutar.")
groups = bpy.data.collections
art = groups["Obras temporales · ocultar al instalar proyectos"]
architecture = groups.new("Sala mayor · bóveda y boiseries")
s.collection.children.link(architecture)
gold = bpy.data.materials["Filete · latón satinado"]
cream = bpy.data.materials["Caliza apomazada"]
bronze = bpy.data.materials["Bronce cepillado"]

def surface(name, points, faces, mat, group=architecture, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(points, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    group.objects.link(obj)
    data.materials.append(mat)
    if uv:
        layer = data.uv_layers.new(name="Pintura")
        for loop in data.loops:
            layer.data[loop.index].uv = uv[loop.vertex_index]
    return obj

def line(name, points, radius, mat, closed=False, group=architecture):
    curve = bpy.data.curves.new(name,"CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    path = curve.splines.new("POLY")
    path.points.add(len(points)-1)
    for p,xyz in zip(path.points,points):
        p.co = (*xyz,1)
    path.use_cyclic_u = closed
    obj = bpy.data.objects.new(name,curve)
    group.objects.link(obj)
    curve.materials.append(mat)
    return obj

def enlarge(o):
    o.location.x *= 1.25
    o.location.y = 3+(o.location.y-3)*1.625
    o.scale.x *= 1.25
    o.scale.y *= 1.625

for group in (groups["Vestíbulo · arquitectura"],groups["Sala · intarsia, estucos y apliques"],
              groups["Colección · atril y marcos"],art,groups["Recorrido · cámaras e iluminación"]):
    for o in list(group.objects):
        n=o.name
        if o.parent or o.type=="CAMERA":
            continue
        if n.startswith(("Techo casetonado","Nervio de artesonado","Viga tallada")):
            o.hide_viewport = o.hide_render = True
        elif group==art or n.startswith(("Marco ·","Fondo de exposición","Filete interior","Pilastra de fondo",
              "Filete de pilastra","Capitel de fondo","Aplique ·","Luz del aplique","Baño de pared")):
            o.location.y += 7
        elif n.startswith(("Friso de galería","Muro de exposición","Zócalo de exposición")):
            o.location.y += 7
            o.scale.x *= 1.25
        elif n.startswith(("Pavimento","Cenefa","Listelo","Estuco lateral","Zócalo lateral","Cornisa lateral","Moldura lateral")):
            enlarge(o)
        elif n.startswith(("Pilastra de caliza","Basa escalonada","Capitel moldurado","Collarino")):
            o.location.x *= 1.25
            o.location.y = 3+(o.location.y-3)*1.625

# Recortar únicamente el volumen interior en las antiguas caras de forjados
# y traseras. La fachada y el techo que se ven desde la laguna quedan intactos.
limits=[(0,-6.73,1),(0,6.73,-1),(1,3.012,1),(1,21.23,-1),(2,1.078,1),(2,8.25,-1)]
def clip(poly, axis, threshold, sign):
    result=[]
    for a,b in zip(poly[-1:]+poly[:-1],poly):
        da=(a[axis]-threshold)*sign
        db=(b[axis]-threshold)*sign
        if (da>=0)!=(db>=0):
            result.append(a.lerp(b,da/(da-db)))
        if db>=0:
            result.append(b)
    return result

for name in ("Piedra de Istria","Piedra en sombra","Relieves claros","Mármol salmón",
             "Cristal verde","Hierro patinado","Postes de amarre","Cubierta terracota"):
    mesh=s.objects[name].data
    bm=bmesh.new()
    bm.from_mesh(mesh)
    for face in list(bm.faces):
        pts=[v.co.copy() for v in face.verts]
        if any(max((p[ax]-v)*sg for p in pts)<=0 for ax,v,sg in limits):
            continue
        inside=pts
        outside=[]
        for ax,v,sg in limits:
            if not inside:
                break
            if min((p[ax]-v)*sg for p in inside)<0:
                outside.append(clip(inside,ax,v,-sg))
            inside=clip(inside,ax,v,sg)
        if len(inside)<3:
            continue
        for poly in outside:
            if len(poly)>=3:
                new=bm.faces.new([bm.verts.new(p) for p in poly])
                new.material_index=face.material_index
        bm.faces.remove(face)
    bm.to_mesh(mesh)
    bm.free()

works=[
 ("43610","Saint Roch Carried to Heaven by Angels","Giovanni Battista Tiepolo"),
 ("432","The Adoration of the Shepherds","Giorgione"),
 ("45","The Finding of Moses","Paolo Veronese"),
 ("32589","Entrance to the Grand Canal from the Molo, Venice","Canaletto"),
 ("1166","Grand Canal with the Rialto Bridge, Venice","Francesco Guardi")]
def painting(item):
    number,title,artist=item
    img=bpy.data.images.load(str(src.parent/"referencias_boveda_v22"/(number+".jpg")))
    img.pack()
    mat=bpy.data.materials.new(title)
    mat.use_nodes=True
    mat["Fuente"]="https://www.nga.gov/artworks/"+number
    mat["Autor"]=artist
    tree=mat.node_tree
    tex=tree.nodes.new("ShaderNodeTexImage")
    tex.image=img
    tree.nodes.active=tex
    p=tree.nodes.get("Principled BSDF")
    tree.links.new(tex.outputs["Color"],p.inputs["Base Color"])
    p.inputs["Roughness"].default_value=.85
    return mat,img.size[0]/img.size[1]

radius=6.70
def vault(t,y,inset=0):
    return ((radius-inset)*sin(t),y,5.05+(2.97-inset)*cos(t))
angles=[pi*(i/80-.5) for i in range(81)]
front,back=2.97,21.19
pts=[vault(t,y) for t in angles for y in (front,back)]
shell=surface("Bóveda elíptica de cañón",pts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(80)],cream)
for p in shell.data.polygons:
    p.use_smooth=True
for y in (front,back):
    surface("Luneto de cierre",[vault(t,y) for t in angles],[tuple(range(81))],cream)
for y in (3.3,4.0,20.2,20.9):
    line("Arco fajón",[vault(t,y,.05) for t in angles],.065,bronze)
    line("Filete del arco",[vault(t,y+.10,.036) for t in angles],.023,gold)

fresco,ratio=painting(works[0])
def oval(r,a,offset):
    return vault(.78*r*cos(a),12.25+(radius*.78/ratio)*r*sin(a),offset)
pts=[oval(0,0,.034)]
uv=[(.5,.5)]
faces=[]
rings,sectors=20,96
for j in range(1,rings+1):
    r=j/rings
    for i in range(sectors):
        a=2*pi*i/sectors
        pts.append(oval(r,a,.034))
        uv.append((.5+.5*r*cos(a),.5+.5*r*sin(a)))
        b=1+(j-1)*sectors+i
        c=1+(j-1)*sectors+(i+1)%sectors
        faces.append((0,c,b) if j==1 else (b-sectors,c-sectors,c,b))
panel=surface(works[0][1],pts,faces,fresco,uv=uv)
for p in panel.data.polygons:
    p.use_smooth=True
for r,depth,mat in ((1,.045,gold),(1.022,.075,cream),(1.049,.032,bronze)):
    line("Moldura del fresco",[oval(r,2*pi*i/sectors,.06) for i in range(sectors)],depth,mat,True)

wall=bpy.data.materials["Estuco de cal · tierra rosada"]
tree=wall.node_tree
coord=tree.nodes.new("ShaderNodeTexCoord")
noise=tree.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value=2.6
tree.links.new(coord.outputs["Object"],noise.inputs[0])
ramp=tree.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color=(.21,.098,.075,1)
ramp.color_ramp.elements[1].color=(.51,.32,.22,1)
tree.links.new(noise.outputs["Fac"],ramp.inputs[0])
tree.links.new(ramp.outputs[0],tree.nodes["Principled BSDF"].inputs["Base Color"])

def wash(name,pos,target,power,size):
    d=bpy.data.lights.new(name,"AREA")
    d.energy,d.size,d.color=power,size,(1,.88,.75)
    o=bpy.data.objects.new(name,d)
    architecture.objects.link(o)
    o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()

for idx,(side,y) in enumerate(((-1,7.7),(-1,16.8),(1,7.7),(1,16.8)),1):
    mat,ratio=painting(works[idx])
    h=min(2.08,3.2/ratio)
    w=h*ratio
    x=side*6.60
    def rect(y0,z0,width,height,xpos):
        return [(xpos,y0+side*a*width/2,z0+b*height/2) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    # Direction de lecture locale vers la droite pour un observateur dans la salle.
    corners=rect(y,3.39,w,h,x)
    surface(works[idx][1],corners,[(0,1,2,3)],mat,art,[(1,0),(0,0),(0,1),(1,1)])
    for extra,bevel,m in ((.05,.042,bronze),(.16,.034,gold)):
        line("Cornice de tableau",rect(y,3.39,w+extra,h+extra,x-side*.024),bevel,m,True,art)
    line("Panneau de stuc",rect(y,3.40,4.1,2.65,side*6.65),.038,cream,True)
    wash("Luz de lienzo",(side*5.42,y,4.86),(x,y,3.3),105,1.0)
for y in (6,12,18):
    for side in (-1,1):
        wash("Luz rasante de bóveda",(side*5.68,y,4.93),(side*2,y,7.7),270,2.3)

# La portada tiene su propio fotograma de referencia. El recorrido conserva
# el mismo comienzo frente a la puerta al reproducir desde el fotograma 1.
hero=s.objects["Camera_Hero"]
travel=s.objects["Camera_Recorrido"]
s.frame_start=0
s.timeline_markers.new("Portada · laguna",frame=0).camera=hero
s.timeline_markers["DoorArrival"].camera=travel
s.frame_set(244)
graph=bpy.context.evaluated_depsgraph_get()
def sight(start,end):
    v=Vector(end)-Vector(start)
    hit,_,_,_,obj,_=s.ray_cast(graph,Vector(start),v.normalized(),distance=v.length+.08)
    return obj.name if hit else None
for x,title in ((-3,"Portrait of a Young Man in Red"),(0,"The Feast of the Gods"),(3,"Rohan au Louvre")):
    target=Vector((x,21.009,3.02))
    assert sight(travel.location,target)==title,(title,sight(travel.location,target))
    ndc=world_to_camera_view(s,travel,target)
    assert 0<ndc.x<1 and 0<ndc.y<1
assert sight((0,12.25,3),oval(0,0,.034))==works[0][1]
for idx,(side,y) in enumerate(((-1,7.7),(-1,16.8),(1,7.7),(1,16.8)),1):
    assert sight((0,y,3.39),(side*6.6,y,3.39))==works[idx][1]

rows=[]
for frame,name in ((0,"Hero"),(1,"DoorArrival"),(70,"Threshold"),(150,"Lectern"),(244,"SelectedWorks")):
    s.frame_set(frame)
    cam=s.camera.evaluated_get(bpy.context.evaluated_depsgraph_get())
    matrix=cam.matrix_world
    values=[*matrix.translation,*(degrees(a) for a in matrix.to_euler("XYZ")),cam.data.lens]
    rows.append("| "+name+" | "+str(frame)+" | "+" | ".join(f"{v:.6f}" for v in values)+" |")
s.frame_set(0)
assert s.camera==hero
s.render.filepath="//museo_boveda_v22_frames/frame_"
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
notes.write_text("# Ubicaciones de cámara · v22\n\nCoordenadas mundiales de Blender. Rotación Euler XYZ en grados. "
                 "El fotograma 0 recupera Camera_Hero, la vista original de la laguna. Del 1 al 264 se usa Camera_Recorrido.\n\n"
                 "| Vista | Fotograma | X | Y | Z | Rot X | Rot Y | Rot Z | Focal (mm) |\n"
                 "|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"+"\n".join(rows)+"\n",encoding="utf-8")
