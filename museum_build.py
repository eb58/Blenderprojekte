"""Baut aus dem Original die Museumsszene um (Fenster, Tageslicht, Waende, Decke, Marmorboden).

Aufruf aus dem Nichts:  blender -b --factory-startup --python museum_build.py -- "Möbius im Museum.blend"
(führt museum_szene.py aus, falls noch keine Szene da ist). Alternativ auf das Backup anwenden statt auf eine schon umgebaute Datei.
Ohne Ausgabepfad wird die geöffnete Datei überschrieben.
"""
import bpy, math, sys, runpy, os
from mathutils import Vector, Matrix

D, S, C = bpy.data, bpy.context.scene, bpy.context
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
BODEN = "parkett"  # "parkett" oder "marmor" (Schachbrett)
if "Kusner p=7" not in D.objects: runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "museum_szene.py"))  # Szene neu erzeugen
mat = lambda n: next(m for m in D.materials if m.name == n or m.name.startswith(n + "."))  # Namen tragen in alten Dateien Suffixe (.011)


def link(o, col):
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o)

def box(name, loc, dim, col):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = C.active_object; o.name = name; o.dimensions = dim; link(o, col); return o

def arch(name, loc, r, depth, col):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=depth, location=loc, rotation=(0, math.pi / 2, 0)); o = C.active_object; o.name = name; link(o, col); return o

def join(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    C.view_layer.objects.active = objs[0]; bpy.ops.object.join(); return C.active_object


# --- Fenster in beiden Seitenwaenden -------------------------------------------------------
fcol = D.collections.new("Fenster"); S.collection.children.link(fcol)
frame = D.materials.new("Fensterrahmen"); frame.use_nodes = True
b = frame.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.06, 0.045, 0.035, 1); b.inputs["Metallic"].default_value = 0.8; b.inputs["Roughness"].default_value = 0.35

YS, W, Z0, ZA = [-7, -1, 5, 11], 3.2, 2.2, 8.4  # Fenstermitten (zwischen den Saeulen), Breite, Sohle, Bogenansatz
R = W / 2
for side, x in (("L", -16.2), ("R", 16.2)):
    cut = []
    for i, y in enumerate(YS):
        cut += [box(f"c{i}", (x, y, (Z0 + ZA) / 2), (1.4, W, ZA - Z0), fcol), arch(f"a{i}", (x, y, ZA), R, 1.4, fcol)]
        f = join([box("p", (x, y, (Z0 + ZA + R) / 2), (0.14, 0.12, ZA + R - Z0), fcol),
                  box("q1", (x, y, Z0 + 2.1), (0.14, W, 0.12), fcol), box("q2", (x, y, Z0 + 4.2), (0.14, W, 0.12), fcol), box("q3", (x, y, ZA), (0.14, W, 0.14), fcol),
                  box("l", (x, y - R + 0.06, (Z0 + ZA) / 2), (0.16, 0.14, ZA - Z0), fcol), box("r", (x, y + R - 0.06, (Z0 + ZA) / 2), (0.16, 0.14, ZA - Z0), fcol),
                  box("s", (x, y, Z0), (0.30, W, 0.14), fcol)])
        f.name = f"Fensterrahmen {side}{i + 1}"; f.data.materials.append(frame)
        bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.05, minor_radius=0.07, major_segments=48, minor_segments=8, location=(x, y, ZA), rotation=(0, math.pi / 2, 0))
        t = C.active_object; t.name = f"Fensterbogen {side}{i + 1}"; t.data.materials.append(frame); link(t, fcol)
    c = join(cut); c.name = f"Fensterschnitt {side}"; c.display_type = 'WIRE'; c.hide_render = True
    bm = D.objects["Seitenwand links" if side == "L" else "Seitenwand rechts"].modifiers.new("Fenster", "BOOLEAN")
    bm.operation, bm.object, bm.solver, bm.use_self = 'DIFFERENCE', c, 'EXACT', True  # use_self: Schnittkoerper ueberlappen sich

# --- Decke, Rueckwand hinter den Arkaden, Vorderwand -----------------------------------------
kalk = mat("Warmer Kalkstein")
for n, loc, dim in (("Decke", (0, 2, 13.45), (32.9, 38, 0.5)), ("Rueckwand hinten", (0, 20.75, 6.6), (32.9, 0.5, 13.2)), ("Vorderwand", (0, -17.25, 6.6), (32.9, 0.5, 13.2))):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = C.active_object; o.name = n; o.dimensions = dim; o.data.materials.append(kalk)

# --- Himmel: fuer die Kamera hell (Strength 1.9), als Beleuchtung gedaempft (0.7) ---------------
nt = S.world.node_tree; nt.nodes.clear()
out, bg, sky, lp, mul = (nt.nodes.new(t) for t in ("ShaderNodeOutputWorld", "ShaderNodeBackground", "ShaderNodeTexSky", "ShaderNodeLightPath", "ShaderNodeMath"))
sky.sky_type = 'MULTIPLE_SCATTERING' if 'MULTIPLE_SCATTERING' in sky.bl_rna.properties['sky_type'].enum_items else 'NISHITA'
sky.sun_disc, sky.sun_elevation, sky.sun_rotation = False, math.radians(38), math.radians(90)
mul.operation = 'MULTIPLY_ADD'; mul.inputs[1].default_value = 1.6; mul.inputs[2].default_value = 0.4
for a, b_ in ((lp.outputs["Is Camera Ray"], mul.inputs[0]), (sky.outputs[0], bg.inputs["Color"]), (mul.outputs[0], bg.inputs["Strength"]), (bg.outputs[0], out.inputs[0])): nt.links.new(a, b_)

# --- Sonne flach durch die +X-Fenster, alte Flaechenlichter dimmen ---------------------------
sun = D.objects["Sonne"]
sun.rotation_euler = Vector((-0.8, 0.22, -0.56)).normalized().to_track_quat('-Z', 'Y').to_euler(); sun.data.energy = 22; sun.data.angle = math.radians(0.6)
for o in D.objects:
    if o.type == 'LIGHT' and o.name != "Sonne": o.data.energy *= 0.35

# --- Boden: polierter Marmor mit Schachbrett oder Parkett (BODEN) ----------------------------- ---------------------------------
nt = mat("Polierter Museumsboden").node_tree; N, L = nt.nodes, nt.links; p = N["Principled BSDF"]
tc, ck, nz, mix, rr = (N.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeTexChecker", "ShaderNodeTexNoise", "ShaderNodeMix", "ShaderNodeMapRange"))
ck.inputs["Scale"].default_value = 11; ck.inputs["Color1"].default_value = (0.82, 0.76, 0.66, 1); ck.inputs["Color2"].default_value = (0.66, 0.60, 0.51, 1)
nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 12; nz.inputs["Roughness"].default_value = 0.6
mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'; mix.inputs["Factor"].default_value = 0.6
rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.06, 0.16
for a, b_ in ((tc.outputs["Generated"], ck.inputs["Vector"]), (tc.outputs["Generated"], nz.inputs["Vector"]), (ck.outputs["Color"], mix.inputs["A"]), (nz.outputs["Color"], mix.inputs["B"]),
              (mix.outputs["Result"], p.inputs["Base Color"]), (nz.outputs["Fac"], rr.inputs["Value"]), (rr.outputs["Result"], p.inputs["Roughness"])): L.new(a, b_)
p.inputs["Coat Weight"].default_value = 0.6; p.inputs["Coat Roughness"].default_value = 0.03
if BODEN == "parkett":  # Dielen im Halbverband: Brick-Textur, pro Diele leicht anderer Ton, Maserung quer zur Dielenlaenge
    bk, wv2, gm2 = (N.new(t) for t in ("ShaderNodeTexBrick", "ShaderNodeTexWave", "ShaderNodeMix"))
    bk.offset, bk.offset_frequency, bk.squash = 0.5, 2, 1.0
    for k, v in (("Scale", 30), ("Color1", (0.60, 0.38, 0.19, 1)), ("Color2", (0.42, 0.25, 0.12, 1)), ("Mortar", (0.05, 0.03, 0.02, 1)), ("Mortar Size", 0.006), ("Mortar Smooth", 0.1), ("Brick Width", 1.0), ("Row Height", 0.12)): bk.inputs[k].default_value = v
    wv2.wave_type, wv2.bands_direction = 'BANDS', 'Y'
    for k, v in (("Scale", 250), ("Distortion", 3.0), ("Detail", 3.0), ("Detail Scale", 3.0), ("Detail Roughness", 0.6)): wv2.inputs[k].default_value = v
    gm2.data_type, gm2.blend_type = 'RGBA', 'MULTIPLY'; gm2.inputs["Factor"].default_value = 0.45
    mix.inputs["Factor"].default_value = 0.25; rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.2, 0.32; p.inputs["Coat Weight"].default_value = 0.3
    for a, b_ in ((tc.outputs["Generated"], bk.inputs["Vector"]), (tc.outputs["Generated"], wv2.inputs["Vector"]), (bk.outputs["Color"], gm2.inputs["A"]), (wv2.outputs["Color"], gm2.inputs["B"]), (gm2.outputs["Result"], mix.inputs["A"])): L.new(a, b_)

# --- Skulptur: prozeduraler brauner Granit (aus BlendKit ausgelesen, siehe granit_material.json) --------
def load_nodes(nt, spec):
    if spec["interface"]:
        for i in spec["interface"]:
            s = nt.interface.new_socket(i["name"], in_out=i["in_out"], socket_type=i["socket_type"])
            for k, a in (("default", "default_value"), ("min_value", "min_value"), ("max_value", "max_value")):
                if k in i: setattr(s, a, i[k])
    nt.nodes.clear(); ns = {}
    for d in spec["nodes"]:
        n = nt.nodes.new(d["idname"]); n.name = d["name"]; n.location = d["loc"]; ns[d["name"]] = n
        for k, v in d["props"].items():
            try: setattr(n, k, v)
            except (AttributeError, TypeError, ValueError): pass
        if "group" in d: g = D.node_groups.new(d["group"]["name"], "ShaderNodeTree"); load_nodes(g, d["group"]); n.node_tree = g
        for k, v in d["in"].items():
            try: n.inputs[int(k)].default_value = v
            except (TypeError, ValueError, IndexError): pass
        if "ramp" in d:
            r = n.color_ramp; r.interpolation, r.color_mode = d["ramp"]["interp"], d["ramp"]["mode"]
            for j, (pos, col) in enumerate(d["ramp"]["els"]):
                e = r.elements[j] if j < len(r.elements) else r.elements.new(pos); e.position, e.color = pos, col
    for d in spec["nodes"]:
        if d["parent"]: ns[d["name"]].parent = ns[d["parent"]]
    for fn, fi, tn, ti in spec["links"]: nt.links.new(ns[fn].outputs[fi], ns[tn].inputs[ti])

import json
gm = D.materials.new("Procedural Brown Granite"); gm.use_nodes = True
load_nodes(gm.node_tree, json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "granit_material.json"), encoding="utf-8")))
D.objects["Kusner p=7"].material_slots[0].material = gm

# --- Weisser Marmor (Sockel der Skulptur, Statuen) ---------------------------------------------
import bmesh
mm = D.materials.new("Weisser Marmor"); mm.use_nodes = True; N, L = mm.node_tree.nodes, mm.node_tree.links; p = N["Principled BSDF"]
tc, mp, wv, ramp = N.new("ShaderNodeTexCoord"), N.new("ShaderNodeMapping"), N.new("ShaderNodeTexWave"), N.new("ShaderNodeValToRGB")
mp.inputs["Scale"].default_value = (0.5, 0.5, 0.5); wv.wave_type, wv.bands_direction = 'BANDS', 'DIAGONAL'
for k, v in (("Scale", 0.9), ("Distortion", 6.0), ("Detail", 8.0), ("Detail Scale", 1.2), ("Detail Roughness", 0.65)): wv.inputs[k].default_value = v
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, (0.55, 0.52, 0.49, 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.035, (0.88, 0.86, 0.81, 1)
e = ramp.color_ramp.elements.new(0.965); e.color = (0.88, 0.86, 0.81, 1); e = ramp.color_ramp.elements.new(1.0); e.color = (0.55, 0.52, 0.49, 1)
p.inputs["Roughness"].default_value = 0.18; p.inputs["Coat Weight"].default_value = 0.25
for a, b_ in ((tc.outputs["Object"], mp.inputs["Vector"]), (mp.outputs["Vector"], wv.inputs["Vector"]), (wv.outputs["Color"], ramp.inputs["Fac"]), (ramp.outputs["Color"], p.inputs["Base Color"])): L.new(a, b_)
for n in ("Sockel unten", "Sockel oben"): D.objects[n].material_slots[0].material = mm

# --- Statuen in den Arkadennischen: Drehprofil (Gewand, Rumpf, Kopf) + Arme, auf Marmorsockel ---
scol = D.collections.new("Statuen"); S.collection.children.link(scol)
PROFIL = [(0, 0), (.34, 0), (.36, .05), (.31, .5), (.27, .9), (.21, 1.15), (.24, 1.3), (.26, 1.42), (.27, 1.5), (.13, 1.58), (.075, 1.62), (.085, 1.67), (.11, 1.75), (.09, 1.84), (0, 1.87)]
def statue(i, x, y, h, arm_up):
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in PROFIL]; es = [bm.edges.new((vs[j], vs[j + 1])) for j in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=32, use_merge=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for j, (sx, up) in enumerate(((-1, False), (1, arm_up))):  # Arme als schlanke Kegel, einer erhoben
        a = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.06, radius2=0.04, depth=0.75, matrix=Matrix.Translation((0, 0, -0.375)))
        rot = Matrix.Rotation(math.radians(sx * (150 if up else 18)), 4, 'Y')
        bmesh.ops.transform(bm, verts=a["verts"], matrix=Matrix.Translation((sx * 0.29, 0, 1.47)) @ rot)
    me = D.meshes.new(f"Statue {i}"); bm.to_mesh(me); bm.free()
    o = D.objects.new(f"Statue {i}", me); scol.objects.link(o); o.location = (x, y, h); o.scale = (1.5, 1.5, 1.5); o.rotation_euler.z = math.radians((-1) ** i * 12)
    for pl in me.polygons: pl.use_smooth = True
    sm = o.modifiers.new("Glatt", "SUBSURF"); sm.levels = sm.render_levels = 1; me.materials.append(mm)
    sk = box(f"Statuensockel {i}", (x, y, h / 2), (1.5, 1.5, h), scol); sk.data.materials.append(mm)
    sp = D.lights.new(f"Statuenlicht {i}", "SPOT"); sp.energy, sp.spot_size, sp.spot_blend, sp.color, sp.shadow_soft_size = 900, math.radians(38), 0.6, (1.0, 0.86, 0.68), 0.3
    so = D.objects.new(f"Statuenlicht {i}", sp); scol.objects.link(so); so.location = (x, y - 4.5, 8.5); so.rotation_euler = (Vector((0, 4.5, -8.5 + h + 1.4)).to_track_quat('-Z', 'Y')).to_euler()
    kp = box(f"Statuensockel Deckplatte {i}", (x, y, h + 0.06), (1.7, 1.7, 0.12), scol); kp.data.materials.append(mm)
for i, x in enumerate((-9, -3, 3, 9)):
    statue(i, x, 18.2, 1.1, arm_up=i % 2 == 0)
    al = D.lights.new(f"Nischenlicht {i}", "AREA"); al.energy, al.size, al.color = 350, 2.5, (1.0, 0.85, 0.66)
    ao = D.objects.new(f"Nischenlicht {i}", al); scol.objects.link(ao); ao.location = (x, 18.0, 9.5)  # zeigt nach unten (Standard)
mat("Tiefe Arkadennischen").node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.4, 0.3, 1)  # vorher fast schwarz

# --- Echte Marmorbueste (Poly Haven "Marble Bust 01", CC0) statt der Platzhalter-Figuren -------------
BUSTE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Modelle", "marble_bust_01")
if os.path.exists(os.path.join(BUSTE, "marble_bust_01.blend")):
    with D.libraries.load(os.path.join(BUSTE, "marble_bust_01.blend"), link=False) as (src, dst): dst.objects = list(src.objects)
    for im in D.images:
        if "marble_bust_01" in im.name: im.filepath = os.path.join(BUSTE, "textures", os.path.basename(im.filepath)); im.reload()
    base = dst.objects[0]; BS = 3.4; zmin = min(v[2] for v in base.bound_box) * BS
    for i, x in enumerate((-9, -3, 3, 9)):
        D.objects.remove(D.objects[f"Statue {i}"])
        o = base if i == 0 else base.copy(); scol.objects.link(o)
        o.scale = (BS,) * 3; o.location = (x, 18.2, 1.1 + 0.12 - zmin); o.rotation_euler = (0, 0, math.radians((-1) ** i * 9))

# --- Kassettendecke: Balkenraster unter der Decke, kleiner Rahmen in jedem Feld, Oberlicht in der Mitte --------
ccol = D.collections.new("Kassettendecke"); S.collection.children.link(ccol)
NX, NY, X0, Y0, DX, DY, ZD = 10, 10, -16.45, -17.0, 3.29, 3.8, 13.2  # Felder, Ursprung, Feldgroesse, Unterkante der Decke
bm = bmesh.new()
def bx(c, sz): bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*sz, 1)))
for i in range(NX + 1): bx((X0 + i * DX, Y0 + NY * DY / 2, ZD - 0.2), (0.32, NY * DY, 0.4))   # Balken laengs
for j in range(NY + 1): bx((0, Y0 + j * DY, ZD - 0.2), (NX * DX, 0.32, 0.4))                   # Balken quer
SKY = {(i, j) for i in (4, 5) for j in (4, 5)}                                                  # Felder des Oberlichts
for i in range(NX):
    for j in range(NY):
        if (i, j) in SKY: continue
        cx, cy = X0 + (i + .5) * DX, Y0 + (j + .5) * DY; fx, fy = DX - 1.1, DY - 1.1
        for dx, dy, sx, sy in ((0, fy / 2, fx, .12), (0, -fy / 2, fx, .12), (fx / 2, 0, .12, fy), (-fx / 2, 0, .12, fy)): bx((cx + dx, cy + dy, ZD - 0.075), (sx, sy, 0.15))
        bx((cx, cy, ZD - 0.05), (0.5, 0.5, 0.1))
me = D.meshes.new("Kassettendecke"); bm.to_mesh(me); bm.free(); ko = D.objects.new("Kassettendecke", me); ccol.objects.link(ko); me.materials.append(mat("Heller Naturstein"))
sw, sh = 2 * DX - 0.32, 2 * DY - 0.32
bpy.ops.mesh.primitive_plane_add(size=1, location=(X0 + 5 * DX, Y0 + 5 * DY, ZD - 0.02), rotation=(math.pi, 0, 0)); sk = C.active_object; sk.name = "Oberlicht"; sk.scale = (sw, sh, 1); link(sk, ccol)
om = D.materials.new("Oberlicht"); om.use_nodes = True; onm = om.node_tree; onm.nodes.clear(); em, oo = onm.nodes.new("ShaderNodeEmission"), onm.nodes.new("ShaderNodeOutputMaterial")
em.inputs["Color"].default_value, em.inputs["Strength"].default_value = (1.0, 0.94, 0.82, 1), 7.0; onm.links.new(em.outputs[0], oo.inputs[0]); sk.data.materials.append(om)

# --- Wellenbank: ~70 Nussholz-Lamellen, Sitz und Lehne schwingen als Welle; Messing-Klingenbeine -----------
bcol = D.collections.new("Bank"); S.collection.children.link(bcol)
def profil(hoehe):  # Querschnitt (y, z): flacher Sitz, sanft in die Lehne aufgebogen; hoehe skaliert die Lehne
    pts = [(-0.28 + 0.4 * u / 6, 0.0) for u in range(7)]
    for k in range(1, 10): t = k / 9; pts.append(((1 - t) ** 2 * 0.12 + 2 * t * (1 - t) * 0.33 + t * t * 0.36, (t * t * 0.52) * hoehe))
    return pts
def streifen(bm, pts, x0, x1, z0, d=0.02):
    ring = []
    for k, (y, z) in enumerate(pts):  # Normale des Querschnitts -> oben/unten Kante
        a, b = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]; ty, tz = b[0] - a[0], b[1] - a[1]; n = math.hypot(ty, tz) or 1; ny, nz = -tz / n, ty / n
        ring.append(((y + ny * d, z0 + z + nz * d), (y - ny * d, z0 + z - nz * d)))
    for x in (x0, x1): pass
    o = [[bm.verts.new((x, *r[0])) for r in ring] for x in (x0, x1)]; u = [[bm.verts.new((x, *r[1])) for r in ring] for x in (x0, x1)]
    for k in range(len(pts) - 1):
        bm.faces.new((o[0][k], o[0][k + 1], o[1][k + 1], o[1][k])); bm.faces.new((u[0][k], u[1][k], u[1][k + 1], u[0][k + 1]))
    for i in (0, 1): bm.faces.new(o[i] + u[i][::-1])
    bm.faces.new((o[0][0], o[1][0], u[1][0], u[0][0])); bm.faces.new((o[0][-1], u[0][-1], u[1][-1], o[1][-1]))
BL, NS = 3.2, 72; bm = bmesh.new()
for i in range(NS):
    x = -BL / 2 + (i + .5) * BL / NS; w = math.sin(2 * math.pi * 1.5 * x / BL)
    streifen(bm, profil(1.0 + 0.4 * w), x - 0.018, x + 0.018, 0.44 + 0.06 * w)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
wme = D.meshes.new("Bank Holz"); bm.to_mesh(wme); bm.free()
bm = bmesh.new()
for x in (-1.1, 1.1): bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((x, -0.05, 0.19)) @ Matrix.Diagonal((0.035, 0.42, 0.38, 1)))
bme = D.meshes.new("Bank Messing"); bm.to_mesh(bme); bm.free()
wood = D.materials.new("Nussholz"); wood.use_nodes = True; wn = wood.node_tree; wp = wn.nodes["Principled BSDF"]
wt, wm, ww, wr = wn.nodes.new("ShaderNodeTexCoord"), wn.nodes.new("ShaderNodeMapping"), wn.nodes.new("ShaderNodeTexWave"), wn.nodes.new("ShaderNodeValToRGB")
wm.inputs["Scale"].default_value = (1, 40, 40); ww.wave_type, ww.bands_direction = 'BANDS', 'Y'; ww.inputs["Scale"].default_value = 3; ww.inputs["Distortion"].default_value = 5; ww.inputs["Detail"].default_value = 4
wr.color_ramp.elements[0].color, wr.color_ramp.elements[1].color = (0.11, 0.055, 0.025, 1), (0.30, 0.16, 0.07, 1)
for a, b_ in ((wt.outputs["Object"], wm.inputs["Vector"]), (wm.outputs["Vector"], ww.inputs["Vector"]), (ww.outputs["Color"], wr.inputs["Fac"]), (wr.outputs["Color"], wp.inputs["Base Color"])): wn.links.new(a, b_)
wp.inputs["Roughness"].default_value = 0.32; wp.inputs["Coat Weight"].default_value = 0.4
brass = D.materials.new("Messing"); brass.use_nodes = True; bp = brass.node_tree.nodes["Principled BSDF"]
bp.inputs["Base Color"].default_value = (0.85, 0.62, 0.25, 1); bp.inputs["Metallic"].default_value = 1.0; bp.inputs["Roughness"].default_value = 0.18
wme.materials.append(wood); bme.materials.append(brass)
for n, (bx_, by_, rot) in enumerate(((11.6, -2.5, -90), (-11.6, 5.0, 90))):  # Ruecken zur Wand, Blick zur Skulptur
    for me_, nm in ((wme, "Holz"), (bme, "Messing")):
        o = D.objects.new(f"Wellenbank {n + 1} {nm}", me_); bcol.objects.link(o); o.location = (bx_, by_, 0); o.rotation_euler.z = math.radians(rot)
        for pl in o.data.polygons: pl.use_smooth = False

# --- Besucher: stilisierte Figuren aus Grundformen (Beine, Rumpf, Arme, Kopf, Haare), einer sitzt auf der Bank ------
vcol = D.collections.new("Besucher"); S.collection.children.link(vcol)
def flat(name, c, rough=0.75):
    m = D.materials.new(name); m.use_nodes = True; pb = m.node_tree.nodes["Principled BSDF"]; pb.inputs["Base Color"].default_value = (*c, 1); pb.inputs["Roughness"].default_value = rough; return m
def limb(bm, p0, p1, r0, r1, sx=1.0, sy=1.0):  # Kegelstumpf von p0 nach p1
    a, b = Vector(p0), Vector(p1); d = b - a; up = 'X' if abs(d.normalized().x) < 0.9 else 'Y'
    bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r0, radius2=r1, depth=d.length, matrix=Matrix.Translation((a + b) / 2) @ d.to_track_quat('Z', up).to_matrix().to_4x4() @ Matrix.Diagonal((sx, sy, 1, 1)))
def ball(bm, c, r, sx=1, sy=1, sz=1): bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r, matrix=Matrix.Translation(c) @ Matrix.Diagonal((sx, sy, sz, 1)))
def person(name, pos, ziel, sitzend, oben, hose, haut, haar, scale=1.0, rot=None):
    g = {k: bmesh.new() for k in ("oben", "hose", "haut", "haar", "schuh")}
    for sx in (-1, 1):
        if sitzend:
            limb(g["hose"], (sx * .09, .05, .48), (sx * .10, -.42, .46), .085, .065); limb(g["hose"], (sx * .10, -.42, .46), (sx * .10, -.44, .08), .06, .05); limb(g["schuh"], (sx * .10, -.42, .05), (sx * .10, -.58, .05), .05, .045)
            ball(g["oben"], (sx * .2, .08, 1.0), .06); limb(g["oben"], (sx * .2, .08, 1.0), (sx * .22, -.02, .75), .05, .042); limb(g["oben"], (sx * .22, -.02, .75), (sx * .14, -.28, .58), .042, .036); ball(g["haut"], (sx * .14, -.30, .57), .04)
        else:
            limb(g["hose"], (sx * .09, 0, .9), (sx * .09, 0, .08), .075, .055); limb(g["schuh"], (sx * .09, .02, .05), (sx * .09, -.13, .05), .05, .045)
            ball(g["oben"], (sx * .2, 0, 1.42), .06); limb(g["oben"], (sx * .21, 0, 1.42), (sx * .24, -.05, .78), .05, .04); ball(g["haut"], (sx * .24, -.05, .74), .045)
    if sitzend:
        limb(g["hose"], (0, 0, .48), (0, 0.03, .55), .17, .16, 1, .72); limb(g["oben"], (0, .03, .5), (0, .08, 1.05), .17, .16, 1, .72); limb(g["haut"], (0, .08, 1.05), (0, .05, 1.14), .05, .045); ball(g["haut"], (0, .04, 1.25), .105, .9, 1, 1.1); ball(g["haar"], (0, .07, 1.29), .108, .92, 1, .9)
    else:
        limb(g["hose"], (0, 0, .85), (0, 0, .95), .17, .17, 1, .72); limb(g["oben"], (0, 0, .9), (0, 0, 1.45), .16, .17, 1, .72); limb(g["haut"], (0, 0, 1.45), (0, -.01, 1.56), .05, .045); ball(g["haut"], (0, -.01, 1.67), .105, .9, 1, 1.1); ball(g["haar"], (0, .02, 1.71), .108, .92, 1, .9)
    z = math.atan2(ziel[0] - pos[0], -(ziel[1] - pos[1])) if rot is None else math.radians(rot)
    for k, c in (("oben", oben), ("hose", hose), ("haut", haut), ("haar", haar), ("schuh", (0.03, 0.025, 0.02))):
        bmesh.ops.recalc_face_normals(g[k], faces=g[k].faces); me_ = D.meshes.new(f"{name} {k}"); g[k].to_mesh(me_); g[k].free(); me_.materials.append(flat(f"{name} {k}", c))
        o = D.objects.new(f"{name} {k}", me_); vcol.objects.link(o); o.location, o.rotation_euler.z, o.scale = (*pos, 0), z, (scale,) * 3
        for pl in me_.polygons: pl.use_smooth = True
SKIN, SKIN2 = (0.72, 0.52, 0.40), (0.55, 0.38, 0.28)
person("Besucher Bank", (-11.54, 4.467), None, True, (0.12, 0.42, 0.45), (0.06, 0.06, 0.08), SKIN, (0.35, 0.22, 0.12), rot=90)  # sitzt im Wellental der linken Bank
person("Besucher 1", (4.6, -5.2), (0, 0), False, (0.07, 0.10, 0.22), (0.45, 0.38, 0.28), SKIN, (0.10, 0.08, 0.07), 1.03)
person("Besucher 2", (-6.4, -4.0), (0, 0), False, (0.55, 0.12, 0.10), (0.05, 0.05, 0.06), SKIN2, (0.05, 0.04, 0.03), 0.96)
person("Besucher 3", (6.8, 4.6), (0, 0), False, (0.55, 0.55, 0.52), (0.12, 0.18, 0.32), SKIN, (0.55, 0.42, 0.22), 0.98)

# --- Sonnenstrahlen: pro Fenster der Sonnenseite ein Lichtschacht (Volumen-Quader entlang der Sonnenrichtung) -------
vm = D.materials.new("Dunst"); vm.use_nodes = True; nt_ = vm.node_tree; nt_.nodes.clear()
pv, vo = nt_.nodes.new("ShaderNodeVolumePrincipled"), nt_.nodes.new("ShaderNodeOutputMaterial")
pv.inputs["Density"].default_value, pv.inputs["Anisotropy"].default_value = 0.12, 0.6
nt_.links.new(pv.outputs["Volume"], vo.inputs["Volume"])
SUNDIR = Vector((-0.8, 0.22, -0.56)).normalized(); LEN = 10.0
for i, y in enumerate(YS):
    o = box(f"Lichtschacht {i + 1}", Vector((16.0, y, (Z0 + ZA) / 2)) + SUNDIR * LEN / 2, (LEN, W - 0.3, ZA - Z0 - 0.3), fcol)
    o.rotation_euler = SUNDIR.to_track_quat('X', 'Z').to_euler(); o.data.materials.append(vm); o.visible_shadow = False; o.display_type = 'WIRE'
S.cycles.volume_bounces = 0

# --- Kamera naeher, Flaeche weich unterteilt (bisher von Hand bzw. per Einzeiler gesetzt) ---
cam = D.objects["Museumskamera"]; cam.location.y = -11.8; cam.data.lens = 35
k = D.objects["Kusner p=7"]
if not any(m.type == 'SUBSURF' for m in k.modifiers): sm = k.modifiers.new("Subdivision", "SUBSURF"); sm.levels, sm.render_levels = 1, 2

bpy.ops.wm.save_as_mainfile(filepath=OUT) if OUT else bpy.ops.wm.save_mainfile()
