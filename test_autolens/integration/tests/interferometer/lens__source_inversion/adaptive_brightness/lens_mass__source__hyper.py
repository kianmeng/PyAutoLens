import autofit as af
import autolens as al
from test_autolens.integration.tests.interferometer import runner

test_type = "lens__source_inversion"
test_name = "lens_mass__source_adaptive_brightness__hyper"
data_type = "lens_mass__source_smooth"
data_resolution = "sma"


def make_pipeline(
    name,
    phase_folders,
    real_space_shape_2d=(100, 100),
    real_space_pixel_scales=(0.1, 0.1),
    optimizer_class=af.MultiNest,
):
    class Phase1(al.PhaseInterferometer):
        def customize_priors(self, results):

            self.galaxies.source.light.sersic_index = af.UniformPrior(3.9, 4.1)

    phase1 = Phase1(
        phase_name="phase_1",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(redshift=0.5, mass=al.mp.EllipticalIsothermal),
            source=al.GalaxyModel(redshift=1.0, light=al.lp.EllipticalSersic),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        optimizer_class=optimizer_class,
    )

    phase1.optimizer.const_efficiency_mode = True
    phase1.optimizer.n_live_points = 50
    phase1.optimizer.sampling_efficiency = 0.8

    phase1 = phase1.extend_with_multiple_hyper_phases(hyper_galaxy=True)

    phase2 = al.PhaseInterferometer(
        phase_name="phase_2_weighted_regularization",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                mass=phase1.result.constant.galaxies.lens.mass,
                hyper_galaxy=phase1.result.hyper_combined.constant.galaxies.lens.hyper_galaxy,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=al.pix.VoronoiBrightnessImage,
                regularization=al.reg.AdaptiveBrightness,
                hyper_galaxy=phase1.result.hyper_combined.constant.galaxies.source.hyper_galaxy,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        optimizer_class=optimizer_class,
    )

    phase2.optimizer.const_efficiency_mode = True
    phase2.optimizer.n_live_points = 30
    phase2.optimizer.sampling_efficiency = 0.8

    phase2 = phase2.extend_with_multiple_hyper_phases(hyper_galaxy=True, inversion=True)

    phase3 = al.PhaseInterferometer(
        phase_name="phase_3",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                mass=phase1.result.variable.galaxies.lens.mass,
                shear=phase1.result.variable.galaxies.lens.shear,
                hyper_galaxy=phase2.result.hyper_combined.constant.galaxies.lens.hyper_galaxy,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                pixelization=phase2.result.constant.galaxies.source.pixelization,
                regularization=phase2.result.constant.galaxies.source.regularization,
                hyper_galaxy=phase2.result.hyper_combined.constant.galaxies.source.hyper_galaxy,
            ),
        ),
        real_space_shape_2d=real_space_shape_2d,
        real_space_pixel_scales=real_space_pixel_scales,
        optimizer_class=optimizer_class,
    )

    phase3.optimizer.const_efficiency_mode = True
    phase3.optimizer.n_live_points = 40
    phase3.optimizer.sampling_efficiency = 0.8

    phase3 = phase3.extend_with_multiple_hyper_phases(hyper_galaxy=True, inversion=True)

    return al.PipelineDataset(name, phase1, phase2, phase3)


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])