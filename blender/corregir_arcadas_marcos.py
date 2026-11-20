"""Reparar los encuentros de las arquerías y enmarcar los siete lienzos de v22."""
from pathlib import Path
from math import cos, sin, pi, sqrt
import bpy
import bmesh
from mathutils import Vector, geometry

scene = bpy.context.scene
source = Path(bpy.data.filepath)
assert source.name == "museo_portada_v22_boveda.blend"
output = source.with_name("museo_portada_v23_arcadas_marcos.blend")
if output.exists():
    raise FileExistsError(output)
group = bpy.data.collections.new("Fachada · encuentros de cantería")
scene.collection.children.link(group)
art = bpy.data.collections["Obras temporales · ocultar al instalar proyectos"]
stone, trim = [bpy.data.materials[k] for k in ("Piedra de Istria","Relieves claros")]
bronze, gold = [bpy.data.materials[k] for k in ("Bronce cepillado","Filete · latón satinado")]

def mesh_object(name, points, faces, indices, materials, collection):
    data = bpy.data.meshes.new(name)
    data.from_pydata(points,[],faces)
    for mat in materials:
        data.materials.append(mat)
    for p,slot in zip(data.polygons,indices):
        p.material_index=slot
    data.update()
    bm=bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000003)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj=bpy.data.objects.new(name,data)
    collection.objects.link(obj)
    return obj

corners=((24,0),(-24,0),(-24,14))
levels=((1.04,3.74,5.43),(5.75,7.60,9.36))
for name in ("Piedra de Istria","Relieves claros","Piedra en sombra"):
    data=scene.objects[name].data
    bm=bmesh.new()
    bm.from_mesh(data)
    obsolete=[]
    for f in bm.faces:
        pts=[v.co for v in f.verts]
        lo,hi=[tuple(fn(p[i] for p in pts) for i in range(3)) for fn in (min,max)]
        front=lo[0]>-24.65 and hi[0]<24.65 and lo[1]>-.65 and hi[1]<.84
        side=lo[1]>-.65 and hi[1]<14.65 and lo[0]>-24.65 and hi[0]<-23.16
        if not (front or side):
            continue
        for bottom,spring,top in levels:
            # Las losas continuas quedan fuera de la selección.
            if lo[2]>=spring-.001 and hi[2]>spring+.001 and hi[2]<=top+.125 and hi[0]-lo[0]<3.2 and hi[1]-lo[1]<3.2:
                obsolete.append(f)
                break
            if lo[2]>=bottom-.001 and hi[2]<=spring+.001 and any(
                    all((p.x-x)**2+(p.y-y)**2<.59**2 for p in pts) for x,y in corners):
                obsolete.append(f)
                break
    assert obsolete,name
    bmesh.ops.delete(bm,geom=obsolete,context="FACES")
    bm.to_mesh(data)
    bm.free()

for obj in list(scene.objects):
    if obj.name.startswith(("Basa de esquina","Capitel de esquina","Remate de esquina","Fuste de esquina")):
        bpy.data.objects.remove(obj,do_unlink=True)

for x,y in corners:
    for bottom,spring,top in levels:
        w=.42 if bottom<2 else .225
        profile=[(bottom,w*1.30),(bottom+.13,w*1.30),(bottom+.20,w),
                 (spring-.31,w),(spring-.26,w*1.09),(spring-.085,w*1.36),(spring,w*1.36)]
        verts=[(x+a*r,y+b*r,z) for z,r in profile for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
        faces=[(3,2,1,0)]
        for k in range(len(profile)-1):
            for j in range(4):
                i=k*4+j
                n=k*4+(j+1)%4
                faces.append((i,n,n+4,i+4))
        faces.append(tuple(range(len(verts)-4,len(verts))))
        mesh_object("Machón de esquina · piedra continua",verts,faces,
                    [0]+[int(i//4 in (0,4,5)) for i in range(len(faces)-2)]+[1],(stone,trim),group)

def arcade(side, bay, pitch, spring, ceiling, height, upper, last):
    half=pitch/2
    radius=half-(.13 if upper else .21)
    rim=.065 if upper else .11
    front,back=(-.125,.15) if upper else (-.18,.225)
    def point(xz,d):
        x,z=xz
        u=(bay+.5)*pitch+x
        if bay==0:  # Encuentro ingletado de frente y retorno
            u+=d*(1-u/pitch)
        return (-24+d,u,z) if side else (-24+u,d,z)

    def profile(r,h):
        return [(t*r,spring+h*sqrt(max(0,1-((abs(t)+.35)/1.35)**2))/.966)
                for t in (i/20 for i in range(-20,21))]
    inner,outer=profile(radius,height),profile(radius+rim,height+rim)
    border=[(-half,spring),*outer,(half,spring),(half,ceiling),(-half,ceiling)]
    rings=[]
    if upper:
        for rad in (.312,.226):
            rings.append([(rad*cos(a)*(1+.13*cos(4*a)),9.003+rad*sin(a)*(1+.13*cos(4*a)))
                          for a in (i*pi/40 for i in range(80))])
    contours=[border]+rings[:1]
    vertices=[]
    paths=[]
    for loop in contours:
        paths.append(list(range(len(vertices),len(vertices)+len(loop))))
        vertices.extend(map(Vector,loop))
    coords,_,tris,_,_,owners=geometry.delaunay_2d_cdt(vertices,[],paths,1,1e-7,True)
    verts=[]; faces=[]; slots=[]
    def face(poly,slot=0):
        faces.append(tuple(range(len(verts),len(verts)+len(poly))))
        verts.extend(poly)
        slots.append(slot)
    for d in (front,back):
        for tri,inside in zip(tris,owners):
            if 0 in inside and 1 not in inside:
                face([point(coords[i],d) for i in tri])
        for i in range(40):
            face([point(p,d) for p in (inner[i],inner[i+1],outer[i+1],outer[i])],1)
        if rings:
            for i in range(80):
                j=(i+1)%80
                face([point(p,d) for p in (rings[0][i],rings[0][j],rings[1][j],rings[1][i])],1)
    def reveal(a,b,slot):
        face([point(a,front),point(b,front),point(b,back),point(a,back)],slot)
    # Los perfiles exterior e interior terminan a diferentes distancias del pilar.
    for a,b in zip(inner,inner[1:]):
        reveal(a,b,0)
    for a,b in ((-half,-radius-rim),(-radius-rim,-radius),(radius,radius+rim),(radius+rim,half)):
        reveal((a,spring),(b,spring),0)
    if last:
        reveal((half,spring),(half,ceiling),0)
    if rings:
        for a,b in zip(rings[1],rings[1][1:]+rings[1][:1]):
            reveal(a,b,1)
    return mesh_object("Tracería calada" if upper else "Arco de piedra",verts,faces,slots,(stone,trim),group)

for side in (False,True):
    for upper in (False,True):
        n=(10 if upper else 5) if side else (32 if upper else 16)
        for i in range(n):
            arcade(side,i,(14 if side else 48)/n,7.6 if upper else 3.74,
                   9.36 if upper else 5.43,.945 if upper else 1.52,upper,i==n-1)

# La abertura del marco se deriva del cuadrilátero del lienzo ya mapeado.
for o in list(scene.objects):
    if o.name.startswith(("Marco ·","Filete interior","Fondo de exposición","Cornice de tableau","Panneau de stuc")):
        bpy.data.objects.remove(o,do_unlink=True)
paintings=[o for o in art.objects if o.type=="MESH" and len(o.data.vertices)==4]
assert len(paintings)==7
for o in paintings:
    pts=[o.matrix_world@v.co for v in o.data.vertices]
    center=sum(pts,Vector())/4
    n=Vector((0,-1,0)) if center.y>20 else Vector((-1 if center.x>0 else 1,0,0))
    up=Vector((0,0,1))
    across=up.cross(n)
    w=max(abs((p-center).dot(across)) for p in pts)
    h=max(abs(p.z-center.z) for p in pts)
    profile=[(-.002,.004),(.009,.022),(.021,.016),(.041,.030),(.055,.030),(.061,.013),(.061,-.025),(-.002,-.025)]
    verts=[center+across*(a*(w+r))+up*(b*(h+r))+n*d for r,d in profile for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
    faces=[]; slots=[]
    for k in range(len(profile)):
        for j in range(4):
            kk=(k+1)%len(profile); jj=(j+1)%4
            faces.append((k*4+j,k*4+jj,kk*4+jj,kk*4+j))
            slots.append(int(k in (0,3)))
    mesh_object("Marco a medida · "+o.name,verts,faces,slots,(bronze,gold),art)

# Comprobar los cuatro lóbulos de cada perforación, radios del capitel y
# distancias reales de apoyo. Rayos en el plano del frente y del retorno.
graph=bpy.context.evaluated_depsgraph_get()
def trace(start,delta):
    d=Vector(delta)
    hit,_,_,_,obj,_=scene.ray_cast(graph,Vector(start),d.normalized(),distance=d.length)
    return obj.name if hit else None
for side,count,pitch in ((False,32,1.5),(True,10,1.4)):
    for i in range(count):
        mid=(i+.5)*pitch
        for dx,dz in ((0,0),(.13,0),(-.13,0),(0,.13),(0,-.13)):
            p=(-24-.30,mid+dx,9.003+dz) if side else (-24+mid+dx,-.30,9.003+dz)
            assert trace(p,(.5,0,0) if side else (0,.5,0)) is None,(side,i,p)
for o in paintings:
    c=sum((o.matrix_world@v.co for v in o.data.vertices),Vector())/4
    n=Vector((0,-1,0)) if c.y>20 else Vector((-1 if c.x>0 else 1,0,0))
    assert trace(c+n*.25,-n*.31)==o.name,o.name
scene.frame_set(0)
assert scene.camera.name=="Camera_Hero"
bpy.ops.wm.save_as_mainfile(filepath=str(output))
print("Vanos calados comprobados: 42. Marcos ajustados: 7.")
