"""Cycles-Einstellungen: OptiX, Ausgabe und die vier GPU-Presets."""
import os

import bpy


def enable_optix():
    """OptiX aktivieren und ausschliesslich erkannte OptiX-GPUs verwenden."""
    cycles_preferences = bpy.context.preferences.addons["cycles"].preferences

    try:
        cycles_preferences.compute_device_type = "OPTIX"
    except TypeError as exc:
        raise RuntimeError(
            "OptiX ist in dieser Blender-Installation nicht verfuegbar. "
            "Bitte NVIDIA-Treiber und Blender-Version pruefen."
        ) from exc

    cycles_preferences.get_devices()
    optix_devices = [
        device
        for device in cycles_preferences.devices
        if device.type == "OPTIX"
    ]

    if not optix_devices:
        raise RuntimeError("Blender hat kein OptiX-faehiges Geraet gefunden.")

    for device in cycles_preferences.devices:
        device.use = device.type == "OPTIX"

    print(
        "OptiX aktiviert: "
        + ", ".join(device.name for device in optix_devices)
    )


def grundeinstellungen(scene, e):
    """Renderer, Auflösung, Bildfolge und Ausgabepfad aus den Einstellungen `e` setzen."""
    scene.render.engine = "CYCLES"
    enable_optix()
    scene.cycles.device = "GPU"
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 6
    scene.render.resolution_x = e.RESOLUTION_X
    scene.render.resolution_y = e.RESOLUTION_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = e.FPS
    scene.frame_start = 1
    scene.frame_end = max(2, round(e.FPS * e.DURATION))

    if e.MAKE_VIDEO:
        scene.cycles.samples = 48
        os.makedirs(e.FRAMES_DIR, exist_ok=True)
        scene.render.filepath = e.ANIMATION_OUTPUT
        scene.render.use_overwrite = not e.RESUME_RENDER
    else:
        scene.cycles.samples = 64
        os.makedirs(e.OUTPUT_DIR, exist_ok=True)
        scene.render.filepath = e.STILL_OUTPUT
        scene.render.use_overwrite = True

    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.use_file_extension = True
    scene.render.use_placeholder = False

    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass


def setup_cycles():
    """Gemeinsame Einstellungen für alle Cycles-Presets setzen."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'
    scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scene.cycles.volume_bounces = 0
    scene.cycles.sample_clamp_direct = 0.0
    scene.render.use_persistent_data = True


# Name: (Anzeige, Werte für scene.cycles)
PRESETS = {
    "test": ("SCHNELLER TEST", dict(
        adaptive_threshold=0.05, samples=16,
        denoising_prefilter='FAST', denoising_quality='BALANCED',
        max_bounces=4, diffuse_bounces=1, glossy_bounces=2,
        transmission_bounces=2, transparent_max_bounces=2,
        sample_clamp_indirect=3.0, caustics_reflective=False, caustics_refractive=False)),
    "final_fast": ("FINAL FAST", dict(
        adaptive_threshold=0.03, samples=32,
        denoising_prefilter='FAST', denoising_quality='BALANCED',
        max_bounces=5, diffuse_bounces=2, glossy_bounces=3,
        transmission_bounces=3, transparent_max_bounces=3,
        sample_clamp_indirect=4.0, caustics_reflective=False, caustics_refractive=False)),
    "animation": ("ANIMATION SCHNELL", dict(
        adaptive_threshold=0.02, samples=48,
        denoising_prefilter='FAST', denoising_quality='BALANCED',
        max_bounces=6, diffuse_bounces=2, glossy_bounces=4,
        transmission_bounces=4, transparent_max_bounces=4,
        sample_clamp_indirect=5.0, caustics_reflective=False, caustics_refractive=False)),
    "quality": ("QUALITÄT", dict(
        adaptive_threshold=0.01, samples=128,
        denoising_prefilter='ACCURATE', denoising_quality='HIGH',
        max_bounces=8, diffuse_bounces=4, glossy_bounces=6,
        transmission_bounces=8, transparent_max_bounces=8,
        sample_clamp_indirect=10.0, caustics_reflective=True, caustics_refractive=True)),
}


def preset_anwenden(name):
    anzeige, werte = PRESETS[name]
    for schluessel, wert in werte.items():
        setattr(bpy.context.scene.cycles, schluessel, wert)
    print("Preset aktiviert: " + anzeige)
