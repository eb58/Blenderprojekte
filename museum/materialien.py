"""Materialien des Museums: Naturstein, Granit, Holz, Leder, Metall, Glas und Licht."""
import json
import math
import os

import bpy

from einstellungen import PROJECT_DIR

D = bpy.data
GRANIT_DATEI = os.path.join(PROJECT_DIR, "assets", "materialien", "granit.json")


def set_socket(node, names, value):
    names = (names,) if isinstance(names, str) else names
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return socket
    return None


def simple_material(name, color, roughness, metallic=0.0):
    material = D.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    set_socket(shader, "Base Color", color)
    set_socket(shader, "Roughness", roughness)
    set_socket(shader, "Metallic", metallic)
    return material


def emissive_material(name, color, strength):
    """Warm leuchtende Fläche (Lichtkante); strahlt auch in Echtzeitansichten (glTF-Emission)."""
    material = D.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    set_socket(bsdf, "Base Color", color)
    set_socket(bsdf, "Emission Color", color)
    set_socket(bsdf, "Emission Strength", strength)
    return material


def emission_material(name, color, strength):
    """Reine Lichtfläche ohne Oberflächenshader (Oberlicht)."""
    material = D.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emission, output = tree.nodes.new("ShaderNodeEmission"), tree.nodes.new("ShaderNodeOutputMaterial")
    emission.inputs["Color"].default_value, emission.inputs["Strength"].default_value = color, strength
    tree.links.new(emission.outputs[0], output.inputs[0])
    return material


def ashlar_material(name, light, dark, mortar, block_width=1.8, block_height=0.6):
    """Quadermauerwerk (Naturstein): Fugen und leichte Farbvariation; die Wandkoordinaten (x, z) steuern das Muster."""
    material = D.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    position = nodes.new("ShaderNodeNewGeometry")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    combine = nodes.new("ShaderNodeCombineXYZ")
    links.new(position.outputs["Position"], separate.inputs["Vector"])
    links.new(separate.outputs["X"], combine.inputs["X"])
    links.new(separate.outputs["Z"], combine.inputs["Y"])
    brick = nodes.new("ShaderNodeTexBrick")
    brick.offset, brick.squash = 0.5, 1.0
    for key, value in (("Brick Width", block_width), ("Row Height", block_height), ("Mortar Size", 0.005),
                       ("Mortar Smooth", 0.6), ("Scale", 1.0)):
        brick.inputs[key].default_value = value
    brick.inputs["Color1"].default_value = light
    brick.inputs["Color2"].default_value = dark
    brick.inputs["Mortar"].default_value = mortar
    links.new(combine.outputs["Vector"], brick.inputs["Vector"])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.5
    noise.inputs["Detail"].default_value = 7.0
    links.new(position.outputs["Position"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.3, 0.7
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = (0.78, 0.78, 0.78, 1), (1, 1, 1, 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    tint = nodes.new("ShaderNodeMix")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    links.new(brick.outputs["Color"], tint.inputs["A"])
    links.new(ramp.outputs["Color"], tint.inputs["B"])
    links.new(tint.outputs["Result"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2
    bump.inputs["Distance"].default_value = 0.02
    links.new(brick.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.78
    # Grundfarbe als Rückfall (z. B. glTF-Export für die 3D-Vorschau kennt das Fugenmuster nicht).
    bsdf.inputs["Base Color"].default_value = light
    return material


# --- Prozeduraler Naturgranit der Skulpturen (Node-Baum aus assets/materialien/granit.json) -
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


# Naturstein bleibt auch in verschachtelten Node-Gruppen nichtmetallisch.
def make_nonmetallic(node_tree):
    for node in node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs["Metallic"].default_value = 0.0
            for incoming in list(node.inputs["Metallic"].links):
                node_tree.links.remove(incoming)
        elif node.type == 'GROUP' and node.node_tree is not None:
            make_nonmetallic(node.node_tree)


def granit():
    granite = D.materials.new("Polierter dunkler Naturgranit")
    granite.use_nodes = True
    with open(GRANIT_DATEI, encoding="utf-8") as datei:
        load_nodes(granite.node_tree, json.load(datei))
    make_nonmetallic(granite.node_tree)
    return granite


def elfenbein_kalkstein():
    """Ruhiger, geschliffener Kalkstein für die Sockel. Er hebt die dunklen
    Granitflächen ab, ohne mit starken Marmoradern zu konkurrieren."""
    plinth_stone = D.materials.new("Geschliffener Elfenbein-Kalkstein")
    plinth_stone.use_nodes = True
    pn, pl = plinth_stone.node_tree.nodes, plinth_stone.node_tree.links
    pbsdf = pn["Principled BSDF"]
    ptc = pn.new("ShaderNodeTexCoord")
    pnoise = pn.new("ShaderNodeTexNoise")
    pdetail = pn.new("ShaderNodeTexNoise")
    pramp = pn.new("ShaderNodeValToRGB")
    prough = pn.new("ShaderNodeMapRange")
    pbump = pn.new("ShaderNodeBump")
    pnoise.noise_dimensions = '3D'
    pnoise.inputs["Scale"].default_value = 2.6
    pnoise.inputs["Detail"].default_value = 7.0
    pnoise.inputs["Roughness"].default_value = 0.62
    pdetail.noise_dimensions = '3D'
    pdetail.inputs["Scale"].default_value = 135.0
    pdetail.inputs["Detail"].default_value = 3.0
    pdetail.inputs["Roughness"].default_value = 0.68
    pramp.color_ramp.elements[0].position = 0.22
    pramp.color_ramp.elements[0].color = (0.25, 0.17, 0.095, 1)
    pramp.color_ramp.elements[1].position = 0.78
    pramp.color_ramp.elements[1].color = (0.58, 0.45, 0.28, 1)
    mid = pramp.color_ramp.elements.new(0.50)
    mid.color = (0.42, 0.31, 0.18, 1)
    prough.inputs["To Min"].default_value = 0.46
    prough.inputs["To Max"].default_value = 0.68
    pbump.inputs["Strength"].default_value = 0.28
    pbump.inputs["Distance"].default_value = 0.035
    pbsdf.inputs["Roughness"].default_value = 0.56
    pbsdf.inputs["Coat Weight"].default_value = 0.04
    for source, target in (
            (ptc.outputs["Generated"], pnoise.inputs["Vector"]),
            (ptc.outputs["Generated"], pdetail.inputs["Vector"]),
            (pnoise.outputs["Fac"], pramp.inputs["Fac"]),
            (pramp.outputs["Color"], pbsdf.inputs["Base Color"]),
            (pnoise.outputs["Fac"], prough.inputs["Value"]),
            (prough.outputs["Result"], pbsdf.inputs["Roughness"]),
            (pdetail.outputs["Fac"], pbump.inputs["Height"]),
            (pbump.outputs["Normal"], pbsdf.inputs["Normal"])):
        pl.new(source, target)
    return plinth_stone


def museumsboden(material, art, boden_objekt):
    """Polierter Marmor mit Schachbrett oder Parkett (`art` = BODEN) auf dem vorhandenen Bodenmaterial."""
    nt = material.node_tree; N, L = nt.nodes, nt.links; p = N["Principled BSDF"]
    tc, ck, nz, mix, rr = (N.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeTexChecker", "ShaderNodeTexNoise", "ShaderNodeMix", "ShaderNodeMapRange"))
    ck.inputs["Scale"].default_value = 11; ck.inputs["Color1"].default_value = (0.82, 0.76, 0.66, 1); ck.inputs["Color2"].default_value = (0.66, 0.60, 0.51, 1)
    nz.inputs["Scale"].default_value = 6; nz.inputs["Detail"].default_value = 12; nz.inputs["Roughness"].default_value = 0.6
    mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'; mix.inputs["Factor"].default_value = 0.6
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.06, 0.16
    for a, b_ in ((tc.outputs["Generated"], ck.inputs["Vector"]), (tc.outputs["Generated"], nz.inputs["Vector"]), (ck.outputs["Color"], mix.inputs["A"]), (nz.outputs["Color"], mix.inputs["B"]),
                  (mix.outputs["Result"], p.inputs["Base Color"]), (nz.outputs["Fac"], rr.inputs["Value"]), (rr.outputs["Result"], p.inputs["Roughness"])): L.new(a, b_)
    p.inputs["Coat Weight"].default_value = 0.6; p.inputs["Coat Roughness"].default_value = 0.03
    if art != "parkett":
        return
    # Dielen im Halbverband: Brick-Textur, pro Diele leicht anderer Ton, Maserung quer zur Dielenlaenge
    bk, wv2, gm2 = (N.new(t) for t in ("ShaderNodeTexBrick", "ShaderNodeTexWave", "ShaderNodeMix"))
    bk.offset, bk.offset_frequency, bk.squash = 0.5, 2, 1.0
    for k, v in (("Scale", 30), ("Color1", (0.60, 0.38, 0.19, 1)), ("Color2", (0.42, 0.25, 0.12, 1)), ("Mortar", (0.05, 0.03, 0.02, 1)), ("Mortar Size", 0.006), ("Mortar Smooth", 0.1), ("Brick Width", 1.0), ("Row Height", 0.12)): bk.inputs[k].default_value = v
    wv2.wave_type, wv2.bands_direction = 'BANDS', 'Y'
    for k, v in (("Scale", 250), ("Distortion", 3.0), ("Detail", 3.0), ("Detail Scale", 3.0), ("Detail Roughness", 0.6)): wv2.inputs[k].default_value = v
    gm2.data_type, gm2.blend_type = 'RGBA', 'MULTIPLY'; gm2.inputs["Factor"].default_value = 0.45
    mix.inputs["Factor"].default_value = 0.25; rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.2, 0.32; p.inputs["Coat Weight"].default_value = 0.3
    for a, b_ in ((tc.outputs["Generated"], bk.inputs["Vector"]), (tc.outputs["Generated"], wv2.inputs["Vector"]), (bk.outputs["Color"], gm2.inputs["A"]), (wv2.outputs["Color"], gm2.inputs["B"]), (gm2.outputs["Result"], mix.inputs["A"])): L.new(a, b_)

    # Fischgrät als gemeinsame Bildtextur für Cycles und glTF/Three.js.
    size, plank_units = 512, 5
    period = 2 * plank_units
    parquet_image = D.images.new("Fischgraet Eiche", width=size, height=size)
    pixels = []
    for yy in range(size):
        for xx in range(size):
            u, v = xx / size * period, yy / size * period
            ix, iy = math.floor(u), math.floor(v)
            difference = (ix - iy) % period
            horizontal = difference < plank_units
            if horizontal:
                along, across = difference + u % 1, v % 1
                anchor_x, anchor_y = ix - difference, iy
            else:
                along, across = period - 1 - difference + v % 1, u % 1
                anchor_x, anchor_y = ix, iy - (period - 1 - difference)
            tone = math.sin(anchor_x * 127.1 + anchor_y * 311.7) * 0.022
            grain = 0.010 * math.sin(across * 110 + math.sin(along * 2.8) * 3)
            edge = min(across, 1 - across, along, plank_units - along)
            shade = 0.76 if edge < 0.022 else 1.0
            pixels.extend(((0.36 + tone + grain) * shade,
                           (0.27 + tone * 0.65 + grain) * shade,
                           (0.18 + tone * 0.35 + grain * 0.5) * shade, 1.0))
    parquet_image.pixels.foreach_set(pixels)
    parquet_image.pack()
    texture = N.new("ShaderNodeTexImage"); texture.image = parquet_image
    texture.extension = 'REPEAT'
    L.new(texture.outputs["Color"], p.inputs["Base Color"])
    for connection in list(p.inputs["Roughness"].links): L.remove(connection)
    p.inputs["Roughness"].default_value = 0.46
    p.inputs["Coat Weight"].default_value = 0.10
    # 18 cm breite, 90 cm lange Stäbe, diagonal zur Raumachse verlegt.
    uv_layer = boden_objekt.data.uv_layers.new(name="Fischgraet UV")
    uv_layer.active_render = True
    uv_node = N.new("ShaderNodeUVMap"); uv_node.uv_map = uv_layer.name
    L.new(uv_node.outputs["UV"], texture.inputs["Vector"])
    for polygon in boden_objekt.data.polygons:
        for loop_index in polygon.loop_indices:
            vertex = boden_objekt.matrix_world @ boden_objekt.data.vertices[boden_objekt.data.loops[loop_index].vertex_index].co
            uv_layer.data[loop_index].uv = ((vertex.x + vertex.y) / (math.sqrt(2) * 1.8),
                                            (vertex.y - vertex.x) / (math.sqrt(2) * 1.8))


def eichenholz(name, maserung):
    """Helle Naturholz-Eiche; `maserung` skaliert das Rauschen je Achse (lang gezogen entlang der Faser)."""
    wood = simple_material(name, (0.23, 0.105, 0.038, 1), 0.48)
    wood_nodes = wood.node_tree.nodes; wood_links = wood.node_tree.links
    wood_coords = wood_nodes.new("ShaderNodeTexCoord")
    wood_mapping = wood_nodes.new("ShaderNodeMapping")
    wood_mapping.inputs["Scale"].default_value = maserung
    wood_noise = wood_nodes.new("ShaderNodeTexNoise")
    wood_noise.inputs["Scale"].default_value = 3.0
    wood_noise.inputs["Detail"].default_value = 3.0
    wood_ramp = wood_nodes.new("ShaderNodeValToRGB")
    wood_ramp.color_ramp.elements[0].color = (0.36, 0.22, 0.10, 1)  # helle Naturholz-Eiche
    wood_ramp.color_ramp.elements[1].color = (0.66, 0.48, 0.27, 1)
    wood_shader = wood_nodes["Principled BSDF"]
    wood_links.new(wood_coords.outputs["Object"], wood_mapping.inputs["Vector"])
    wood_links.new(wood_mapping.outputs["Vector"], wood_noise.inputs["Vector"])
    wood_links.new(wood_noise.outputs["Fac"], wood_ramp.inputs["Fac"])
    wood_links.new(wood_ramp.outputs["Color"], wood_shader.inputs["Base Color"])
    wood_bump = wood_nodes.new("ShaderNodeBump")
    wood_bump.inputs["Strength"].default_value = 0.12
    wood_bump.inputs["Distance"].default_value = 0.008
    wood_links.new(wood_noise.outputs["Fac"], wood_bump.inputs["Height"])
    wood_links.new(wood_bump.outputs["Normal"], wood_shader.inputs["Normal"])
    return wood


def titan():
    """Schlanker Fensterrahmen in gebürstetem Titan (hell, kühl, metallisch)."""
    titanium = D.materials.new("Fensterrahmen Titan"); titanium.use_nodes = True
    titanium_bsdf = titanium.node_tree.nodes["Principled BSDF"]
    titanium_bsdf.inputs["Base Color"].default_value = (0.62, 0.62, 0.64, 1)
    titanium_bsdf.inputs["Metallic"].default_value = 1.0
    titanium_bsdf.inputs["Roughness"].default_value = 0.3
    return titanium


def fensterglas():
    """Glas für die Scheibe. Für Schattenstrahlen ist es durchsichtig, damit die Sonne weiter in den Raum fällt."""
    glass = D.materials.new("Fensterglas"); glass.use_nodes = True
    glass_nodes, glass_links = glass.node_tree.nodes, glass.node_tree.links
    glass_bsdf = glass_nodes["Principled BSDF"]
    glass_bsdf.inputs["Transmission Weight"].default_value = 1.0
    glass_bsdf.inputs["Roughness"].default_value = 0.0
    glass_bsdf.inputs["IOR"].default_value = 1.45
    glass_bsdf.inputs["Base Color"].default_value = (0.92, 0.97, 1.0, 1)
    glass_clear = glass_nodes.new("ShaderNodeBsdfTransparent")
    glass_path = glass_nodes.new("ShaderNodeLightPath")
    glass_mix = glass_nodes.new("ShaderNodeMixShader")
    glass_links.new(glass_path.outputs["Is Shadow Ray"], glass_mix.inputs["Fac"])
    glass_links.new(glass_bsdf.outputs["BSDF"], glass_mix.inputs[1])
    glass_links.new(glass_clear.outputs["BSDF"], glass_mix.inputs[2])
    glass_links.new(glass_mix.outputs["Shader"], glass_nodes["Material Output"].inputs["Surface"])
    return glass


def leder():
    """Bordeauxrotes Polsterleder mit feiner Narbung."""
    leather = simple_material("Museumsbank Bordeaux Leder", (0.10, 0.006, 0.017, 1), 0.48)
    nodes, links = leather.node_tree.nodes, leather.node_tree.links
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 230
    grain.inputs['Detail'].default_value = 2
    coords = nodes.new('ShaderNodeTexCoord')
    links.new(coords.outputs['Object'], grain.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .18
    bump.inputs['Distance'].default_value = .0015
    links.new(grain.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], nodes['Principled BSDF'].inputs['Normal'])
    return leather


def dunst():
    """Leichtes Volumen für sichtbare Sonnenstrahlen."""
    vm = D.materials.new("Dunst"); vm.use_nodes = True; nt_ = vm.node_tree; nt_.nodes.clear()
    pv, vo = nt_.nodes.new("ShaderNodeVolumePrincipled"), nt_.nodes.new("ShaderNodeOutputMaterial")
    pv.inputs["Density"].default_value, pv.inputs["Anisotropy"].default_value = 0.025, 0.35
    nt_.links.new(pv.outputs["Volume"], vo.inputs["Volume"])
    return vm
