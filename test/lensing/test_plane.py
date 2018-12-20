import numpy as np
import pytest
from astropy import cosmology as cosmo

from autolens import exc
from autolens.data.array.util import mapping_util
from autolens.data.array import grids, mask
from autolens.model.inversion import pixelizations, regularization
from autolens.model.galaxy import galaxy as g
from autolens.lensing import plane as pl
from autolens.model.profiles import light_profiles as lp, mass_profiles as mp
from test.mock.mock_inversion import MockRegularization, MockPixelization
from test.mock.mock_imaging import MockBorders

@pytest.fixture(name="data_grid_stack")
def make_data_grid_stack():
    ma = mask.Mask(np.array([[True, True, True, True],
                             [True, False, False, True],
                             [True, True, True, True]]), pixel_scale=6.0)

    data_grid_stack = grids.GridStack.grid_stack_from_mask_sub_grid_size_and_psf_shape(mask=ma, sub_grid_size=2, psf_shape=(3, 3))

    # Manually overwrite a set of cooridnates to make tests of grid_stacks and defledctions straightforward

    data_grid_stack.regular[0] = np.array([1.0, 1.0])
    data_grid_stack.regular[1] = np.array([1.0, 0.0])
    data_grid_stack.sub[0] = np.array([1.0, 1.0])
    data_grid_stack.sub[1] = np.array([1.0, 0.0])
    data_grid_stack.sub[2] = np.array([1.0, 1.0])
    data_grid_stack.sub[3] = np.array([1.0, 0.0])
    data_grid_stack.sub[4] = np.array([-1.0, 2.0])
    data_grid_stack.sub[5] = np.array([-1.0, 4.0])
    data_grid_stack.sub[6] = np.array([1.0, 2.0])
    data_grid_stack.sub[7] = np.array([1.0, 4.0])
    data_grid_stack.blurring[0] = np.array([1.0, 0.0])
    data_grid_stack.blurring[1] = np.array([-6.0, -3.0])
    data_grid_stack.blurring[2] = np.array([-6.0, 3.0])
    data_grid_stack.blurring[3] = np.array([-6.0, 9.0])
    data_grid_stack.blurring[4] = np.array([0.0, -9.0])
    data_grid_stack.blurring[5] = np.array([0.0, 9.0])
    data_grid_stack.blurring[6] = np.array([6.0, -9.0])
    data_grid_stack.blurring[7] = np.array([6.0, -3.0])
    data_grid_stack.blurring[8] = np.array([6.0, 3.0])
    data_grid_stack.blurring[9] = np.array([6.0, 9.0])

    return data_grid_stack


@pytest.fixture(name="data_grid_stack_1")
def make_data_grid_stack_1():
    ma = mask.Mask(np.array([[True, True, True, True],
                             [True, False, False, True],
                             [True, True, True, True]]), pixel_scale=12.0)

    data_grid_stack = grids.GridStack.grid_stack_from_mask_sub_grid_size_and_psf_shape(mask=ma, sub_grid_size=2, psf_shape=(3, 3))

    # Manually overwrite a set of cooridnates to make tests of grid_stacks and defledctions straightforward

    data_grid_stack.regular[0] = np.array([2.0, 2.0])
    data_grid_stack.regular[1] = np.array([2.0, 2.0])
    data_grid_stack.sub[0] = np.array([2.0, 2.0])
    data_grid_stack.sub[1] = np.array([2.0, 0.0])
    data_grid_stack.sub[2] = np.array([2.0, 2.0])
    data_grid_stack.sub[3] = np.array([2.0, 0.0])
    data_grid_stack.sub[4] = np.array([-2.0, 4.0])
    data_grid_stack.sub[5] = np.array([-2.0, 8.0])
    data_grid_stack.sub[6] = np.array([2.0, 4.0])
    data_grid_stack.sub[7] = np.array([2.0, 8.0])
    data_grid_stack.blurring[0] = np.array([2.0, 0.0])
    data_grid_stack.blurring[1] = np.array([-12.0, -6.0])
    data_grid_stack.blurring[2] = np.array([-12.0, 6.0])
    data_grid_stack.blurring[3] = np.array([-12.0, 18.0])
    data_grid_stack.blurring[4] = np.array([0.0, -18.0])
    data_grid_stack.blurring[5] = np.array([0.0, 18.0])
    data_grid_stack.blurring[6] = np.array([12.0, -18.0])
    data_grid_stack.blurring[7] = np.array([12.0, -6.0])
    data_grid_stack.blurring[8] = np.array([12.0, 6.0])
    data_grid_stack.blurring[9] = np.array([12.0, 18.0])

    return data_grid_stack


@pytest.fixture(name="padded_grid_stack")
def make_padded_grid_stack():
    ma = mask.Mask(np.array([[True, False]]), pixel_scale=3.0)
    return grids.GridStack.padded_grid_stack_from_mask_sub_grid_size_and_psf_shape(ma, 2, (3, 3))


@pytest.fixture(name='galaxy_non', scope='function')
def make_galaxy_non():
    return g.Galaxy()


@pytest.fixture(name="galaxy_light")
def make_galaxy_light():
    return g.Galaxy(light_profile=lp.EllipticalSersic(centre=(0.1, 0.1), axis_ratio=1.0, phi=0.0, intensity=1.0,
                                                      effective_radius=0.6, sersic_index=4.0))


@pytest.fixture(name="galaxy_mass")
def make_galaxy_mass():
    return g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=1.0))


@pytest.fixture(name='galaxy_mass_x2')
def make_galaxy_mass_x2():
    return g.Galaxy(sis_0=mp.SphericalIsothermal(einstein_radius=1.0),
                    sis_1=mp.SphericalIsothermal(einstein_radius=1.0))


class TestIntensitiesFromGrid:

    def test__no_galaxies__intensities_returned_as_0s(self, data_grid_stack, galaxy_non):

        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [2.0, 2.0],
                                        [3.0, 3.0]])

        intensities = pl.intensities_from_grid(grid=data_grid_stack.regular,
                                                        galaxies=[galaxy_non])

        assert (intensities[0] == np.array([0.0, 0.0])).all()
        assert (intensities[1] == np.array([0.0, 0.0])).all()
        assert (intensities[2] == np.array([0.0, 0.0])).all()

    def test__galaxy_light__intensities_returned_as_correct_values(self, data_grid_stack, galaxy_light):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [1.0, 0.0],
                                        [-1.0, 0.0]])

        galaxy_intensities = galaxy_light.intensities_from_grid(data_grid_stack.regular)

        tracer_intensities = pl.intensities_from_grid(grid=data_grid_stack.regular,
                                                               galaxies=[galaxy_light])

        assert (galaxy_intensities == tracer_intensities).all()

    def test__galaxy_light_x2__intensities_double_from_above(self, data_grid_stack, galaxy_light):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [1.0, 0.0],
                                        [-1.0, 0.0]])

        galaxy_intensities = galaxy_light.intensities_from_grid(data_grid_stack.regular)

        tracer_intensities = pl.intensities_from_grid(grid=data_grid_stack.regular,
                                                               galaxies=[galaxy_light, galaxy_light])

        assert (2.0 * galaxy_intensities == tracer_intensities).all()

    def test__sub_grid_in__grid_is_mapped_to_image_grid_by_wrapper(self, data_grid_stack, galaxy_light):
        galaxy_image = galaxy_light.intensities_from_grid(data_grid_stack.sub)

        galaxy_image = (galaxy_image[0] + galaxy_image[1] + galaxy_image[2] +
                        galaxy_image[3]) / 4.0

        tracer_intensities = pl.intensities_from_grid(grid=data_grid_stack.sub, galaxies=[galaxy_light])

        assert tracer_intensities[0] == galaxy_image


class TestSurfaceDensityFromGrid:

    def test__no_galaxies__surface_density_returned_as_0s(self, data_grid_stack, galaxy_non):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [2.0, 2.0],
                                        [3.0, 3.0]])

        surface_density = pl.surface_density_from_grid(grid=data_grid_stack.regular, galaxies=[galaxy_non])

        assert (surface_density[0] == np.array([0.0, 0.0])).all()
        assert (surface_density[1] == np.array([0.0, 0.0])).all()
        assert (surface_density[2] == np.array([0.0, 0.0])).all()

    def test__galaxy_mass__surface_density_returned_as_correct_values(self, data_grid_stack, galaxy_mass):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [1.0, 0.0],
                                        [-1.0, 0.0]])

        galaxy_surface_density = galaxy_mass.surface_density_from_grid(data_grid_stack.regular)

        tracer_surface_density = pl.surface_density_from_grid(grid=data_grid_stack.regular,
                                                                       galaxies=[galaxy_mass])

        assert (galaxy_surface_density == tracer_surface_density).all()

    def test__galaxy_mass_x2__surface_density_double_from_above(self, data_grid_stack, galaxy_mass):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [1.0, 0.0],
                                        [-1.0, 0.0]])

        galaxy_surface_density = galaxy_mass.surface_density_from_grid(data_grid_stack.regular)

        tracer_surface_density = pl.surface_density_from_grid(grid=data_grid_stack.regular,
                                                                       galaxies=[galaxy_mass, galaxy_mass])

        assert (2.0 * galaxy_surface_density == tracer_surface_density).all()

    def test__sub_grid_in__grid_is_mapped_to_image_grid_by_wrapper(self, data_grid_stack, galaxy_mass):
        galaxy_image = galaxy_mass.surface_density_from_grid(data_grid_stack.sub)

        galaxy_image = (galaxy_image[0] + galaxy_image[1] + galaxy_image[2] +
                        galaxy_image[3]) / 4.0

        tracer_surface_density = pl.surface_density_from_grid(grid=data_grid_stack.sub,
                                                                       galaxies=[galaxy_mass])

        assert tracer_surface_density[0] == galaxy_image


class TestPotentialFromGrid:

    def test__no_galaxies__potential_returned_as_0s(self, data_grid_stack, galaxy_non):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [2.0, 2.0],
                                        [3.0, 3.0]])

        potential = pl.potential_from_grid(grid=data_grid_stack.regular, galaxies=[galaxy_non])

        assert (potential[0] == np.array([0.0, 0.0])).all()
        assert (potential[1] == np.array([0.0, 0.0])).all()
        assert (potential[2] == np.array([0.0, 0.0])).all()

    def test__galaxy_mass__potential_returned_as_correct_values(self, data_grid_stack, galaxy_mass):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [1.0, 0.0],
                                        [-1.0, 0.0]])

        galaxy_potential = galaxy_mass.potential_from_grid(data_grid_stack.regular)

        tracer_potential = pl.potential_from_grid(grid=data_grid_stack.regular, galaxies=[galaxy_mass])

        assert (galaxy_potential == tracer_potential).all()

    def test__galaxy_mass_x2__potential_double_from_above(self, data_grid_stack, galaxy_mass):
        data_grid_stack.regular = np.array([[1.0, 1.0],
                                        [1.0, 0.0],
                                        [-1.0, 0.0]])

        galaxy_potential = galaxy_mass.potential_from_grid(data_grid_stack.regular)

        tracer_potential = pl.potential_from_grid(grid=data_grid_stack.regular,
                                                           galaxies=[galaxy_mass, galaxy_mass])

        assert (2.0 * galaxy_potential == tracer_potential).all()

    def test__sub_grid_in__grid_is_mapped_to_image_grid_by_wrapper(self, data_grid_stack, galaxy_mass):
        galaxy_image = galaxy_mass.potential_from_grid(data_grid_stack.sub)

        galaxy_image = (galaxy_image[0] + galaxy_image[1] + galaxy_image[2] +
                        galaxy_image[3]) / 4.0

        tracer_potential = pl.potential_from_grid(grid=data_grid_stack.sub, galaxies=[galaxy_mass])

        assert tracer_potential[0] == galaxy_image


class TestDeflectionsFromGrid:

    def test__all_coordinates(self, data_grid_stack, galaxy_mass):
        deflections = pl.deflections_from_grid_stack(data_grid_stack, [galaxy_mass])

        assert deflections.regular[0] == pytest.approx(np.array([0.707, 0.707]), 1e-3)
        assert deflections.sub[0] == pytest.approx(np.array([0.707, 0.707]), 1e-3)
        assert deflections.sub[1] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
        #    assert deflection_stacks.sub.sub_grid_size == 2
        assert deflections.blurring[0] == pytest.approx(np.array([1.0, 0.0]), 1e-3)

    def test__2_identical_lens_galaxies__deflection_angles_double(self, data_grid_stack, galaxy_mass):
        deflections = pl.deflections_from_grid_stack(data_grid_stack, [galaxy_mass, galaxy_mass])

        assert deflections.regular[0] == pytest.approx(np.array([2.0 * 0.707, 2.0 * 0.707]), 1e-3)
        assert deflections.sub[0] == pytest.approx(np.array([2.0 * 0.707, 2.0 * 0.707]), 1e-3)
        assert deflections.sub[1] == pytest.approx(np.array([2.0, 0.0]), 1e-3)
        #    assert deflection_stacks.sub.sub_grid_size == 2
        assert deflections.blurring[0] == pytest.approx(np.array([2.0, 0.0]), 1e-3)

    def test__1_lens_with_2_identical_mass_profiles__deflection_angles_double(self, data_grid_stack, galaxy_mass_x2):
        deflections = pl.deflections_from_grid_stack(data_grid_stack, [galaxy_mass_x2])

        assert deflections.regular[0] == pytest.approx(np.array([2.0 * 0.707, 2.0 * 0.707]), 1e-3)
        assert deflections.sub[0] == pytest.approx(np.array([2.0 * 0.707, 2.0 * 0.707]), 1e-3)
        assert deflections.sub[1] == pytest.approx(np.array([2.0, 0.0]), 1e-3)
        assert deflections.blurring[0] == pytest.approx(np.array([2.0, 0.0]), 1e-3)


class TestSetupTracedGrid:

    def test__simple_sis_model__deflection_angles(self, data_grid_stack, galaxy_mass):
        deflections = pl.deflections_from_grid_stack(data_grid_stack, [galaxy_mass])

        grid_traced = pl.traced_collection_for_deflections(data_grid_stack, deflections)

        assert grid_traced.regular[0] == pytest.approx(np.array([1.0 - 0.707, 1.0 - 0.707]), 1e-2)

    def test_two_identical_lenses__deflection_angles_double(self, data_grid_stack, galaxy_mass):
        deflections = pl.deflections_from_grid_stack(data_grid_stack, [galaxy_mass, galaxy_mass])

        grid_traced = pl.traced_collection_for_deflections(data_grid_stack, deflections)

        assert grid_traced.regular[0] == pytest.approx(np.array([1.0 - 2.0 * 0.707, 1.0 - 2.0 * 0.707]), 1e-3)

    def test_one_lens_with_double_identical_mass_profiles__deflection_angles_double(self, data_grid_stack,
                                                                                    galaxy_mass_x2):
        deflections = pl.deflections_from_grid_stack(data_grid_stack, [galaxy_mass_x2])

        grid_traced = pl.traced_collection_for_deflections(data_grid_stack, deflections)

        assert grid_traced.regular[0] == pytest.approx(np.array([1.0 - 2.0 * 0.707, 1.0 - 2.0 * 0.707]), 1e-3)


class TestAbstractPlane(object):

    class TestRedshift:

        def test__galaxy_redshifts_gives_list_of_redshifts(self):

            g0 = g.Galaxy(redshift=1.0)
            g1 = g.Galaxy(redshift=1.0)
            g2 = g.Galaxy(redshift=1.0)

            plane = pl.AbstractPlane(galaxies=[g0, g1, g2], cosmology=cosmo.Planck15)

            assert plane.galaxy_redshifts == [1.0, 1.0, 1.0]

        def test__galaxy_has_no_redshift__cosmology_input__raises_exception(self):

            g0 = g.Galaxy()
            g1 = g.Galaxy(redshift=1.0)

            with pytest.raises(exc.RayTracingException):
                pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.LambdaCDM)


        def test__galaxies_entered_all_have_no_redshifts__no_exception_raised(self):

            g0 = g.Galaxy()
            g1 = g.Galaxy()

            pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)

        def test__galaxies_entered_all_have_same_redshifts__no_exception_raised(self):

            g0 = g.Galaxy(redshift=0.1)
            g1 = g.Galaxy(redshift=0.1)

            pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)

        def test__1_galaxy_has_redshift_other_does_not__exception_is_raised(self):

            g0 = g.Galaxy(redshift=0.1)
            g1 = g.Galaxy()

            with pytest.raises(exc.RayTracingException):
                pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)

        def test__galaxies_have_different_redshifts__exception_is_raised(self):

            g0 = g.Galaxy(redshift=0.1)
            g1 = g.Galaxy(redshift=1.0)

            with pytest.raises(exc.RayTracingException):
                pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)

        def test__galaxy_has_redshift__returns_redshift(self):

            g0 = g.Galaxy(redshift=0.1)

            plane = pl.AbstractPlane(galaxies=[g0], cosmology=cosmo.Planck15)

            assert plane.redshift == 0.1

        def test__galaxy_has_no_redshift__returns_none(self):

            g0 = g.Galaxy()

            plane = pl.AbstractPlane(galaxies=[g0], cosmology=cosmo.Planck15)

            assert plane.redshift == None

    class TestCosmology:

        def test__arcsec_to_kpc_coversion_and_anguar_diameter_distance_to_earth(self):

            g0 = g.Galaxy(redshift=0.1)
            plane = pl.AbstractPlane(galaxies=[g0], cosmology=cosmo.Planck15)
            assert plane.arcsec_per_kpc_proper == pytest.approx(0.525060, 1e-5)
            assert plane.kpc_per_arcsec_proper == pytest.approx(1.904544, 1e-5)
            assert plane.angular_diameter_distance_to_earth == pytest.approx(392840, 1e-5)

            g0 = g.Galaxy(redshift=1.0)
            plane = pl.AbstractPlane(galaxies=[g0], cosmology=cosmo.Planck15)
            assert plane.arcsec_per_kpc_proper == pytest.approx(0.1214785, 1e-5)
            assert plane.kpc_per_arcsec_proper == pytest.approx(8.231907, 1e-5)
            assert plane.angular_diameter_distance_to_earth == pytest.approx(1697952, 1e-5)

    class TestProperties:

        def test__no_galaxies__raises_exception(self):

            with pytest.raises(exc.RayTracingException):
                pl.AbstractPlane(galaxies=[], cosmology=cosmo.Planck15)

        def test__has_light_profile(self):

            plane = pl.AbstractPlane(galaxies=[g.Galaxy()], cosmology=cosmo.Planck15)
            assert plane.has_light_profile == False

            plane = pl.AbstractPlane(galaxies=[g.Galaxy(light_profile=lp.LightProfile())], cosmology=cosmo.Planck15)
            assert plane.has_light_profile == True

            plane = pl.AbstractPlane(galaxies=[g.Galaxy(light_profile=lp.LightProfile()), g.Galaxy()],
                                     cosmology=cosmo.Planck15)
            assert plane.has_light_profile == True

        def test__has_pixelization(self):

            plane = pl.AbstractPlane(galaxies=[g.Galaxy()], cosmology=cosmo.Planck15)
            assert plane.has_pixelization == False

            galaxy_pix = g.Galaxy(pixelization=pixelizations.Pixelization(),
                                  regularization=regularization.Regularization())

            plane = pl.AbstractPlane(galaxies=[galaxy_pix], cosmology=cosmo.Planck15)
            assert plane.has_pixelization == True

            plane = pl.AbstractPlane(galaxies=[galaxy_pix, g.Galaxy()], cosmology=cosmo.Planck15)
            assert plane.has_pixelization == True

        def test__has_regularization(self):

            plane = pl.AbstractPlane(galaxies=[g.Galaxy()], cosmology=cosmo.Planck15)
            assert plane.has_regularization == False

            galaxy_pix = g.Galaxy(pixelization=pixelizations.Pixelization(),
                                  regularization=regularization.Regularization())

            plane = pl.AbstractPlane(galaxies=[galaxy_pix], cosmology=cosmo.Planck15)
            assert plane.has_regularization == True

            plane = pl.AbstractPlane(galaxies=[galaxy_pix, g.Galaxy()], cosmology=cosmo.Planck15)
            assert plane.has_regularization == True

        def test__has_hyper_galaxy(self):

            plane = pl.AbstractPlane(galaxies=[g.Galaxy()], cosmology=cosmo.Planck15)
            assert plane.has_hyper_galaxy == False

            plane = pl.AbstractPlane(galaxies=[g.Galaxy(hyper_galaxy=g.HyperGalaxy())], cosmology=cosmo.Planck15)
            assert plane.has_hyper_galaxy == True

            plane = pl.AbstractPlane(galaxies=[g.Galaxy(hyper_galaxy=g.HyperGalaxy()), g.Galaxy()],
                                     cosmology=cosmo.Planck15)
            assert plane.has_hyper_galaxy == True

        def test__extract_hyper_galaxies(self):

            plane = pl.AbstractPlane(galaxies=[g.Galaxy()], cosmology=cosmo.Planck15)
            assert plane.hyper_galaxies == [None]

            hyper_galaxy = g.HyperGalaxy()
            plane = pl.AbstractPlane(galaxies=[g.Galaxy(hyper_galaxy=hyper_galaxy)], cosmology=cosmo.Planck15)
            assert plane.hyper_galaxies == [hyper_galaxy]

            plane = pl.AbstractPlane(galaxies=[g.Galaxy(), g.Galaxy(hyper_galaxy=hyper_galaxy), g.Galaxy()],
                                     cosmology=cosmo.Planck15)
            assert plane.hyper_galaxies == [None, hyper_galaxy, None]

    class TestLuminosities:

        def test__within_circle__no_conversion_factor__same_as_galaxy_dimensionless_luminosities(self):

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=1.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=2.0))

            g0_luminosity = g0.luminosity_within_circle(radius=1.0)
            g1_luminosity = g1.luminosity_within_circle(radius=1.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_circles(radius=1.0)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=3.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=4.0))

            g0_luminosity = g0.luminosity_within_circle(radius=2.0)
            g1_luminosity = g1.luminosity_within_circle(radius=2.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_circles(radius=2.0)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

        def test__luminosity_within_circle__same_as_galaxy_luminosities(self):

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=1.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=2.0))

            g0_luminosity = g0.luminosity_within_circle(radius=1.0, conversion_factor=3.0)
            g1_luminosity = g1.luminosity_within_circle(radius=1.0, conversion_factor=3.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_circles(radius=1.0, conversion_factor=3.0)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=3.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=4.0))

            g0_luminosity = g0.luminosity_within_circle(radius=2.0, conversion_factor=6.0)
            g1_luminosity = g1.luminosity_within_circle(radius=2.0, conversion_factor=6.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_circles(radius=2.0, conversion_factor=6.0)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

        def test__within_ellipse__no_conversion_factor__same_as_galaxy_dimensionless_luminosities(self):

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=1.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=2.0))

            g0_luminosity = g0.luminosity_within_ellipse(major_axis=0.8)
            g1_luminosity = g1.luminosity_within_ellipse(major_axis=0.8)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_ellipses(major_axis=0.8)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=3.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=4.0))

            g0_luminosity = g0.luminosity_within_ellipse(major_axis=0.6)
            g1_luminosity = g1.luminosity_within_ellipse(major_axis=0.6)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_ellipses(major_axis=0.6)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

        def test__luminosity_within_ellipse__same_as_galaxy_luminosities(self):

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=1.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=2.0))

            g0_luminosity = g0.luminosity_within_ellipse(major_axis=0.8, conversion_factor=3.0)
            g1_luminosity = g1.luminosity_within_ellipse(major_axis=0.8, conversion_factor=3.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_ellipses(major_axis=0.8, conversion_factor=3.0)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

            g0 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=3.0))
            g1 = g.Galaxy(luminosity=lp.SphericalSersic(intensity=4.0))

            g0_luminosity = g0.luminosity_within_ellipse(major_axis=0.6, conversion_factor=6.0)
            g1_luminosity = g1.luminosity_within_ellipse(major_axis=0.6, conversion_factor=6.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_luminosities = plane.luminosities_of_galaxies_within_ellipses(major_axis=0.6, conversion_factor=6.0)

            assert plane_luminosities[0] == g0_luminosity
            assert plane_luminosities[1] == g1_luminosity

    class TestMasses:

        def test__within_circle__no_conversion_factor__same_as_galaxy_dimensionless_masses(self):

            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=2.0))

            g0_mass = g0.mass_within_circle(radius=1.0)
            g1_mass = g1.mass_within_circle(radius=1.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_circles(radius=1.0)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass

            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=3.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=4.0))

            g0_mass = g0.mass_within_circle(radius=2.0)
            g1_mass = g1.mass_within_circle(radius=2.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_circles(radius=2.0)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass

        def test__mass_within_circle__same_as_galaxy_masses(self):
            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=2.0))

            g0_mass = g0.mass_within_circle(radius=1.0, conversion_factor=3.0)
            g1_mass = g1.mass_within_circle(radius=1.0, conversion_factor=3.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_circles(radius=1.0, conversion_factor=3.0)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass

            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=3.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=4.0))

            g0_mass = g0.mass_within_circle(radius=2.0, conversion_factor=6.0)
            g1_mass = g1.mass_within_circle(radius=2.0, conversion_factor=6.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_circles(radius=2.0, conversion_factor=6.0)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass

        def test__within_ellipse__no_conversion_factor__same_as_galaxy_dimensionless_masses(self):

            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=2.0))

            g0_mass = g0.mass_within_ellipse(major_axis=0.8)
            g1_mass = g1.mass_within_ellipse(major_axis=0.8)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_ellipses(major_axis=0.8)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass

            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=3.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=4.0))

            g0_mass = g0.mass_within_ellipse(major_axis=0.6)
            g1_mass = g1.mass_within_ellipse(major_axis=0.6)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_ellipses(major_axis=0.6)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass

        def test__mass_within_ellipse__same_as_galaxy_masses(self):

            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=2.0))

            g0_mass = g0.mass_within_ellipse(major_axis=0.8, conversion_factor=3.0)
            g1_mass = g1.mass_within_ellipse(major_axis=0.8, conversion_factor=3.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_ellipses(major_axis=0.8, conversion_factor=3.0)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass

            g0 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=3.0))
            g1 = g.Galaxy(mass=mp.SphericalIsothermal(einstein_radius=4.0))

            g0_mass = g0.mass_within_ellipse(major_axis=0.6, conversion_factor=6.0)
            g1_mass = g1.mass_within_ellipse(major_axis=0.6, conversion_factor=6.0)
            plane = pl.AbstractPlane(galaxies=[g0, g1], cosmology=cosmo.Planck15)
            plane_masses = plane.masses_of_galaxies_within_ellipses(major_axis=0.6, conversion_factor=6.0)

            assert plane_masses[0] == g0_mass
            assert plane_masses[1] == g1_mass


class TestPlane(object):

    class TestGridStackSetup:

        def test__data_grid_stack_setup_for_regular_sub_and_blurring__no_deflections(self, data_grid_stack,
                                                                                     galaxy_mass):
            
            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack, compute_deflections=False)

            assert plane.grid_stack.regular == pytest.approx(np.array([[1.0, 1.0], [1.0, 0.0]]), 1e-3)
            assert plane.grid_stack.sub == pytest.approx(np.array([[1.0, 1.0], [1.0, 0.0], [1.0, 1.0], [1.0, 0.0],
                                                                      [-1.0, 2.0], [-1.0, 4.0], [1.0, 2.0], [1.0, 4.0]]), 1e-3)
            assert plane.grid_stack.blurring == pytest.approx(np.array([[1.0, 0.0], [-6.0, -3.0], [-6.0, 3.0], [-6.0, 9.0],
                                                                           [0.0, -9.0], [0.0, 9.0],
                                                                           [6.0, -9.0], [6.0, -3.0], [6.0, 3.0], [6.0, 9.0]]), 1e-3)

            assert plane.deflection_stack == None

        def test__same_as_above_but_test_deflections(self, data_grid_stack, galaxy_mass):

            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack, compute_deflections=True)

            sub_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.sub)
            blurring_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.blurring)

            assert plane.deflection_stack.regular == pytest.approx(np.array([[0.707, 0.707], [1.0, 0.0]]), 1e-3)
            assert (plane.deflection_stack.sub == sub_galaxy_deflections).all()
            assert (plane.deflection_stack.blurring == blurring_galaxy_deflections).all()

        def test__same_as_above__x2_galaxy_in_plane__or_galaxy_x2_sis__deflections_double(self, data_grid_stack,
                                                                                          galaxy_mass,
                                                                                          galaxy_mass_x2):

            plane = pl.Plane(galaxies=[galaxy_mass_x2], grid_stack=data_grid_stack, compute_deflections=True)

            sub_galaxy_deflections = galaxy_mass_x2.deflections_from_grid(data_grid_stack.sub)
            blurring_galaxy_deflections = galaxy_mass_x2.deflections_from_grid(data_grid_stack.blurring)

            assert plane.deflection_stack.regular == pytest.approx(np.array([[2.0 * 0.707, 2.0 * 0.707], [2.0, 0.0]]), 1e-3)
            assert (plane.deflection_stack.sub == sub_galaxy_deflections).all()
            assert (plane.deflection_stack.blurring == blurring_galaxy_deflections).all()

            plane = pl.Plane(galaxies=[galaxy_mass, galaxy_mass], grid_stack=data_grid_stack, compute_deflections=True)

            sub_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.sub)
            blurring_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.blurring)

            assert plane.deflection_stack.regular == pytest.approx(np.array([[2.0 * 0.707, 2.0 * 0.707], [2.0, 0.0]]), 1e-3)
            assert (plane.deflection_stack.sub == 2.0 * sub_galaxy_deflections).all()
            assert (plane.deflection_stack.blurring == 2.0 * blurring_galaxy_deflections).all()

    class TestProperties:

        def test__padded_grid_in__tracer_has_padded_grid_property(self, data_grid_stack, padded_grid_stack, galaxy_light):

            plane = pl.Plane(grid_stack=data_grid_stack, galaxies=[galaxy_light])
            assert plane.has_padded_grid_stack == False

            plane = pl.Plane(grid_stack=padded_grid_stack, galaxies=[galaxy_light])
            assert plane.has_padded_grid_stack == True

    class TestImage:

        def test__image_from_plane__same_as_its_light_profile_image(self, data_grid_stack, galaxy_light):
            
            lp = galaxy_light.light_profiles[0]

            lp_sub_image = lp.intensities_from_grid(data_grid_stack.sub)

            # Perform sub gridding average manually
            lp_image_pixel_0 = (lp_sub_image[0] + lp_sub_image[1] + lp_sub_image[2] + lp_sub_image[3]) / 4
            lp_image_pixel_1 = (lp_sub_image[4] + lp_sub_image[5] + lp_sub_image[6] + lp_sub_image[7]) / 4

            plane = pl.Plane(galaxies=[galaxy_light], grid_stack=data_grid_stack)

            assert (plane.image_plane_image_1d[0] == lp_image_pixel_0).all()
            assert (plane.image_plane_image_1d[1] == lp_image_pixel_1).all()
            assert (plane.image_plane_image ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_image_1d)).all()

        def test__image_from_plane__same_as_its_galaxy_image(self, data_grid_stack, galaxy_light):

            galaxy_image = pl.intensities_from_grid(data_grid_stack.sub, galaxies=[galaxy_light])

            plane = pl.Plane(galaxies=[galaxy_light], grid_stack=data_grid_stack)

            assert (plane.image_plane_image_1d == galaxy_image).all()
            assert (plane.image_plane_image ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_image_1d)).all()

        def test__image_plane_image_of_galaxies(self, data_grid_stack):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
            g1 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=2.0))

            lp0 = g0.light_profiles[0]
            lp1 = g1.light_profiles[0]

            lp0_sub_image = lp0.intensities_from_grid(data_grid_stack.sub)
            lp1_sub_image = lp1.intensities_from_grid(data_grid_stack.sub)

            # Perform sub gridding average manually
            lp0_image_pixel_0 = (lp0_sub_image[0] + lp0_sub_image[1] + lp0_sub_image[2] + lp0_sub_image[3]) / 4
            lp0_image_pixel_1 = (lp0_sub_image[4] + lp0_sub_image[5] + lp0_sub_image[6] + lp0_sub_image[7]) / 4
            lp1_image_pixel_0 = (lp1_sub_image[0] + lp1_sub_image[1] + lp1_sub_image[2] + lp1_sub_image[3]) / 4
            lp1_image_pixel_1 = (lp1_sub_image[4] + lp1_sub_image[5] + lp1_sub_image[6] + lp1_sub_image[7]) / 4

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.image_plane_image_1d[0] == lp0_image_pixel_0 + lp1_image_pixel_0).all()
            assert (plane.image_plane_image_1d[1] == lp0_image_pixel_1 + lp1_image_pixel_1).all()
            assert (plane.image_plane_image ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_image_1d)).all()

            assert (plane.image_plane_image_1d_of_galaxies[0][0] == lp0_image_pixel_0)
            assert (plane.image_plane_image_1d_of_galaxies[0][1] == lp0_image_pixel_1)
            assert (plane.image_plane_image_1d_of_galaxies[1][0] == lp1_image_pixel_0)
            assert (plane.image_plane_image_1d_of_galaxies[1][1] == lp1_image_pixel_1)

        def test__same_as_above__use_multiple_galaxies(self, data_grid_stack):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
            g1 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=2.0))

            g0_image = pl.intensities_from_grid(data_grid_stack.sub, galaxies=[g0])
            g1_image = pl.intensities_from_grid(data_grid_stack.sub, galaxies=[g1])

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.image_plane_image_1d == g0_image + g1_image).all()
            assert (plane.image_plane_image ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_image_1d)).all()

            assert (plane.image_plane_image_1d_of_galaxies[0] == g0_image).all()
            assert (plane.image_plane_image_1d_of_galaxies[1] == g1_image).all()

        def test__padded_grid_stack_in__image_plane_image_is_padded(self, padded_grid_stack, galaxy_light):
            
            lp = galaxy_light.light_profiles[0]

            lp_sub_image = lp.intensities_from_grid(padded_grid_stack.sub)

            # Perform sub gridding average manually
            lp_image_pixel_0 = (lp_sub_image[0] + lp_sub_image[1] + lp_sub_image[2] + lp_sub_image[3]) / 4
            lp_image_pixel_1 = (lp_sub_image[4] + lp_sub_image[5] + lp_sub_image[6] + lp_sub_image[7]) / 4
            lp_image_pixel_2 = (lp_sub_image[8] + lp_sub_image[9] + lp_sub_image[10] + lp_sub_image[11]) / 4
            lp_image_pixel_3 = (lp_sub_image[12] + lp_sub_image[13] + lp_sub_image[14] + lp_sub_image[15]) / 4
            lp_image_pixel_4 = (lp_sub_image[16] + lp_sub_image[17] + lp_sub_image[18] + lp_sub_image[19]) / 4
            lp_image_pixel_5 = (lp_sub_image[20] + lp_sub_image[21] + lp_sub_image[22] + lp_sub_image[23]) / 4
            lp_image_pixel_6 = (lp_sub_image[24] + lp_sub_image[25] + lp_sub_image[26] + lp_sub_image[27]) / 4
            lp_image_pixel_7 = (lp_sub_image[28] + lp_sub_image[29] + lp_sub_image[30] + lp_sub_image[31]) / 4
            lp_image_pixel_8 = (lp_sub_image[32] + lp_sub_image[33] + lp_sub_image[34] + lp_sub_image[35]) / 4
            lp_image_pixel_9 = (lp_sub_image[36] + lp_sub_image[37] + lp_sub_image[38] + lp_sub_image[39]) / 4
            lp_image_pixel_10 = (lp_sub_image[40] + lp_sub_image[41] + lp_sub_image[42] + lp_sub_image[43]) / 4
            lp_image_pixel_11 = (lp_sub_image[44] + lp_sub_image[45] + lp_sub_image[46] + lp_sub_image[47]) / 4

            plane = pl.Plane(galaxies=[galaxy_light], grid_stack=padded_grid_stack)

            assert plane.image_plane_image_for_simulation.shape == (3, 4)
            assert (plane.image_plane_image_for_simulation[0, 0] == lp_image_pixel_0).all()
            assert (plane.image_plane_image_for_simulation[0, 1] == lp_image_pixel_1).all()
            assert (plane.image_plane_image_for_simulation[0, 2] == lp_image_pixel_2).all()
            assert (plane.image_plane_image_for_simulation[0, 3] == lp_image_pixel_3).all()
            assert (plane.image_plane_image_for_simulation[1, 0] == lp_image_pixel_4).all()
            assert (plane.image_plane_image_for_simulation[1, 1] == lp_image_pixel_5).all()
            assert (plane.image_plane_image_for_simulation[1, 2] == lp_image_pixel_6).all()
            assert (plane.image_plane_image_for_simulation[1, 3] == lp_image_pixel_7).all()
            assert (plane.image_plane_image_for_simulation[2, 0] == lp_image_pixel_8).all()
            assert (plane.image_plane_image_for_simulation[2, 1] == lp_image_pixel_9).all()
            assert (plane.image_plane_image_for_simulation[2, 2] == lp_image_pixel_10).all()
            assert (plane.image_plane_image_for_simulation[2, 3] == lp_image_pixel_11).all()

    class TestBlurringImage:

        def test__image_from_plane__same_as_its_light_profile_image(self, data_grid_stack, galaxy_light):

            lp = galaxy_light.light_profiles[0]

            lp_blurring_image = lp.intensities_from_grid(data_grid_stack.blurring)

            plane = pl.Plane(galaxies=[galaxy_light], grid_stack=data_grid_stack)

            assert (plane.image_plane_blurring_image_1d == lp_blurring_image).all()

        def test__same_as_above__use_multiple_galaxies(self, data_grid_stack):
            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.blurring[1] = np.array([2.0, 2.0])

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
            g1 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=2.0))

            lp0 = g0.light_profiles[0]
            lp1 = g1.light_profiles[0]

            lp0_blurring_image = lp0.intensities_from_grid(data_grid_stack.blurring)
            lp1_blurring_image = lp1.intensities_from_grid(data_grid_stack.blurring)

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.image_plane_blurring_image_1d == lp0_blurring_image + lp1_blurring_image).all()

        def test__image_from_plane__same_as_its_galaxy_image(self, data_grid_stack, galaxy_light):

            galaxy_image = pl.intensities_from_grid(data_grid_stack.blurring, galaxies=[galaxy_light])

            plane = pl.Plane(galaxies=[galaxy_light], grid_stack=data_grid_stack)

            assert (plane.image_plane_blurring_image_1d == galaxy_image).all()

        def test__same_as_above_galaxies___use_multiple_galaxies(self, data_grid_stack):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.blurring[1] = np.array([2.0, 2.0])

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
            g1 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=2.0))

            g0_image = pl.intensities_from_grid(data_grid_stack.blurring, galaxies=[g0])
            g1_image = pl.intensities_from_grid(data_grid_stack.blurring, galaxies=[g1])

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.image_plane_blurring_image_1d == g0_image + g1_image).all()

    class TestSurfaceDensity:

        def test__surface_density_from_plane__same_as_its_mass_profile(self, data_grid_stack, galaxy_mass):

            mp = galaxy_mass.mass_profiles[0]

            mp_sub_image = mp.surface_density_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp_image_pixel_0 = (mp_sub_image[0] + mp_sub_image[1] + mp_sub_image[2] + mp_sub_image[3]) / 4
            mp_image_pixel_1 = (mp_sub_image[4] + mp_sub_image[5] + mp_sub_image[6] + mp_sub_image[7]) / 4

            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack)

            assert (plane.surface_density[1,1] == mp_image_pixel_0).all()
            assert (plane.surface_density[1,2] == mp_image_pixel_1).all()

        def test__same_as_above__use_multiple_galaxies(self, data_grid_stack):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=2.0))

            mp0 = g0.mass_profiles[0]
            mp1 = g1.mass_profiles[0]

            mp0_sub_image = mp0.surface_density_from_grid(data_grid_stack.sub.unlensed_grid)
            mp1_sub_image = mp1.surface_density_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp0_image_pixel_0 = (mp0_sub_image[0] + mp0_sub_image[1] + mp0_sub_image[2] + mp0_sub_image[3]) / 4
            mp0_image_pixel_1 = (mp0_sub_image[4] + mp0_sub_image[5] + mp0_sub_image[6] + mp0_sub_image[7]) / 4
            mp1_image_pixel_0 = (mp1_sub_image[0] + mp1_sub_image[1] + mp1_sub_image[2] + mp1_sub_image[3]) / 4
            mp1_image_pixel_1 = (mp1_sub_image[4] + mp1_sub_image[5] + mp1_sub_image[6] + mp1_sub_image[7]) / 4

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.surface_density[1,1] == mp0_image_pixel_0 + mp1_image_pixel_0).all()
            assert (plane.surface_density[1,2] == mp0_image_pixel_1 + mp1_image_pixel_1).all()

        def test__surface_density__same_as_its_galaxy(self, data_grid_stack, galaxy_mass):

            galaxy_surface_density = pl.surface_density_from_grid(data_grid_stack.sub.unlensed_grid,
                                                                  galaxies=[galaxy_mass])

            galaxy_surface_density = data_grid_stack.regular.scaled_array_from_array_1d(galaxy_surface_density)

            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack)

            assert (plane.surface_density == galaxy_surface_density).all()

        def test__same_as_above_galaxies___use_multiple_galaxies(self, data_grid_stack):

            g0 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=2.0))

            g0_surface_density = pl.surface_density_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[g0])
            g1_surface_density = pl.surface_density_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[g1])

            g0_surface_density = data_grid_stack.regular.scaled_array_from_array_1d(g0_surface_density)
            g1_surface_density = data_grid_stack.regular.scaled_array_from_array_1d(g1_surface_density)

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.surface_density == g0_surface_density + g1_surface_density).all()

    class TestPotential:

        def test__potential_from_plane__same_as_its_mass_profile(self, data_grid_stack, galaxy_mass):
            mp = galaxy_mass.mass_profiles[0]

            mp_sub_potential = mp.potential_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp_potential_pixel_0 = (mp_sub_potential[0] + mp_sub_potential[1] + mp_sub_potential[2] + mp_sub_potential
                [3]) / 4
            mp_potential_pixel_1 = (mp_sub_potential[4] + mp_sub_potential[5] + mp_sub_potential[6] + mp_sub_potential
                [7]) / 4

            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack)

            assert (plane.potential[1,1] == mp_potential_pixel_0).all()
            assert (plane.potential[1,2] == mp_potential_pixel_1).all()

        def test__same_as_above__use_multiple_galaxies(self, data_grid_stack):
            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub.unlensed_grid[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=2.0))

            mp0 = g0.mass_profiles[0]
            mp1 = g1.mass_profiles[0]

            mp0_sub_potential = mp0.potential_from_grid(data_grid_stack.sub.unlensed_grid)
            mp1_sub_potential = mp1.potential_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp0_potential_pixel_0 = (mp0_sub_potential[0] + mp0_sub_potential[1] + mp0_sub_potential[2] + mp0_sub_potential[3]) / 4
            mp0_potential_pixel_1 = (mp0_sub_potential[4] + mp0_sub_potential[5] + mp0_sub_potential[6] + mp0_sub_potential[7]) / 4
            mp1_potential_pixel_0 = (mp1_sub_potential[0] + mp1_sub_potential[1] + mp1_sub_potential[2] + mp1_sub_potential[3]) / 4
            mp1_potential_pixel_1 = (mp1_sub_potential[4] + mp1_sub_potential[5] + mp1_sub_potential[6] + mp1_sub_potential[7]) / 4

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.potential[1,1] == mp0_potential_pixel_0 + mp1_potential_pixel_0).all()
            assert (plane.potential[1,2] == mp0_potential_pixel_1 + mp1_potential_pixel_1).all()

        def test__potential__same_as_its_galaxy(self, data_grid_stack, galaxy_mass):
            galaxy_potential = pl.potential_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[galaxy_mass])

            galaxy_potential = data_grid_stack.regular.scaled_array_from_array_1d(galaxy_potential)

            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack)

            assert (plane.potential == galaxy_potential).all()

        def test__same_as_above_galaxies___use_multiple_galaxies(self, data_grid_stack):
            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub.unlensed_grid[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=2.0))

            g0_potential = pl.potential_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[g0])
            g1_potential = pl.potential_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[g1])

            g0_potential = data_grid_stack.regular.scaled_array_from_array_1d(g0_potential)
            g1_potential = data_grid_stack.regular.scaled_array_from_array_1d(g1_potential)

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.potential == g0_potential + g1_potential).all()

    class TestDeflections:

        def test__deflections_from_plane__same_as_its_mass_profile(self, data_grid_stack, galaxy_mass):

            mp = galaxy_mass.mass_profiles[0]

            mp_sub_image = mp.deflections_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp_image_pixel_0x = (mp_sub_image[0 ,0] + mp_sub_image[1 ,0] + mp_sub_image[2 ,0] + mp_sub_image[3 ,0]) / 4
            mp_image_pixel_1x = (mp_sub_image[4 ,0] + mp_sub_image[5 ,0] + mp_sub_image[6 ,0] + mp_sub_image[7 ,0]) / 4
            mp_image_pixel_0y = (mp_sub_image[0 ,1] + mp_sub_image[1 ,1] + mp_sub_image[2 ,1] + mp_sub_image[3 ,1]) / 4
            mp_image_pixel_1y = (mp_sub_image[4 ,1] + mp_sub_image[5 ,1] + mp_sub_image[6 ,1] + mp_sub_image[7 ,1]) / 4

            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack)

            assert (plane.deflections_1d[0 , 0] == mp_image_pixel_0x).all()
            assert (plane.deflections_1d[0 , 1] == mp_image_pixel_0y).all()
            assert (plane.deflections_1d[1 , 0] == mp_image_pixel_1x).all()
            assert (plane.deflections_1d[1 , 1] == mp_image_pixel_1y).all()
            assert (plane.deflections_y ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 0])).all()
            assert (plane.deflections_x ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 1])).all()

        def test__same_as_above__use_multiple_galaxies(self, data_grid_stack):
            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub.unlensed_grid[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=2.0))

            mp0 = g0.mass_profiles[0]
            mp1 = g1.mass_profiles[0]

            mp0_sub_image = mp0.deflections_from_grid(data_grid_stack.sub.unlensed_grid)
            mp1_sub_image = mp1.deflections_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp0_image_pixel_0x = (mp0_sub_image[0 ,0] + mp0_sub_image[1 ,0] + mp0_sub_image[2 ,0] + mp0_sub_image
                [3 ,0]) / 4
            mp0_image_pixel_1x = (mp0_sub_image[4 ,0] + mp0_sub_image[5 ,0] + mp0_sub_image[6 ,0] + mp0_sub_image
                [7 ,0]) / 4
            mp0_image_pixel_0y = (mp0_sub_image[0 ,1] + mp0_sub_image[1 ,1] + mp0_sub_image[2 ,1] + mp0_sub_image
                [3 ,1]) / 4
            mp0_image_pixel_1y = (mp0_sub_image[4 ,1] + mp0_sub_image[5 ,1] + mp0_sub_image[6 ,1] + mp0_sub_image
                [7 ,1]) / 4

            mp1_image_pixel_0x = (mp1_sub_image[0 ,0] + mp1_sub_image[1 ,0] + mp1_sub_image[2 ,0] + mp1_sub_image
                [3 ,0]) / 4
            mp1_image_pixel_1x = (mp1_sub_image[4 ,0] + mp1_sub_image[5 ,0] + mp1_sub_image[6 ,0] + mp1_sub_image
                [7 ,0]) / 4
            mp1_image_pixel_0y = (mp1_sub_image[0 ,1] + mp1_sub_image[1 ,1] + mp1_sub_image[2 ,1] + mp1_sub_image
                [3 ,1]) / 4
            mp1_image_pixel_1y = (mp1_sub_image[4 ,1] + mp1_sub_image[5 ,1] + mp1_sub_image[6 ,1] + mp1_sub_image
                [7 ,1]) / 4

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.deflections_1d[0 , 0] == mp0_image_pixel_0x + mp1_image_pixel_0x).all()
            assert (plane.deflections_1d[1 , 0] == mp0_image_pixel_1x + mp1_image_pixel_1x).all()
            assert (plane.deflections_1d[0 , 1] == mp0_image_pixel_0y + mp1_image_pixel_0y).all()
            assert (plane.deflections_1d[1 , 1] == mp0_image_pixel_1y + mp1_image_pixel_1y).all()
            assert (plane.deflections_y ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 0])).all()
            assert (plane.deflections_x ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 1])).all()

        def test__deflections__same_as_its_galaxy(self, data_grid_stack, galaxy_mass):

            galaxy_deflections = pl.deflections_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[galaxy_mass])

            plane = pl.Plane(galaxies=[galaxy_mass], grid_stack=data_grid_stack)

            assert (plane.deflections_1d == galaxy_deflections).all()
            assert (plane.deflections_y ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 0])).all()
            assert (plane.deflections_x ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 1])).all()

        def test__same_as_above_galaxies___use_multiple_galaxies(self, data_grid_stack):
            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub.unlensed_grid[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=1.0))
            g1 = g.Galaxy(mass_profile=mp.SphericalIsothermal(einstein_radius=2.0))

            g0_deflections = pl.deflections_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[g0])
            g1_deflections = pl.deflections_from_grid(data_grid_stack.sub.unlensed_grid, galaxies=[g1])

            plane = pl.Plane(galaxies=[g0, g1], grid_stack=data_grid_stack)

            assert (plane.deflections_1d == g0_deflections + g1_deflections).all()
            assert (plane.deflections_y ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 0])).all()
            assert (plane.deflections_x ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 1])).all()

    class TestMapper:

        def test__no_galaxies_with_pixelizations_in_plane__returns_none(self, data_grid_stack):
            galaxy_no_pix = g.Galaxy()

            plane = pl.Plane(galaxies=[galaxy_no_pix], grid_stack=data_grid_stack, border=[MockBorders()])

            assert plane.mapper is None

        def test__1_galaxy_in_plane__it_has_pixelization__returns_mapper(self, data_grid_stack):
            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))

            plane = pl.Plane(galaxies=[galaxy_pix], grid_stack=data_grid_stack, border=[MockBorders()])

            assert plane.mapper == 1

        def test__2_galaxies_in_plane__1_has_pixelization__extracts_reconstructor(self, data_grid_stack):
            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_no_pix = g.Galaxy()

            plane = pl.Plane(galaxies=[galaxy_no_pix, galaxy_pix], grid_stack=data_grid_stack, border=[MockBorders()])

            assert plane.mapper == 1

        def test__plane_has_no_border__still_returns_mapper(self, data_grid_stack):

            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_no_pix = g.Galaxy()

            plane = pl.Plane(galaxies=[galaxy_no_pix, galaxy_pix], grid_stack=data_grid_stack)

            assert plane.mapper == 1

        def test__2_galaxies_in_plane__both_have_pixelization__raises_error(self, data_grid_stack):
            galaxy_pix_0 = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_pix_1 = g.Galaxy(pixelization=MockPixelization(value=2), regularization=MockRegularization(value=0))

            plane = pl.Plane(galaxies=[galaxy_pix_0, galaxy_pix_1], grid_stack=data_grid_stack, border=[MockBorders()])

            with pytest.raises(exc.PixelizationException):
                plane.mapper

    class TestRegularization:

        def test__no_galaxies_with_pixelizations_in_plane__returns_none(self, data_grid_stack):

            galaxy_no_pix = g.Galaxy()

            plane = pl.Plane(galaxies=[galaxy_no_pix], grid_stack=data_grid_stack, border=MockBorders())

            assert plane.regularization is None

        def test__1_galaxy_in_plane__it_has_pixelization__returns_mapper(self, data_grid_stack):
            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))

            plane = pl.Plane(galaxies=[galaxy_pix], grid_stack=data_grid_stack, border=MockBorders())

            assert plane.regularization.value == 0

        def test__2_galaxies_in_plane__1_has_pixelization__extracts_reconstructor(self, data_grid_stack):
            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_no_pix = g.Galaxy()

            plane = pl.Plane(galaxies=[galaxy_no_pix, galaxy_pix], grid_stack=data_grid_stack, border=MockBorders())

            assert plane.regularization.value == 0

        def test__2_galaxies_in_plane__both_have_pixelization__raises_error(self, data_grid_stack):
            galaxy_pix_0 = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_pix_1 = g.Galaxy(pixelization=MockPixelization(value=2), regularization=MockRegularization(value=0))

            plane = pl.Plane(galaxies=[galaxy_pix_0, galaxy_pix_1], grid_stack=data_grid_stack, border=MockBorders())

            with pytest.raises(exc.PixelizationException):
                plane.regularization

    class TestPlaneImage:

        def test__3x3_grid__extracts_max_min_coordinates__ignores_other_coordinates_more_central(self, data_grid_stack):

            data_grid_stack.regular[1] = np.array([2.0, 2.0])

            galaxy = g.Galaxy(light=lp.EllipticalSersic(intensity=1.0))

            plane = pl.Plane(galaxies=[galaxy], grid_stack=data_grid_stack, compute_deflections=False)

            plane_image_from_func = pl.plane_image_from_grid_and_galaxies(shape=(3, 4),
                                                                          grid_stack=data_grid_stack.regular,
                                                                          galaxies=[galaxy])

            assert (plane_image_from_func == plane.plane_image).all()

        def test__ensure_index_of_plane_image_has_negative_arcseconds_at_start(self, data_grid_stack):
            # The grid coordinates -2.0 -> 2.0 mean a plane of shape (5,5) has arc second coordinates running over
            # -1.6, -0.8, 0.0, 0.8, 1.6. The origin -1.6, -1.6 of the model_galaxy means its brighest pixel should be
            # index 0 of the 1D grid and (0,0) of the 2d plane datas_.

            msk = mask.Mask(array=np.full((5, 5), False), pixel_scale=1.0)

            data_grid_stack.regular = grids.RegularGrid(np.array([[-2.0, -2.0], [2.0, 2.0]]), mask=msk)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(1.6, -1.6), intensity=1.0))
            plane = pl.Plane(galaxies=[g0], grid_stack=data_grid_stack)

            assert plane.plane_image.shape == (5, 5)
            assert np.unravel_index(plane.plane_image.argmax(), plane.plane_image.shape) == (0, 0)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(1.6, 1.6), intensity=1.0))
            plane = pl.Plane(galaxies=[g0], grid_stack=data_grid_stack)
            assert np.unravel_index(plane.plane_image.argmax(), plane.plane_image.shape) == (0, 4)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(-1.6, -1.6), intensity=1.0))
            plane = pl.Plane(galaxies=[g0], grid_stack=data_grid_stack)
            assert np.unravel_index(plane.plane_image.argmax(), plane.plane_image.shape) == (4, 0)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(-1.6, 1.6), intensity=1.0))
            plane = pl.Plane(galaxies=[g0], grid_stack=data_grid_stack)
            assert np.unravel_index(plane.plane_image.argmax(), plane.plane_image.shape) == (4, 4)

        def test__compute_xticks_from_image_grid_correctly(self):

            plane_image = pl.PlaneImage(array=np.ones((3,3)), pixel_scales=(5.0, 1.0), grid=None)
            assert plane_image.xticks == pytest.approx(np.array([-1.5, -0.5, 0.5, 1.5]), 1e-3)

            plane_image = pl.PlaneImage(array=np.ones((3,3)), pixel_scales=(5.0, 0.5), grid=None)
            assert plane_image.xticks == pytest.approx(np.array([-0.75, -0.25, 0.25, 0.75]), 1e-3)

            plane_image = pl.PlaneImage(array=np.ones((1,6)), pixel_scales=(5.0, 1.0), grid=None)
            assert plane_image.xticks == pytest.approx(np.array([-3.0, -1.0, 1.0, 3.0]), 1e-2)

        def test__compute_yticks_from_image_grid_correctly(self):

            plane_image = pl.PlaneImage(array=np.ones((3,3)), pixel_scales=(1.0, 5.0), grid=None)
            assert plane_image.yticks == pytest.approx(np.array([-1.5, -0.5, 0.5, 1.5]), 1e-3)

            plane_image = pl.PlaneImage(array=np.ones((3,3)), pixel_scales=(0.5, 5.0), grid=None)
            assert plane_image.yticks == pytest.approx(np.array([-0.75, -0.25, 0.25, 0.75]), 1e-3)

            plane_image = pl.PlaneImage(array=np.ones((6,1)), pixel_scales=(1.0, 5.0), grid=None)
            assert plane_image.yticks == pytest.approx(np.array([-3.0, -1.0, 1.0, 3.0]), 1e-2)


class TestPlaneMulti:

    class TestGridsStacksSetup:

        def test__data_grid_stack_setup_for_regular_sub_and_blurring__no_deflections(self, data_grid_stack,
                                                                                     galaxy_mass):
            plane = pl.PlaneStack(galaxies=[galaxy_mass], grid_stacks=[data_grid_stack, data_grid_stack],
                                  compute_deflections=False)

            assert plane.grid_stacks[0].regular == pytest.approx(np.array([[1.0, 1.0], [1.0, 0.0]]), 1e-3)
            assert plane.grid_stacks[0].sub == pytest.approx(np.array([[1.0, 1.0], [1.0, 0.0], [1.0, 1.0], [1.0, 0.0],
                                                                      [-1.0, 2.0], [-1.0, 4.0], [1.0, 2.0],
                                                                      [1.0, 4.0]]), 1e-3)
            assert plane.grid_stacks[0].blurring == pytest.approx(
                np.array([[1.0, 0.0], [-6.0, -3.0], [-6.0, 3.0], [-6.0, 9.0],
                          [0.0, -9.0], [0.0, 9.0],
                          [6.0, -9.0], [6.0, -3.0], [6.0, 3.0], [6.0, 9.0]]), 1e-3)

            assert plane.grid_stacks[1].regular == pytest.approx(np.array([[1.0, 1.0], [1.0, 0.0]]), 1e-3)
            assert plane.grid_stacks[1].sub == pytest.approx(np.array([[1.0, 1.0], [1.0, 0.0], [1.0, 1.0], [1.0, 0.0],
                                                                      [-1.0, 2.0], [-1.0, 4.0], [1.0, 2.0],
                                                                      [1.0, 4.0]]), 1e-3)
            assert plane.grid_stacks[1].blurring == pytest.approx(
                np.array([[1.0, 0.0], [-6.0, -3.0], [-6.0, 3.0], [-6.0, 9.0],
                          [0.0, -9.0], [0.0, 9.0],
                          [6.0, -9.0], [6.0, -3.0], [6.0, 3.0], [6.0, 9.0]]), 1e-3)

            assert plane.deflection_stacks == None

        def test__same_as_above_but_test_deflections(self, data_grid_stack, galaxy_mass):
            plane = pl.PlaneStack(galaxies=[galaxy_mass], grid_stacks=[data_grid_stack, data_grid_stack],
                                  compute_deflections=True)

            sub_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.sub)
            blurring_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.blurring)

            assert plane.deflection_stacks[0].regular == pytest.approx(np.array([[0.707, 0.707], [1.0, 0.0]]), 1e-3)
            assert (plane.deflection_stacks[0].sub == sub_galaxy_deflections).all()
            assert (plane.deflection_stacks[0].blurring == blurring_galaxy_deflections).all()

            assert plane.deflection_stacks[1].regular == pytest.approx(np.array([[0.707, 0.707], [1.0, 0.0]]), 1e-3)
            assert (plane.deflection_stacks[1].sub == sub_galaxy_deflections).all()
            assert (plane.deflection_stacks[1].blurring == blurring_galaxy_deflections).all()

        def test__same_as_above__x2_galaxy_in_plane__or_galaxy_x2_sis__deflections_double(self, data_grid_stack,
                                                                                          galaxy_mass,
                                                                                          galaxy_mass_x2):
            plane = pl.PlaneStack(galaxies=[galaxy_mass_x2], grid_stacks=[data_grid_stack, data_grid_stack],
                                  compute_deflections=True)

            sub_galaxy_deflections = galaxy_mass_x2.deflections_from_grid(data_grid_stack.sub)
            blurring_galaxy_deflections = galaxy_mass_x2.deflections_from_grid(data_grid_stack.blurring)

            assert plane.deflection_stacks[0].regular == pytest.approx(np.array([[2.0 * 0.707, 2.0 * 0.707], [2.0, 0.0]]),
                                                                       1e-3)
            assert (plane.deflection_stacks[0].sub == sub_galaxy_deflections).all()
            assert (plane.deflection_stacks[0].blurring == blurring_galaxy_deflections).all()

            assert plane.deflection_stacks[1].regular == pytest.approx(np.array([[2.0 * 0.707, 2.0 * 0.707], [2.0, 0.0]]),
                                                                       1e-3)
            assert (plane.deflection_stacks[1].sub == sub_galaxy_deflections).all()
            assert (plane.deflection_stacks[1].blurring == blurring_galaxy_deflections).all()

            plane = pl.PlaneStack(galaxies=[galaxy_mass, galaxy_mass], grid_stacks=[data_grid_stack, data_grid_stack],
                                  compute_deflections=True)

            sub_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.sub)
            blurring_galaxy_deflections = galaxy_mass.deflections_from_grid(data_grid_stack.blurring)

            assert plane.deflection_stacks[0].regular == pytest.approx(np.array([[2.0 * 0.707, 2.0 * 0.707], [2.0, 0.0]]),
                                                                       1e-3)
            assert (plane.deflection_stacks[0].sub == 2.0 * sub_galaxy_deflections).all()
            assert (plane.deflection_stacks[0].blurring == 2.0 * blurring_galaxy_deflections).all()

            assert plane.deflection_stacks[1].regular == pytest.approx(np.array([[2.0 * 0.707, 2.0 * 0.707], [2.0, 0.0]]),
                                                                       1e-3)
            assert (plane.deflection_stacks[1].sub == 2.0 * sub_galaxy_deflections).all()
            assert (plane.deflection_stacks[1].blurring == 2.0 * blurring_galaxy_deflections).all()

    class TestProperties:

        def test__total_images(self, data_grid_stack):

            plane = pl.PlaneStack(galaxies=[g.Galaxy()], grid_stacks=[data_grid_stack])
            assert plane.total_grid_stacks == 1

            plane = pl.PlaneStack(galaxies=[g.Galaxy()], grid_stacks=[data_grid_stack, data_grid_stack])
            assert plane.total_grid_stacks == 2

            plane = pl.PlaneStack(galaxies=[g.Galaxy()], grid_stacks=[data_grid_stack, data_grid_stack, data_grid_stack])
            assert plane.total_grid_stacks == 3

        def test__padded_grid_in__tracer_has_padded_grid_property(self, data_grid_stack, padded_grid_stack, galaxy_light):

            plane = pl.PlaneStack(grid_stacks=[data_grid_stack], galaxies=[galaxy_light])
            assert plane.has_padded_grid_stack == False

            plane = pl.PlaneStack(grid_stacks=[padded_grid_stack], galaxies=[galaxy_light])
            assert plane.has_padded_grid_stack == True

            plane = pl.PlaneStack(grid_stacks=[data_grid_stack, padded_grid_stack], galaxies=[galaxy_light])
            assert plane.has_padded_grid_stack == True

    class TestImages:

        def test__images_from_plane__same_as_light_profile_images(self, data_grid_stack, galaxy_light):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub[5] = np.array([2.0, 2.0])

            lp = galaxy_light.light_profiles[0]

            lp_sub_image = lp.intensities_from_grid(data_grid_stack.sub)

            # Perform sub gridding average manually
            lp_image_pixel_0 = (lp_sub_image[0] + lp_sub_image[1] + lp_sub_image[2] + lp_sub_image[3]) / 4
            lp_image_pixel_1 = (lp_sub_image[4] + lp_sub_image[5] + lp_sub_image[6] + lp_sub_image[7]) / 4

            plane = pl.PlaneStack(galaxies=[galaxy_light], grid_stacks=[data_grid_stack])

            assert (plane.image_plane_images_1d[0][0] == lp_image_pixel_0).all()
            assert (plane.image_plane_images_1d[0][1] == lp_image_pixel_1).all()
            assert (plane.image_plane_images[0] ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_images_1d[0])).all()

        def test__image_from_plane__same_as_galaxy_images(self, data_grid_stack, galaxy_light):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub[5] = np.array([2.0, 2.0])

            galaxy_image = pl.intensities_from_grid(data_grid_stack.sub, galaxies=[galaxy_light])

            plane = pl.PlaneStack(galaxies=[galaxy_light], grid_stacks=[data_grid_stack, data_grid_stack])

            assert (plane.image_plane_images_1d[0] == galaxy_image).all()
            assert (plane.image_plane_images[0] ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_images_1d[0])).all()

            assert (plane.image_plane_images_1d[1] == galaxy_image).all()
            assert (plane.image_plane_images[1] ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_images_1d[1])).all()

        def test__image_plane_image_of_galaxies__use_multiple_grids__get_multiple_images(self, data_grid_stack,
                                                                                         data_grid_stack_1):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.sub[5] = np.array([2.0, 2.0])

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
            g1 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=2.0))

            plane = pl.PlaneStack(galaxies=[g0, g1], grid_stacks=[data_grid_stack, data_grid_stack_1])

            g0_image_grid_0 = pl.intensities_from_grid(data_grid_stack.sub, galaxies=[g0])
            g1_image_grid_0 = pl.intensities_from_grid(data_grid_stack.sub, galaxies=[g1])

            assert (plane.image_plane_images_1d[0] == g0_image_grid_0 + g1_image_grid_0).all()
            assert (plane.image_plane_images[0] ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_images_1d[0])).all()

            assert (plane.image_plane_images_1d_of_galaxies[0][0] == g0_image_grid_0).all()
            assert (plane.image_plane_images_1d_of_galaxies[0][1] == g1_image_grid_0).all()

            g0_image_grid_1 = pl.intensities_from_grid(data_grid_stack_1.sub, galaxies=[g0])
            g1_image_grid_1 = pl.intensities_from_grid(data_grid_stack_1.sub, galaxies=[g1])

            assert (plane.image_plane_images_1d[1] == g0_image_grid_1 + g1_image_grid_1).all()
            assert (plane.image_plane_images[1] ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.image_plane_images_1d[1])).all()

            assert (plane.image_plane_images_1d_of_galaxies[1][0] == g0_image_grid_1).all()
            assert (plane.image_plane_images_1d_of_galaxies[1][1] == g1_image_grid_1).all()

        def test__padded_grid_stack_in__image_plane_image_is_padded(self, padded_grid_stack, galaxy_light):
            
            lp = galaxy_light.light_profiles[0]

            lp_sub_image = lp.intensities_from_grid(padded_grid_stack.sub)

            # Perform sub gridding average manually
            lp_image_pixel_0 = (lp_sub_image[0] + lp_sub_image[1] + lp_sub_image[2] + lp_sub_image[3]) / 4
            lp_image_pixel_1 = (lp_sub_image[4] + lp_sub_image[5] + lp_sub_image[6] + lp_sub_image[7]) / 4
            lp_image_pixel_2 = (lp_sub_image[8] + lp_sub_image[9] + lp_sub_image[10] + lp_sub_image[11]) / 4
            lp_image_pixel_3 = (lp_sub_image[12] + lp_sub_image[13] + lp_sub_image[14] + lp_sub_image[15]) / 4
            lp_image_pixel_4 = (lp_sub_image[16] + lp_sub_image[17] + lp_sub_image[18] + lp_sub_image[19]) / 4
            lp_image_pixel_5 = (lp_sub_image[20] + lp_sub_image[21] + lp_sub_image[22] + lp_sub_image[23]) / 4
            lp_image_pixel_6 = (lp_sub_image[24] + lp_sub_image[25] + lp_sub_image[26] + lp_sub_image[27]) / 4
            lp_image_pixel_7 = (lp_sub_image[28] + lp_sub_image[29] + lp_sub_image[30] + lp_sub_image[31]) / 4
            lp_image_pixel_8 = (lp_sub_image[32] + lp_sub_image[33] + lp_sub_image[34] + lp_sub_image[35]) / 4
            lp_image_pixel_9 = (lp_sub_image[36] + lp_sub_image[37] + lp_sub_image[38] + lp_sub_image[39]) / 4
            lp_image_pixel_10 = (lp_sub_image[40] + lp_sub_image[41] + lp_sub_image[42] + lp_sub_image[43]) / 4
            lp_image_pixel_11 = (lp_sub_image[44] + lp_sub_image[45] + lp_sub_image[46] + lp_sub_image[47]) / 4

            plane = pl.PlaneStack(galaxies=[galaxy_light], grid_stacks=[padded_grid_stack, padded_grid_stack])

            assert plane.image_plane_images_for_simulation[0].shape == (3, 4)
            assert (plane.image_plane_images_for_simulation[0][0, 0] == lp_image_pixel_0).all()
            assert (plane.image_plane_images_for_simulation[0][0, 1] == lp_image_pixel_1).all()
            assert (plane.image_plane_images_for_simulation[0][0, 2] == lp_image_pixel_2).all()
            assert (plane.image_plane_images_for_simulation[0][0, 3] == lp_image_pixel_3).all()
            assert (plane.image_plane_images_for_simulation[0][1, 0] == lp_image_pixel_4).all()
            assert (plane.image_plane_images_for_simulation[0][1, 1] == lp_image_pixel_5).all()
            assert (plane.image_plane_images_for_simulation[0][1, 2] == lp_image_pixel_6).all()
            assert (plane.image_plane_images_for_simulation[0][1, 3] == lp_image_pixel_7).all()
            assert (plane.image_plane_images_for_simulation[0][2, 0] == lp_image_pixel_8).all()
            assert (plane.image_plane_images_for_simulation[0][2, 1] == lp_image_pixel_9).all()
            assert (plane.image_plane_images_for_simulation[0][2, 2] == lp_image_pixel_10).all()
            assert (plane.image_plane_images_for_simulation[0][2, 3] == lp_image_pixel_11).all()

            assert plane.image_plane_images_for_simulation[1].shape == (3, 4)
            assert (plane.image_plane_images_for_simulation[1][0, 0] == lp_image_pixel_0).all()
            assert (plane.image_plane_images_for_simulation[1][0, 1] == lp_image_pixel_1).all()
            assert (plane.image_plane_images_for_simulation[1][0, 2] == lp_image_pixel_2).all()
            assert (plane.image_plane_images_for_simulation[1][0, 3] == lp_image_pixel_3).all()
            assert (plane.image_plane_images_for_simulation[1][1, 0] == lp_image_pixel_4).all()
            assert (plane.image_plane_images_for_simulation[1][1, 1] == lp_image_pixel_5).all()
            assert (plane.image_plane_images_for_simulation[1][1, 2] == lp_image_pixel_6).all()
            assert (plane.image_plane_images_for_simulation[1][1, 3] == lp_image_pixel_7).all()
            assert (plane.image_plane_images_for_simulation[1][2, 0] == lp_image_pixel_8).all()
            assert (plane.image_plane_images_for_simulation[1][2, 1] == lp_image_pixel_9).all()
            assert (plane.image_plane_images_for_simulation[1][2, 2] == lp_image_pixel_10).all()
            assert (plane.image_plane_images_for_simulation[1][2, 3] == lp_image_pixel_11).all()

    class TestBlurringImages:

        def test__images_from_plane__same_as_their_light_profile(self, data_grid_stack, data_grid_stack_1,
                                                                  galaxy_light):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.blurring[1] = np.array([2.0, 2.0])

            lp = galaxy_light.light_profiles[0]

            lp_blurring_image = lp.intensities_from_grid(data_grid_stack.blurring)
            lp_blurring_image_1 = lp.intensities_from_grid(data_grid_stack_1.blurring)

            plane = pl.PlaneStack(galaxies=[galaxy_light], grid_stacks=[data_grid_stack, data_grid_stack_1])

            assert (plane.image_plane_blurring_images_1d[0] == lp_blurring_image).all()
            assert (plane.image_plane_blurring_images_1d[1] == lp_blurring_image_1).all()

        def test__same_as_above_but_for_galaxies(self, data_grid_stack, data_grid_stack_1, galaxy_light):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.blurring[1] = np.array([2.0, 2.0])

            galaxy_image = pl.intensities_from_grid(data_grid_stack.blurring, galaxies=[galaxy_light])
            galaxy_image_1 = pl.intensities_from_grid(data_grid_stack_1.blurring, galaxies=[galaxy_light])

            plane = pl.PlaneStack(galaxies=[galaxy_light], grid_stacks=[data_grid_stack, data_grid_stack_1])

            assert (plane.image_plane_blurring_images_1d[0] == galaxy_image).all()
            assert (plane.image_plane_blurring_images_1d[1] == galaxy_image_1).all()

        def test__same_as_above__multiple_galaxies(self, data_grid_stack, data_grid_stack_1):

            # Overwrite one value so intensity in each pixel is different
            data_grid_stack.blurring[1] = np.array([2.0, 2.0])
            data_grid_stack_1.blurring[1] = np.array([2.0, 2.0])

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
            g1 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=2.0))

            g0_image_grid_0 = pl.intensities_from_grid(data_grid_stack.blurring, galaxies=[g0])
            g1_image_grid_0 = pl.intensities_from_grid(data_grid_stack.blurring, galaxies=[g1])

            plane = pl.PlaneStack(galaxies=[g0, g1], grid_stacks=[data_grid_stack, data_grid_stack_1])

            assert (plane.image_plane_blurring_images_1d[0] == g0_image_grid_0 + g1_image_grid_0).all()

            g0_image_grid_1 = pl.intensities_from_grid(data_grid_stack_1.blurring, galaxies=[g0])
            g1_image_grid_1 = pl.intensities_from_grid(data_grid_stack_1.blurring, galaxies=[g1])

            plane = pl.PlaneStack(galaxies=[g0, g1], grid_stacks=[data_grid_stack, data_grid_stack_1])

            assert (plane.image_plane_blurring_images_1d[1] == g0_image_grid_1 + g1_image_grid_1).all()

    class TestSurfaceDensity:

        def test__computes_x1_surface_density__uses_primary_data_grid_stack(self, data_grid_stack, data_grid_stack_1,
                                                                                  galaxy_mass):

            mp = galaxy_mass.mass_profiles[0]

            mp_sub_image = mp.surface_density_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp_image_pixel_0 = (mp_sub_image[0] + mp_sub_image[1] + mp_sub_image[2] + mp_sub_image[3]) / 4
            mp_image_pixel_1 = (mp_sub_image[4] + mp_sub_image[5] + mp_sub_image[6] + mp_sub_image[7]) / 4

            plane = pl.PlaneStack(galaxies=[galaxy_mass], grid_stacks=[data_grid_stack, data_grid_stack_1])

            assert (plane.surface_density[1, 1] == mp_image_pixel_0).all()
            assert (plane.surface_density[1, 2] == mp_image_pixel_1).all()

    class TestPotential:

        def test__computes_x1_potential__uses_primary_data_grid_stack(self, data_grid_stack, data_grid_stack_1,
                                                                      galaxy_mass):

            mp = galaxy_mass.mass_profiles[0]

            mp_sub_image = mp.potential_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp_image_pixel_0 = (mp_sub_image[0] + mp_sub_image[1] + mp_sub_image[2] + mp_sub_image[3]) / 4
            mp_image_pixel_1 = (mp_sub_image[4] + mp_sub_image[5] + mp_sub_image[6] + mp_sub_image[7]) / 4

            plane = pl.PlaneStack(galaxies=[galaxy_mass], grid_stacks=[data_grid_stack, data_grid_stack_1])

            assert (plane.potential[1, 1] == mp_image_pixel_0).all()
            assert (plane.potential[1, 2] == mp_image_pixel_1).all()

    class TestDeflections:

        def test__computes_x1_deflections__uses_primary_data_grid_stack(self, data_grid_stack, data_grid_stack_1,
                                                                        galaxy_mass):

            mp = galaxy_mass.mass_profiles[0]

            mp_sub_image = mp.deflections_from_grid(data_grid_stack.sub.unlensed_grid)

            # Perform sub gridding average manually
            mp_image_pixel_0x = (mp_sub_image[0 ,0] + mp_sub_image[1 ,0] + mp_sub_image[2 ,0] + mp_sub_image[3 ,0]) / 4
            mp_image_pixel_1x = (mp_sub_image[4 ,0] + mp_sub_image[5 ,0] + mp_sub_image[6 ,0] + mp_sub_image[7 ,0]) / 4
            mp_image_pixel_0y = (mp_sub_image[0 ,1] + mp_sub_image[1 ,1] + mp_sub_image[2 ,1] + mp_sub_image[3 ,1]) / 4
            mp_image_pixel_1y = (mp_sub_image[4 ,1] + mp_sub_image[5 ,1] + mp_sub_image[6 ,1] + mp_sub_image[7 ,1]) / 4

            plane = pl.PlaneStack(galaxies=[galaxy_mass], grid_stacks=[data_grid_stack, data_grid_stack_1])

            assert (plane.deflections_1d[0 , 0] == mp_image_pixel_0x).all()
            assert (plane.deflections_1d[0 , 1] == mp_image_pixel_0y).all()
            assert (plane.deflections_1d[1 , 0] == mp_image_pixel_1x).all()
            assert (plane.deflections_1d[1 , 1] == mp_image_pixel_1y).all()
            assert (plane.deflections_y ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 0])).all()
            assert (plane.deflections_x ==
                    data_grid_stack.regular.scaled_array_from_array_1d(plane.deflections_1d[:, 1])).all()

    class TestMapper:

        def test__no_galaxies_with_pixelizations_in_plane__returns_none(self, data_grid_stack):

            galaxy_no_pix = g.Galaxy()

            plane = pl.PlaneStack(galaxies=[galaxy_no_pix], grid_stacks=[data_grid_stack],
                                  borders=[MockBorders()])

            assert plane.mapper is None

        def test__1_galaxy_in_plane__it_has_pixelization__returns_mapper(self, data_grid_stack):
            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))

            plane = pl.PlaneStack(galaxies=[galaxy_pix], grid_stacks=[data_grid_stack],
                                  borders=[MockBorders()])

            assert plane.mapper == 1

        def test__2_galaxies_in_plane__1_has_pixelization__extracts_reconstructor(self, data_grid_stack):
            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_no_pix = g.Galaxy()

            plane = pl.PlaneStack(galaxies=[galaxy_no_pix, galaxy_pix], grid_stacks=[data_grid_stack],
                                  borders=[MockBorders()])

            assert plane.mapper == 1

        def test__plane_has_no_border__still_returns_mapper(self, data_grid_stack):

            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_no_pix = g.Galaxy()

            plane = pl.PlaneStack(galaxies=[galaxy_no_pix, galaxy_pix], grid_stacks=[data_grid_stack])

            assert plane.mapper == 1

        def test__2_galaxies_in_plane__both_have_pixelization__raises_error(self, data_grid_stack):

            galaxy_pix_0 = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_pix_1 = g.Galaxy(pixelization=MockPixelization(value=2), regularization=MockRegularization(value=0))

            plane = pl.PlaneStack(galaxies=[galaxy_pix_0, galaxy_pix_1], grid_stacks=[data_grid_stack],
                                  borders=[MockBorders()])

            with pytest.raises(exc.PixelizationException):
                plane.mapper

    class TestRegularization:

        def test__no_galaxies_with_pixelizations_in_plane__returns_none(self, data_grid_stack):

            galaxy_no_pix = g.Galaxy()

            plane = pl.PlaneStack(galaxies=[galaxy_no_pix], grid_stacks=[data_grid_stack], borders=[MockBorders()])

            assert plane.regularization is None

        def test__1_galaxy_in_plane__it_has_pixelization__returns_mapper(self, data_grid_stack):

            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))

            plane = pl.PlaneStack(galaxies=[galaxy_pix], grid_stacks=[data_grid_stack], borders=[MockBorders()])

            assert plane.regularization.value == 0

        def test__2_galaxies_in_plane__1_has_pixelization__extracts_reconstructor(self, data_grid_stack):

            galaxy_pix = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_no_pix = g.Galaxy()

            plane = pl.PlaneStack(galaxies=[galaxy_no_pix, galaxy_pix], grid_stacks=[data_grid_stack],
                                  borders=[MockBorders()])

            assert plane.regularization.value == 0

        def test__2_galaxies_in_plane__both_have_pixelization__raises_error(self, data_grid_stack):

            galaxy_pix_0 = g.Galaxy(pixelization=MockPixelization(value=1), regularization=MockRegularization(value=0))
            galaxy_pix_1 = g.Galaxy(pixelization=MockPixelization(value=2), regularization=MockRegularization(value=0))

            plane = pl.PlaneStack(galaxies=[galaxy_pix_0, galaxy_pix_1], grid_stacks=[data_grid_stack],
                                  borders=[MockBorders()])

            with pytest.raises(exc.PixelizationException):
                plane.regularization

    class TestPlaneImages:

        def test__x2_data_stacks__x2_plane_images(self, data_grid_stack, data_grid_stack_1):

            data_grid_stack.regular[1] = np.array([2.0, 2.0])

            galaxy = g.Galaxy(light=lp.EllipticalSersic(intensity=1.0))

            plane = pl.PlaneStack(galaxies=[galaxy], grid_stacks=[data_grid_stack, data_grid_stack_1],
                                  compute_deflections=False)

            plane_image_from_func = pl.plane_image_from_grid_and_galaxies(shape=(3, 4),
                                                                          grid_stack=data_grid_stack.regular,
                                                                          galaxies=[galaxy])

            plane_image_from_func_1 = pl.plane_image_from_grid_and_galaxies(shape=(3, 4),
                                                                          grid_stack=data_grid_stack_1.regular,
                                                                          galaxies=[galaxy])

            assert (plane_image_from_func == plane.plane_images[0]).all()
            assert (plane_image_from_func_1 == plane.plane_images[1]).all()

        def test__ensure_index_of_plane_image_has_negative_arcseconds_at_start(self, data_grid_stack):

            # The grid coordinates -2.0 -> 2.0 mean a plane of shape (5,5) has arc second coordinates running over
            # -1.6, -0.8, 0.0, 0.8, 1.6. The origin -1.6, -1.6 of the model_galaxy means its brighest pixel should be
            # index 0 of the 1D grid and (0,0) of the 2d plane datas_.

            msk = mask.Mask(array=np.full((5, 5), False), pixel_scale=1.0)

            data_grid_stack.regular = grids.RegularGrid(np.array([[-2.0, -2.0], [2.0, 2.0]]), mask=msk)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(1.6, -1.6), intensity=1.0))
            plane = pl.PlaneStack(galaxies=[g0], grid_stacks=[data_grid_stack])

            assert plane.plane_images[0].shape == (5, 5)
            assert np.unravel_index(plane.plane_images[0].argmax(), plane.plane_images[0].shape) == (0, 0)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(1.6, 1.6), intensity=1.0))
            plane = pl.PlaneStack(galaxies=[g0], grid_stacks=[data_grid_stack])
            assert np.unravel_index(plane.plane_images[0].argmax(), plane.plane_images[0].shape) == (0, 4)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(-1.6, -1.6), intensity=1.0))
            plane = pl.PlaneStack(galaxies=[g0], grid_stacks=[data_grid_stack])
            assert np.unravel_index(plane.plane_images[0].argmax(), plane.plane_images[0].shape) == (4, 0)

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(centre=(-1.6, 1.6), intensity=1.0))
            plane = pl.PlaneStack(galaxies=[g0], grid_stacks=[data_grid_stack])
            assert np.unravel_index(plane.plane_images[0].argmax(), plane.plane_images[0].shape) == (4, 4)


class TestPlaneImageFromGrid:

    def test__3x3_grid__extracts_max_min_coordinates__creates_regular_grid_including_half_pixel_offset_from_edge(self):

        galaxy = g.Galaxy(light=lp.EllipticalSersic(intensity=1.0))

        grid = np.array([[-1.5, -1.5], [1.5, 1.5]])

        plane_image = pl.plane_image_from_grid_and_galaxies(shape=(3, 3), grid_stack=grid, galaxies=[galaxy], buffer=0.0)

        plane_image_galaxy = galaxy.intensities_from_grid(grid=np.array([[-1.0, -1.0], [-1.0, 0.0], [-1.0, 1.0],
                                                                           [0.0, -1.0], [0.0, 0.0], [0.0, 1.0],
                                                                           [1.0, -1.0], [1.0, 0.0], [1.0, 1.0]]))

        plane_image_galaxy = mapping_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(
            array_1d=plane_image_galaxy, shape=(3,3))

        assert (plane_image == plane_image_galaxy).all()

    def test__3x3_grid__extracts_max_min_coordinates__ignores_other_coordinates_more_central(self):

        galaxy = g.Galaxy(light=lp.EllipticalSersic(intensity=1.0))

        grid = np.array([[-1.5, -1.5], [1.5, 1.5], [0.1, -0.1], [-1.0, 0.6], [1.4, -1.3], [1.5, 1.5]])

        plane_image = pl.plane_image_from_grid_and_galaxies(shape=(3, 3), grid_stack=grid, galaxies=[galaxy], buffer=0.0)

        plane_image_galaxy = galaxy.intensities_from_grid(grid=np.array([[-1.0, -1.0], [-1.0, 0.0], [-1.0, 1.0],
                                                                           [0.0, -1.0], [0.0, 0.0], [0.0, 1.0],
                                                                           [1.0, -1.0], [1.0, 0.0], [1.0, 1.0]]))

        plane_image_galaxy = mapping_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(
            array_1d=plane_image_galaxy, shape=(3,3))

        assert (plane_image == plane_image_galaxy).all()

    def test__2x3_grid__shape_change_correct_and_coordinates_shift(self):

        galaxy = g.Galaxy(light=lp.EllipticalSersic(intensity=1.0))

        grid = np.array([[-1.5, -1.5], [1.5, 1.5]])

        plane_image = pl.plane_image_from_grid_and_galaxies(shape=(2, 3), grid_stack=grid, galaxies=[galaxy], buffer=0.0)

        plane_image_galaxy = galaxy.intensities_from_grid(grid=np.array([[-0.75, -1.0], [-0.75, 0.0], [-0.75, 1.0],
                                                                          [0.75, -1.0], [0.75, 0.0], [0.75, 1.0]]))

        plane_image_galaxy = mapping_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(
            array_1d=plane_image_galaxy, shape=(2,3))

        assert (plane_image == plane_image_galaxy).all()

    def test__3x2_grid__shape_change_correct_and_coordinates_shift(self):

        galaxy = g.Galaxy(light=lp.EllipticalSersic(intensity=1.0))

        grid = np.array([[-1.5, -1.5], [1.5, 1.5]])

        plane_image = pl.plane_image_from_grid_and_galaxies(shape=(3, 2), grid_stack=grid, galaxies=[galaxy], buffer=0.0)

        plane_image_galaxy = galaxy.intensities_from_grid(grid=np.array([[-1.0, -0.75], [-1.0, 0.75],
                                                                          [0.0, -0.75], [0.0, 0.75],
                                                                          [1.0, -0.75], [1.0, 0.75]]))

        plane_image_galaxy = mapping_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(
            array_1d=plane_image_galaxy, shape=(3,2))

        assert (plane_image == plane_image_galaxy).all()

    def test__3x3_grid__buffer_aligns_two_grids(self):

        galaxy = g.Galaxy(light=lp.EllipticalSersic(intensity=1.0))

        grid_without_buffer = np.array([[-1.48, -1.48], [1.48, 1.48]])

        plane_image = pl.plane_image_from_grid_and_galaxies(shape=(3, 3), grid_stack=grid_without_buffer, galaxies=[galaxy],
                                                            buffer=0.02)

        plane_image_galaxy = galaxy.intensities_from_grid(grid=np.array([[-1.0, -1.0], [-1.0, 0.0], [-1.0, 1.0],
                                                                           [0.0, -1.0], [0.0, 0.0], [0.0, 1.0],
                                                                           [1.0, -1.0], [1.0, 0.0], [1.0, 1.0]]))

        plane_image_galaxy = mapping_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(
            array_1d=plane_image_galaxy, shape=(3,3))

        assert (plane_image == plane_image_galaxy).all()


class TestPlaneImage:

    def test__compute_xticks_from_regular_grid_correctly(self):

        plane_image = pl.PlaneImage(array=np.ones((3, 3)), pixel_scales=(5.0, 1.0), grid=None)
        assert plane_image.xticks == pytest.approx(np.array([-1.5, -0.5, 0.5, 1.5]), 1e-3)

        plane_image = pl.PlaneImage(array=np.ones((3, 3)), pixel_scales=(5.0, 0.5), grid=None)
        assert plane_image.xticks == pytest.approx(np.array([-0.75, -0.25, 0.25, 0.75]), 1e-3)

        plane_image = pl.PlaneImage(array=np.ones((1, 6)), pixel_scales=(5.0, 1.0), grid=None)
        assert plane_image.xticks == pytest.approx(np.array([-3.0, -1.0, 1.0, 3.0]), 1e-2)


    def test__compute_yticks_from_regular_grid_correctly(self):

        plane_image = pl.PlaneImage(array=np.ones((3, 3)), pixel_scales=(1.0, 5.0), grid=None)
        assert plane_image.yticks == pytest.approx(np.array([-1.5, -0.5, 0.5, 1.5]), 1e-3)

        plane_image = pl.PlaneImage(array=np.ones((3, 3)), pixel_scales=(0.5, 5.0), grid=None)
        assert plane_image.yticks == pytest.approx(np.array([-0.75, -0.25, 0.25, 0.75]), 1e-3)

        plane_image = pl.PlaneImage(array=np.ones((6, 1)), pixel_scales=(1.0, 5.0), grid=None)
        assert plane_image.yticks == pytest.approx(np.array([-3.0, -1.0, 1.0, 3.0]), 1e-2)