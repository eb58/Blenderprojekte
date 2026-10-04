import bpy

scene = bpy.context.scene


def enable_optix():
    """OptiX wählen und alle erkannten OptiX-GPUs aktivieren."""
    cycles_preferences = bpy.context.preferences.addons["cycles"].preferences

    try:
        cycles_preferences.compute_device_type = 'OPTIX'
    except TypeError as exc:
        raise RuntimeError(
            "OptiX ist in dieser Blender-Installation nicht verfügbar. "
            "Bitte NVIDIA-Treiber und Blender-Version prüfen."
        ) from exc

    # Geräteliste nach dem Wechsel des Backends aktualisieren.
    cycles_preferences.get_devices()
    optix_devices = [
        device for device in cycles_preferences.devices
        if device.type == 'OPTIX'
    ]

    if not optix_devices:
        raise RuntimeError("Blender hat kein OptiX-fähiges Gerät gefunden.")

    # CPU abwählen und nur OptiX-Geräte aktivieren.
    for device in cycles_preferences.devices:
        device.use = device.type == 'OPTIX'

    print(
        "OptiX aktiviert: "
        + ", ".join(device.name for device in optix_devices)
    )


def setup_cycles():
    """Gemeinsame Einstellungen für alle Cycles-Presets setzen."""
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scene.cycles.volume_bounces = 0
    scene.cycles.sample_clamp_direct = 0.0
    scene.render.use_persistent_data = True


def preset_quality():
    c = scene.cycles

    c.adaptive_threshold = 0.01
    c.samples = 128

    c.denoising_prefilter = 'ACCURATE'
    c.denoising_quality = 'HIGH'

    c.max_bounces = 8
    c.diffuse_bounces = 4
    c.glossy_bounces = 6
    c.transmission_bounces = 8
    c.transparent_max_bounces = 8

    c.sample_clamp_indirect = 10.0

    c.caustics_reflective = True
    c.caustics_refractive = True

    print("Preset aktiviert: QUALITÄT")


def preset_test():
    c = scene.cycles

    c.adaptive_threshold = 0.05
    c.samples = 16

    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 4
    c.diffuse_bounces = 1
    c.glossy_bounces = 2
    c.transmission_bounces = 2
    c.transparent_max_bounces = 2

    c.sample_clamp_indirect = 3.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    print("Preset aktiviert: SCHNELLER TEST")


def preset_animation():
    c = scene.cycles

    c.adaptive_threshold = 0.02
    c.samples = 48

    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 4
    c.transmission_bounces = 4
    c.transparent_max_bounces = 4

    c.sample_clamp_indirect = 5.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    print("Preset aktiviert: ANIMATION SCHNELL")

def preset_final_fast():
    c = scene.cycles

    c.adaptive_threshold = 0.03
    c.samples = 32

    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 5
    c.diffuse_bounces = 2
    c.glossy_bounces = 3
    c.transmission_bounces = 3
    c.transparent_max_bounces = 3

    c.sample_clamp_indirect = 4.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    print("Preset aktiviert: FINAL FAST")
# -------------------------------------------------
# HIER NUR EINE ZEILE AKTIV LASSEN
# -------------------------------------------------

enable_optix()
setup_cycles()

# preset_quality()
# preset_test()
# preset_animation()
preset_final_fast()
