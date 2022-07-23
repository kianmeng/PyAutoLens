import numpy as np
import pytest

import autolens as al


def test__model_visibilities(interferometer_7):

    g0 = al.Galaxy(redshift=0.5, bulge=al.m.MockLightProfile(image_2d=np.ones(2)))
    tracer = al.Tracer.from_galaxies(galaxies=[g0])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.model_visibilities.slim[0] == pytest.approx(
        np.array([1.2933 + 0.2829j]), 1.0e-4
    )
    assert fit.log_likelihood == pytest.approx(-27.06284, 1.0e-4)


def test__noise_map__with_and_without_hyper_background(interferometer_7):

    g0 = al.Galaxy(redshift=0.5, bulge=al.m.MockLightProfile(image_2d=np.ones(2)))
    tracer = al.Tracer.from_galaxies(galaxies=[g0])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert (fit.noise_map.slim == np.full(fill_value=2.0 + 2.0j, shape=(7,))).all()

    hyper_background_noise = al.hyper_data.HyperBackgroundNoise(noise_scale=1.0)

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        hyper_background_noise=hyper_background_noise,
    )

    assert (fit.noise_map.slim == np.full(fill_value=3.0 + 3.0j, shape=(7,))).all()
    assert fit.log_likelihood == pytest.approx(-30.24288, 1.0e-4)


def test__fit_figure_of_merit(interferometer_7):

    g0 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllSersic(intensity=1.0),
        disk=al.lp.EllSersic(intensity=2.0),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )

    g1 = al.Galaxy(redshift=1.0, bulge=al.lp.EllSersic(intensity=1.0))

    tracer = al.Tracer.from_galaxies(galaxies=[g0, g1])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.perform_inversion is False
    assert fit.figure_of_merit == pytest.approx(-59413306.47762, 1.0e-4)

    basis = al.lp_basis.Basis(
        light_profile_list=[
            al.lp.EllSersic(intensity=1.0),
            al.lp.EllSersic(intensity=2.0),
        ]
    )

    g0 = al.Galaxy(
        redshift=0.5, bulge=basis, mass_profile=al.mp.SphIsothermal(einstein_radius=1.0)
    )

    g1 = al.Galaxy(redshift=1.0, bulge=al.lp.EllSersic(intensity=1.0))

    tracer = al.Tracer.from_galaxies(galaxies=[g0, g1])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.perform_inversion is False
    assert fit.figure_of_merit == pytest.approx(-59413306.47762, 1.0e-4)

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=0.01)

    g0 = al.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit.perform_inversion is True
    assert fit.figure_of_merit == pytest.approx(-66.90612, 1.0e-4)

    galaxy_light = al.Galaxy(redshift=0.5, bulge=al.lp.EllSersic(intensity=1.0))

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=1.0)
    galaxy_pix = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[galaxy_light, galaxy_pix])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit.perform_inversion is True
    assert fit.figure_of_merit == pytest.approx(-1570173.14216, 1.0e-4)

    g0_linear = al.Galaxy(
        redshift=0.5,
        bulge=al.lp_linear.EllSersic(sersic_index=1.0),
        disk=al.lp_linear.EllSersic(sersic_index=4.0),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )

    tracer = al.Tracer.from_galaxies(galaxies=[g0_linear, g1])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.perform_inversion is True
    assert fit.figure_of_merit == pytest.approx(-669283.091396, 1.0e-4)

    basis = al.lp_basis.Basis(
        light_profile_list=[
            al.lp_linear.EllSersic(sersic_index=1.0),
            al.lp_linear.EllSersic(sersic_index=4.0),
        ]
    )

    g0_linear = al.Galaxy(
        redshift=0.5, bulge=basis, mass_profile=al.mp.SphIsothermal(einstein_radius=1.0)
    )

    tracer = al.Tracer.from_galaxies(galaxies=[g0_linear, g1])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.perform_inversion is True
    assert fit.figure_of_merit == pytest.approx(-669283.091396, 1.0e-4)

    tracer = al.Tracer.from_galaxies(galaxies=[g0_linear, galaxy_pix])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.perform_inversion is True
    assert fit.figure_of_merit == pytest.approx(-34.393456, 1.0e-4)


def test__fit_figure_of_merit__include_hyper_methods(interferometer_7):

    hyper_background_noise = al.hyper_data.HyperBackgroundNoise(noise_scale=1.0)

    g0 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllSersic(intensity=1.0),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )

    g1 = al.Galaxy(redshift=1.0, bulge=al.lp.EllSersic(intensity=1.0))

    tracer = al.Tracer.from_galaxies(galaxies=[g0, g1])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        hyper_background_noise=hyper_background_noise,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert (fit.noise_map.slim == np.full(fill_value=3.0 + 3.0j, shape=(7,))).all()
    assert fit.log_likelihood == pytest.approx(-9648681.9168, 1e-4)
    assert fit.figure_of_merit == pytest.approx(-9648681.9168, 1.0e-4)

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        hyper_background_noise=hyper_background_noise,
        use_hyper_scaling=False,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit.noise_map == pytest.approx(interferometer_7.noise_map, 1.0e-4)

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=0.01)

    g0 = al.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        hyper_background_noise=hyper_background_noise,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert (fit.noise_map.slim == np.full(fill_value=3.0 + 3.0j, shape=(7,))).all()
    assert fit.log_evidence == pytest.approx(-68.63380, 1e-4)
    assert fit.figure_of_merit == pytest.approx(-68.63380, 1.0e-4)

    galaxy_light = al.Galaxy(redshift=0.5, bulge=al.lp.EllSersic(intensity=1.0))

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=1.0)
    galaxy_pix = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[galaxy_light, galaxy_pix])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        hyper_background_noise=hyper_background_noise,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert (fit.noise_map.slim == np.full(fill_value=3.0 + 3.0j, shape=(7,))).all()
    assert fit.log_evidence == pytest.approx(-892439.04665, 1e-4)
    assert fit.figure_of_merit == pytest.approx(-892439.04665, 1.0e-4)


def test___fit_figure_of_merit__different_settings(
    interferometer_7, interferometer_7_lop
):

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=0.01)

    g0 = al.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

    fit = al.FitInterferometer(
        dataset=interferometer_7_lop,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(
            use_w_tilde=False, use_linear_operators=True
        ),
    )

    assert (fit.noise_map.slim == np.full(fill_value=2.0 + 2.0j, shape=(7,))).all()
    assert fit.log_evidence == pytest.approx(-71.5177, 1e-4)
    assert fit.figure_of_merit == pytest.approx(-71.5177, 1.0e-4)


def test___galaxy_model_image_dict(interferometer_7, interferometer_7_grid):

    # Normal Light Profiles Only

    g0 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllSersic(intensity=1.0),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )
    g1 = al.Galaxy(redshift=1.0, bulge=al.lp.EllSersic(intensity=1.0))
    g2 = al.Galaxy(redshift=1.0)

    tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

    fit = al.FitInterferometer(
        dataset=interferometer_7_grid,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    traced_grid_2d_list_from = tracer.traced_grid_2d_list_from(
        grid=interferometer_7_grid.grid
    )

    g0_image = g0.image_2d_from(grid=traced_grid_2d_list_from[0])
    g1_image = g1.image_2d_from(grid=traced_grid_2d_list_from[1])

    assert fit.galaxy_model_image_dict[g0] == pytest.approx(g0_image, 1.0e-4)
    assert fit.galaxy_model_image_dict[g1] == pytest.approx(g1_image, 1.0e-4)

    # Linear Light Profiles Only

    g0_linear = al.Galaxy(
        redshift=0.5,
        bulge=al.lp_linear.EllSersic(),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )
    g1_linear = al.Galaxy(redshift=1.0, bulge=al.lp_linear.EllSersic())

    tracer = al.Tracer.from_galaxies(galaxies=[g0_linear, g1_linear, g2])

    fit = al.FitInterferometer(
        dataset=interferometer_7_grid,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit.galaxy_model_image_dict[g0_linear][4] == pytest.approx(
        1.00018622848, 1.0e-2
    )
    assert fit.galaxy_model_image_dict[g1_linear][3] == pytest.approx(
        -3.89387356e-04, 1.0e-2
    )

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=1.0)

    g0_no_light = al.Galaxy(
        redshift=0.5, mass_profile=al.mp.SphIsothermal(einstein_radius=1.0)
    )
    galaxy_pix_0 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[g0_no_light, galaxy_pix_0])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert (fit.galaxy_model_image_dict[g0_no_light].native == np.zeros((7, 7))).all()

    assert fit.galaxy_model_image_dict[galaxy_pix_0][0] == pytest.approx(
        -0.169439019, 1.0e-4
    )

    # Normal light + Linear Light PRofiles + Pixelization + Regularizaiton

    galaxy_pix_1 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)
    tracer = al.Tracer.from_galaxies(
        galaxies=[g0, g0_linear, g2, galaxy_pix_0, galaxy_pix_1]
    )

    fit = al.FitInterferometer(
        dataset=interferometer_7_grid,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit.galaxy_model_image_dict[g0] == pytest.approx(g0_image, 1.0e-4)

    assert fit.galaxy_model_image_dict[g0_linear][4] == pytest.approx(
        -1946.44265722, 1.0e-4
    )

    assert fit.galaxy_model_image_dict[galaxy_pix_0][4] == pytest.approx(
        0.0473537322, 1.0e-3
    )
    assert fit.galaxy_model_image_dict[galaxy_pix_1][4] == pytest.approx(
        0.0473505541, 1.0e-3
    )
    assert (fit.galaxy_model_image_dict[g2] == np.zeros(9)).all()


def test__galaxy_model_visibilities_dict(interferometer_7, interferometer_7_grid):

    # Normal Light Profiles Only

    g0 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllSersic(intensity=1.0),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )
    g1 = al.Galaxy(redshift=1.0, bulge=al.lp.EllSersic(intensity=1.0))
    g2 = al.Galaxy(redshift=1.0)

    tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    traced_grid_2d_list_from = tracer.traced_grid_2d_list_from(
        grid=interferometer_7_grid.grid
    )

    g0_profile_visibilities = g0.visibilities_from(
        grid=traced_grid_2d_list_from[0], transformer=interferometer_7_grid.transformer
    )

    g1_profile_visibilities = g1.visibilities_from(
        grid=traced_grid_2d_list_from[1], transformer=interferometer_7_grid.transformer
    )

    assert fit.galaxy_model_visibilities_dict[g0].slim == pytest.approx(
        g0_profile_visibilities, 1.0e-4
    )
    assert fit.galaxy_model_visibilities_dict[g1].slim == pytest.approx(
        g1_profile_visibilities, 1.0e-4
    )
    assert (
        fit.galaxy_model_visibilities_dict[g2].slim == (0.0 + 0.0j) * np.zeros((7,))
    ).all()

    assert fit.model_visibilities.slim == pytest.approx(
        fit.galaxy_model_visibilities_dict[g0].slim
        + fit.galaxy_model_visibilities_dict[g1].slim,
        1.0e-4,
    )

    # Linear Light Profiles Only

    g0_linear = al.Galaxy(
        redshift=0.5,
        bulge=al.lp_linear.EllSersic(),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )
    g1_linear = al.Galaxy(redshift=1.0, bulge=al.lp_linear.EllSersic())

    tracer = al.Tracer.from_galaxies(galaxies=[g0_linear, g1_linear, g2])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.galaxy_model_visibilities_dict[g0_linear][0] == pytest.approx(
        1.0002975772292932 - 7.12783377916253e-21j, 1.0e-2
    )
    assert fit.galaxy_model_visibilities_dict[g1_linear][0] == pytest.approx(
        -0.0002828972025576841 + 3.035459109423297e-06j, 1.0e-2
    )
    assert (fit.galaxy_model_visibilities_dict[g2] == np.zeros((7,))).all()

    assert fit.model_visibilities == pytest.approx(
        fit.galaxy_model_visibilities_dict[g0_linear]
        + fit.galaxy_model_visibilities_dict[g1_linear],
        1.0e-4,
    )

    # Pixelization + Regularizaiton only

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=1.0)

    g0_no_light = al.Galaxy(
        redshift=0.5, mass_profile=al.mp.SphIsothermal(einstein_radius=1.0)
    )
    galaxy_pix_0 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[g0_no_light, galaxy_pix_0])

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert (fit.galaxy_model_visibilities_dict[g0_no_light] == np.zeros((7,))).all()
    assert fit.galaxy_model_visibilities_dict[galaxy_pix_0][0] == pytest.approx(
        0.2813594007737543 + 0.18428485685088292j, 1.0e-4
    )

    assert fit.model_visibilities == pytest.approx(
        fit.galaxy_model_visibilities_dict[galaxy_pix_0], 1.0e-4
    )

    # Normal light + Linear Light PRofiles + Pixelization + Regularizaiton

    galaxy_pix_1 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(
        galaxies=[g0, g0_linear, g2, galaxy_pix_0, galaxy_pix_1]
    )

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.galaxy_model_visibilities_dict[g0] == pytest.approx(
        g0_profile_visibilities, 1.0e-4
    )

    assert fit.galaxy_model_visibilities_dict[g0_linear][0] == pytest.approx(
        -1946.6593508251335 + 1.3871336483456645e-17j, 1.0e-4
    )

    assert fit.galaxy_model_visibilities_dict[galaxy_pix_0][0] == pytest.approx(
        0.04732569077375984 + 0.14872801091458496j, 1.0e-4
    )
    assert fit.galaxy_model_visibilities_dict[galaxy_pix_1][0] == pytest.approx(
        0.047320971438523735 + 0.14872801091458515j, 1.0e-4
    )
    assert (fit.galaxy_model_visibilities_dict[g2] == np.zeros((7,))).all()


def test__model_visibilities_of_planes_list(interferometer_7):

    g0 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllSersic(intensity=1.0),
        mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
    )

    g1_linear = al.Galaxy(redshift=0.75, bulge=al.lp_linear.EllSersic())

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=1.0)

    galaxy_pix_0 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)
    galaxy_pix_1 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(
        galaxies=[g0, g1_linear, galaxy_pix_0, galaxy_pix_1]
    )

    fit = al.FitInterferometer(dataset=interferometer_7, tracer=tracer)

    assert fit.model_visibilities_of_planes_list[0] == pytest.approx(
        fit.galaxy_model_visibilities_dict[g0], 1.0e-4
    )
    assert fit.model_visibilities_of_planes_list[1] == pytest.approx(
        fit.galaxy_model_visibilities_dict[g1_linear], 1.0e-4
    )
    assert fit.model_visibilities_of_planes_list[2] == pytest.approx(
        fit.galaxy_model_visibilities_dict[galaxy_pix_0]
        + fit.galaxy_model_visibilities_dict[galaxy_pix_1],
        1.0e-4,
    )


def test___stochastic_mode__gives_different_log_likelihood_list(interferometer_7):

    pix = al.pix.VoronoiBrightnessImage(pixels=5)
    reg = al.reg.Constant(coefficient=1.0)

    g0 = al.Galaxy(
        redshift=0.5,
        pixelization=pix,
        regularization=reg,
        hyper_model_image=al.Array2D.ones(shape_native=(3, 3), pixel_scales=1.0),
        hyper_galaxy_image=al.Array2D.ones(shape_native=(3, 3), pixel_scales=1.0),
    )

    tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

    fit_0 = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_pixelization=al.SettingsPixelization(is_stochastic=False),
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )
    fit_1 = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_pixelization=al.SettingsPixelization(is_stochastic=False),
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit_0.log_evidence == fit_1.log_evidence

    fit_0 = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_pixelization=al.SettingsPixelization(is_stochastic=True),
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )
    fit_1 = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_pixelization=al.SettingsPixelization(is_stochastic=True),
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit_0.log_evidence != fit_1.log_evidence


def test__total_mappers(interferometer_7):
    g0 = al.Galaxy(redshift=0.5)

    g1 = al.Galaxy(redshift=1.0)

    g2 = al.Galaxy(redshift=2.0)

    tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit.total_mappers == 0

    g2 = al.Galaxy(
        redshift=2.0,
        pixelization=al.pix.Rectangular(),
        regularization=al.reg.Constant(),
    )

    tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(use_w_tilde=False),
    )

    assert fit.total_mappers == 1
