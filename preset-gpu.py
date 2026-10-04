import bpy

scene = bpy.context.scene


def preset_quality():
    c = scene.cycles

    scene.render.engine = 'CYCLES'
    c.device = 'GPU'

    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.01
    c.samples = 128

    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.denoising_prefilter = 'ACCURATE'
    c.denoising_quality = 'HIGH'

    c.max_bounces = 8
    c.diffuse_bounces = 4
    c.glossy_bounces = 6
    c.transmission_bounces = 8
    c.volume_bounces = 0
    c.transparent_max_bounces = 8

    c.sample_clamp_direct = 0.0
    c.sample_clamp_indirect = 10.0

    c.caustics_reflective = True
    c.caustics_refractive = True

    scene.render.use_persistent_data = True

    print("Preset aktiviert: QUALITÄT")


def preset_test():
    c = scene.cycles

    scene.render.engine = 'CYCLES'
    c.device = 'GPU'

    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.samples = 16

    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 4
    c.diffuse_bounces = 1
    c.glossy_bounces = 2
    c.transmission_bounces = 2
    c.volume_bounces = 0
    c.transparent_max_bounces = 2

    c.sample_clamp_direct = 0.0
    c.sample_clamp_indirect = 3.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    scene.render.use_persistent_data = True

    print("Preset aktiviert: SCHNELLER TEST")


def preset_animation():
    c = scene.cycles

    scene.render.engine = 'CYCLES'
    c.device = 'GPU'

    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.samples = 48

    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 4
    c.transmission_bounces = 4
    c.volume_bounces = 0
    c.transparent_max_bounces = 4

    c.sample_clamp_direct = 0.0
    c.sample_clamp_indirect = 5.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    scene.render.use_persistent_data = True

    print("Preset aktiviert: ANIMATION SCHNELL")

def preset_final_fast():
    c = scene.cycles

    scene.render.engine = 'CYCLES'
    c.device = 'GPU'

    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.03
    c.samples = 32

    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.denoising_prefilter = 'FAST'
    c.denoising_quality = 'BALANCED'

    c.max_bounces = 5
    c.diffuse_bounces = 2
    c.glossy_bounces = 3
    c.transmission_bounces = 3
    c.volume_bounces = 0
    c.transparent_max_bounces = 3

    c.sample_clamp_direct = 0.0
    c.sample_clamp_indirect = 4.0

    c.caustics_reflective = False
    c.caustics_refractive = False

    scene.render.use_persistent_data = True

    print("Preset aktiviert: FINAL FAST")
# -------------------------------------------------
# HIER NUR EINE ZEILE AKTIV LASSEN
# -------------------------------------------------

# preset_quality()
# preset_test()
# preset_animation()
preset_final_fast()