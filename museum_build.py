"""Baut aus dem Original die Museumsszene um (Fenster, Tageslicht, Waende, Decke, Marmorboden).

Aufruf aus dem Nichts:  blender -b --factory-startup --python museum_build.py -- "Möbius im Museum.blend"
(führt museum_szene.py aus, falls noch keine Szene da ist). Alternativ auf das Backup anwenden statt auf eine schon umgebaute Datei.
Ohne Ausgabepfad wird die geöffnete Datei überschrieben.
"""
import bpy, math, sys, runpy, os
from mathutils import Vector

D, S, C = bpy.data, bpy.context.scene, bpy.context
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
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
mul.operation = 'MULTIPLY_ADD'; mul.inputs[1].default_value = 1.2; mul.inputs[2].default_value = 0.7
for a, b_ in ((lp.outputs["Is Camera Ray"], mul.inputs[0]), (sky.outputs[0], bg.inputs["Color"]), (mul.outputs[0], bg.inputs["Strength"]), (bg.outputs[0], out.inputs[0])): nt.links.new(a, b_)

# --- Sonne flach durch die +X-Fenster, alte Flaechenlichter dimmen ---------------------------
sun = D.objects["Sonne"]
sun.rotation_euler = Vector((-0.8, 0.22, -0.56)).normalized().to_track_quat('-Z', 'Y').to_euler(); sun.data.energy = 12; sun.data.angle = math.radians(0.6)
for o in D.objects:
    if o.type == 'LIGHT' and o.name != "Sonne": o.data.energy *= 0.35

# --- Boden: polierter Marmor mit Schachbrett und Maserung ---------------------------------
nt = mat("Polierter Museumsboden").node_tree; N, L = nt.nodes, nt.links; p = N["Principled BSDF"]
tc, ck, nz, mix, rr = (N.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeTexChecker", "ShaderNodeTexNoise", "ShaderNodeMix", "ShaderNodeMapRange"))
ck.inputs["Scale"].default_value = 11; ck.inputs["Color1"].default_value = (0.78, 0.70, 0.58, 1); ck.inputs["Color2"].default_value = (0.36, 0.30, 0.25, 1)
nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 12; nz.inputs["Roughness"].default_value = 0.6
mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'; mix.inputs["Factor"].default_value = 0.35
rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.06, 0.16
for a, b_ in ((tc.outputs["Generated"], ck.inputs["Vector"]), (tc.outputs["Generated"], nz.inputs["Vector"]), (ck.outputs["Color"], mix.inputs["A"]), (nz.outputs["Color"], mix.inputs["B"]),
              (mix.outputs["Result"], p.inputs["Base Color"]), (nz.outputs["Fac"], rr.inputs["Value"]), (rr.outputs["Result"], p.inputs["Roughness"])): L.new(a, b_)
p.inputs["Coat Weight"].default_value = 0.6; p.inputs["Coat Roughness"].default_value = 0.03

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

# --- Kamera naeher, Flaeche weich unterteilt (bisher von Hand bzw. per Einzeiler gesetzt) ---
cam = D.objects["Museumskamera"]; cam.location.y = -11.8; cam.data.lens = 35
k = D.objects["Kusner p=7"]
if not any(m.type == 'SUBSURF' for m in k.modifiers): sm = k.modifiers.new("Subdivision", "SUBSURF"); sm.levels, sm.render_levels = 1, 2

bpy.ops.wm.save_as_mainfile(filepath=OUT) if OUT else bpy.ops.wm.save_mainfile()
