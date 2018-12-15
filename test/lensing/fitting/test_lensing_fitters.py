import numpy as np
import pytest

from autolens.data.imaging import image
from autolens.data.array import mask as mask
from autolens.data.fitting import fitting_util
from autolens.lensing.fitting import lensing_fitting_util
from autolens.lensing.fitting import lensing_fitters
from autolens.model.galaxy import galaxy as g
from autolens.lensing import ray_tracing
from autolens.lensing import lensing_image
from autolens.model.profiles import light_profiles as lp
from test.mock.mock_profiles import MockLightProfile
from test.mock.mock_lensing import MockTracer

@pytest.fixture(name="no_galaxies", scope='function')
def make_no_galaxies():
    return [g.Galaxy()]


@pytest.fixture(name="sersic")
def make_sersic():
    return lp.EllipticalSersic(axis_ratio=1.0, phi=0.0, intensity=1.0, effective_radius=0.6, sersic_index=4.0)


@pytest.fixture(name="galaxy_light", scope='function')
def make_galaxy_light(sersic):
    return g.Galaxy(light_profile=sersic)


@pytest.fixture(name='li_no_blur_1x1')
def make_li_no_blur_1x1():
    psf = image.PSF(array=(np.array([[0.0, 0.0, 0.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.0, 0.0]])), pixel_scale=1.0, renormalize=False)

    im = image.Image(np.ones((3, 3)), pixel_scale=1.0, psf=psf, noise_map=np.ones((3, 3)))

    ma = mask.Mask(array=np.array([[True, True, True],
                                   [True, False, True],
                                   [True, True, True]]), pixel_scale=1.0)

    return lensing_image.LensingImage(im, ma, sub_grid_size=1)


@pytest.fixture(name='li_manual')
def make_li_manual():
    im = np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 2.0, 3.0, 0.0],
                   [0.0, 4.0, 5.0, 6.0, 0.0],
                   [0.0, 7.0, 8.0, 9.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0, 0.0]])
    psf = image.PSF(array=(np.array([[1.0, 5.0, 9.0],
                                     [2.0, 5.0, 1.0],
                                     [3.0, 4.0, 0.0]])), pixel_scale=1.0)
    im = image.Image(im, pixel_scale=1.0, psf=psf, noise_map=np.ones((5, 5)))
    ma = mask.Mask(array=np.array([[True, True, True, True, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, True, True, True, True]]), pixel_scale=1.0)

    return lensing_image.LensingImage(im, ma, sub_grid_size=1)

@pytest.fixture(name='li_manual_1')
def make_li_manual_1():
    im = np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 2.0, 3.0, 0.0],
                   [0.0, 4.0, 5.0, 6.0, 0.0],
                   [0.0, 7.0, 8.0, 10.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0, 0.0]])
    psf = image.PSF(array=(np.array([[1.0, 5.0, 9.0],
                                     [2.0, 1.0, 1.0],
                                     [3.0, 2.0, 0.0]])), pixel_scale=1.0)
    im = image.Image(im, pixel_scale=2.0, psf=psf, noise_map=2.0 * np.ones((5, 5)))
    ma = mask.Mask(array=np.array([[True, True, True, True, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, True, True, True, True]]), pixel_scale=2.0)

    return lensing_image.LensingImage(im, ma, sub_grid_size=2)


@pytest.fixture(name='hyper')
def make_hyper():
    class Hyper(object):

        def __init__(self):
            pass

    hyper = Hyper()

    hyper.hyper_model_image = np.array([1.0, 3.0, 5.0, 7.0, 9.0, 8.0, 6.0, 4.0, 0.0])
    hyper.hyper_galaxy_images = [np.array([1.0, 3.0, 5.0, 7.0, 9.0, 8.0, 6.0, 4.0, 0.0]),
                                 np.array([1.0, 3.0, 5.0, 7.0, 9.0, 8.0, 6.0, 4.0, 0.0])]
    hyper.hyper_minimum_values = [0.2, 0.8]
    return hyper

@pytest.fixture(name='li_hyper_no_blur')
def make_li_hyper_no_blur(hyper):
    im = np.array([[0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0]])
    psf = image.PSF(array=(np.array([[0.0, 0.0, 0.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.0, 0.0]])), pixel_scale=1.0, renormalize=False)
    im = image.Image(im, pixel_scale=1.0, psf=psf, noise_map=np.ones((4, 4)))

    ma = np.array([[True, True, True, True],
                   [True, False, False, True],
                   [True, False, False, True],
                   [True, True, True, True]])
    ma = mask.Mask(array=ma, pixel_scale=1.0)

    return lensing_image.LensingHyperImage(im, ma, hyper_model_image=hyper.hyper_model_image,
                                           hyper_galaxy_images=hyper.hyper_galaxy_images,
                                           hyper_minimum_values=hyper.hyper_minimum_values, sub_grid_size=1)

@pytest.fixture(name='li_hyper_no_blur_1x1')
def make_li_hyper_no_blur_1x1(hyper):
    psf = image.PSF(array=(np.array([[0.0, 0.0, 0.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.0, 0.0]])), pixel_scale=1.0, renormalize=False)

    im = image.Image(np.ones((3, 3)), pixel_scale=1.0, psf=psf, noise_map=np.ones((3, 3)))

    ma = mask.Mask(array=np.array([[True, True, True],
                                   [True, False, True],
                                   [True, True, True]]), pixel_scale=1.0)

    return lensing_image.LensingHyperImage(im, ma, hyper_model_image=hyper.hyper_model_image,
                                           hyper_galaxy_images=hyper.hyper_galaxy_images,
                                           hyper_minimum_values=hyper.hyper_minimum_values, sub_grid_size=1)

@pytest.fixture(name='li_hyper_manual')
def make_li_hyper_manual(hyper):
    im = np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 2.0, 3.0, 0.0],
                   [0.0, 4.0, 5.0, 6.0, 0.0],
                   [0.0, 7.0, 8.0, 9.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0, 0.0]])
    psf = image.PSF(array=(np.array([[1.0, 5.0, 9.0],
                                     [2.0, 5.0, 1.0],
                                     [3.0, 4.0, 0.0]])), pixel_scale=1.0)
    im = image.Image(im, pixel_scale=1.0, psf=psf, noise_map=np.ones((5, 5)))
    ma = mask.Mask(array=np.array([[True, True, True, True, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, True, True, True, True]]), pixel_scale=1.0)

    return lensing_image.LensingHyperImage(im, ma, hyper_model_image=hyper.hyper_model_image,
                                           hyper_galaxy_images=hyper.hyper_galaxy_images,
                                           hyper_minimum_values=hyper.hyper_minimum_values, sub_grid_size=1)

@pytest.fixture(name='li_hyper_manual_1')
def make_li_hyper_manual_1(hyper):
    im = np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 2.0, 3.0, 0.0],
                   [0.0, 4.0, 5.0, 9.0, 0.0],
                   [0.0, 7.0, 8.0, 9.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0, 0.0]])
    psf = image.PSF(array=(np.array([[1.0, 5.0, 9.0],
                                     [2.0, 5.0, 1.0],
                                     [3.0, 4.0, 0.0]])), pixel_scale=2.0)
    im = image.Image(im, pixel_scale=2.0, psf=psf, noise_map=np.ones((5, 5)))
    ma = mask.Mask(array=np.array([[True, True, True, True, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, False, False, False, True],
                                   [True, True, True, True, True]]), pixel_scale=1.0)

    return lensing_image.LensingHyperImage(im, ma, hyper_model_image=hyper.hyper_model_image,
                                           hyper_galaxy_images=hyper.hyper_galaxy_images,
                                           hyper_minimum_values=hyper.hyper_minimum_values, sub_grid_size=2)


@pytest.fixture(name='li_blur')
def make_li_blur():

    im = np.array([[0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0]])
    psf = image.PSF(array=(np.array([[1.0, 1.0, 1.0],
                                     [1.0, 1.0, 1.0],
                                     [1.0, 1.0, 1.0]])), pixel_scale=1.0, renormalize=False)
    im = image.Image(im, pixel_scale=1.0, psf=psf, noise_map=np.ones((4, 4)))

    ma = np.array([[True, True, True, True],
                   [True, False, False, True],
                   [True, False, False, True],
                   [True, True, True, True]])
    ma = mask.Mask(array=ma, pixel_scale=1.0)

    return lensing_image.LensingImage(im, ma, sub_grid_size=2)


@pytest.fixture(name='li_no_blur')
def make_li_no_blur():
    im = np.array([[0.0, 0.0, 0.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 1.0, 1.0, 0.0],
                   [0.0, 0.0, 0.0, 0.0]])
    psf = image.PSF(array=(np.array([[0.0, 0.0, 0.0],
                                     [0.0, 1.0, 0.0],
                                     [0.0, 0.0, 0.0]])), pixel_scale=1.0, renormalize=False)
    im = image.Image(im, pixel_scale=1.0, psf=psf, noise_map=np.ones((4, 4)))

    ma = np.array([[True, True, True, True],
                   [True, False, False, True],
                   [True, False, False, True],
                   [True, True, True, True]])
    ma = mask.Mask(array=ma, pixel_scale=1.0)

    return lensing_image.LensingImage(im, ma, sub_grid_size=2)


class TestLensingProfileFit:

    class TestModelImages:

        def test__mock_tracer__2x2_image_all_1s__3x3_psf_all_1s__blurring_region__image_blurs_to_9s(self, li_blur):

            tracer = MockTracer(unblurred_image_1d=li_blur.mask.map_2d_array_to_masked_1d_array(li_blur.image),
                                blurring_image_1d=np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]),
                                has_light_profile=True, has_hyper_galaxy=False, has_pixelization=False)

            fit = lensing_fitters.LensingProfileFitter(lensing_image=li_blur, tracer=tracer)

            assert (fit.model_image == np.array([[0.0, 0.0, 0.0, 0.0],
                                                 [0.0, 9.0, 9.0, 0.0],
                                                 [0.0, 9.0, 9.0, 0.0],
                                                 [0.0, 0.0, 0.0, 0.0]])).all()

    class TestLikelihood:

        def test__1x1_image__tracing_fits_data_perfectly__no_psf_blurring__lh_is_noise_term(self):

            psf = image.PSF(array=(np.array([[0.0, 0.0, 0.0],
                                             [0.0, 1.0, 0.0],
                                             [0.0, 0.0, 0.0]])), pixel_scale=1.0)

            im = image.Image(np.ones((3, 3)), pixel_scale=1.0, psf=psf, noise_map=np.ones((3, 3)))

            ma = mask.Mask(array=np.array([[True, True, True],
                                           [True, False, True],
                                           [True, True, True]]), pixel_scale=1.0)
            li = lensing_image.LensingImage(im, ma, sub_grid_size=1)

            g0 = g.Galaxy(light_profile=MockLightProfile(value=1.0))
            tracer = ray_tracing.TracerImagePlane(lens_galaxies=[g0], image_plane_grids=[li.grids])

            fit = lensing_fitters.LensingProfileFitter(lensing_image=li, tracer=tracer)
            assert fit.likelihood == -0.5 * np.log(2 * np.pi * 1.0)

        def test__1x2_image__tracing_fits_data_with_chi_sq_5(self):

            psf = image.PSF(array=(np.array([[0.0, 0.0, 0.0],
                                             [0.0, 1.0, 0.0],
                                             [0.0, 0.0, 0.0]])), pixel_scale=1.0)

            im = image.Image(5.0 * np.ones((3, 4)), pixel_scale=1.0, psf=psf, noise_map=np.ones((3, 4)))
            im[1,2]  = 4.0

            ma = mask.Mask(array=np.array([[True, True, True, True],
                                           [True, False, False, True],
                                           [True, True, True, True]]), pixel_scale=1.0)

            li = lensing_image.LensingImage(im, ma, sub_grid_size=1)

            # Setup as a ray trace instance, using a light profile for the lens

            g0 = g.Galaxy(light_profile=MockLightProfile(value=1.0, size=2))
            tracer = ray_tracing.TracerImagePlane(lens_galaxies=[g0], image_plane_grids=[li.grids])

            fit = lensing_fitters.LensingProfileFitter(lensing_image=li, tracer=tracer)

            assert fit.chi_squared_term == 25.0
            assert fit.reduced_chi_squared_term == 25.0 / 2.0
            assert fit.likelihood == -0.5 * (25.0 + 2.0*np.log(2 * np.pi * 1.0))

    class TestCompareToManual:

        def test___manual_image_and_psf(self, li_manual):

            g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))

            tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0], source_galaxies=[g0],
                                                         image_plane_grids=[li_manual.grids])

            padded_tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0], source_galaxies=[g0],
                                                                  image_plane_grids=[li_manual.padded_grids])

            fit = lensing_fitters.fit_lensing_image_with_tracer(lensing_image=li_manual, tracer=tracer,
                                                                padded_tracer=padded_tracer)

            assert li_manual.noise_map == pytest.approx(fit.noise_map, 1e-4)

            unblurred_image_1d = tracer.image_plane_images_[0]
            blurring_image_1d = tracer.image_plane_blurring_images_[0]

            model_image = lensing_fitting_util.blurred_image_from_1d_unblurred_and_blurring_images(
                unblurred_image_1d=unblurred_image_1d, blurring_image_1d=blurring_image_1d,
                convolver=li_manual.convolver_image, map_to_scaled_array=li_manual.map_to_scaled_array)

            assert model_image == pytest.approx(fit.model_image, 1e-4)

            residual_map = fitting_util.residual_map_from_data_mask_and_model_data(data=li_manual.image,
                                                                                   mask=li_manual.mask,
                                                                                   model_data=model_image)

            assert residual_map == pytest.approx(fit.residual_map, 1e-4)

            chi_squared_map = fitting_util.chi_squareds_from_residual_map_and_noise_map(residual_map=residual_map,
                                                                                        noise_map=li_manual.noise_map)

            assert chi_squared_map == pytest.approx(fit.chi_squared_map, 1e-4)

            chi_squared_term = fitting_util.chi_squared_term_from_chi_squared_map(chi_squared_map=chi_squared_map)
            noise_term = fitting_util.noise_term_from_mask_and_noise_map(mask=li_manual.mask,
                                                                         noise_map=li_manual.noise_map)
            likelihood = fitting_util.likelihood_from_chi_squared_term_and_noise_term(chi_squared_term=chi_squared_term,
                                                                                      noise_term=noise_term)

            assert likelihood == pytest.approx(fit.likelihood, 1e-4)

            fast_likelihood = lensing_fitters.fast_likelihood_from_lensing_image_and_tracer(lensing_image=li_manual,
                                                                                            tracer=tracer)
            assert fast_likelihood == pytest.approx(fit.likelihood)

            model_image_of_planes = lensing_fitting_util.blurred_image_of_planes_from_tracer_and_convolver(
            tracer=tracer, convolver_image=li_manual.convolver_image, map_to_scaled_array=li_manual.map_to_scaled_array)

            assert (model_image_of_planes[0] == fit.model_image_of_planes[0]).all()
            assert (model_image_of_planes[1] == fit.model_image_of_planes[1]).all()

            # padded_model_image = fitting_util.unmasked_blurred_images_from_fitting_images(fitting_images=[li_manual],
            #                                                                          unmasked_images_=padded_tracer.image_plane_images_)
            #
            # assert (padded_model_image == fit.unmasked_model_profile_image).all()
            #
            # padded_model_image_of_galaxies = \
            #     lensing_fitters.unmasked_model_images_of_galaxies_from_lensing_image_and_tracer(lensing_image=li_manual,
            #                                                                                     tracer=padded_tracer,
            #                                                                                     image_index=0)
            #
            # assert (padded_model_image_of_galaxies[0][0] == fit.unmasked_model_profile_images_of_galaxies[0][0][0]).all()
            # assert (padded_model_image_of_galaxies[1][0] == fit.unmasked_model_profile_images_of_galaxies[0][1][0]).all()

# class TestHyperLensingProfileFit:
#
#     class TestScaledLikelihood:
#
#         def test__hyper_galaxy_adds_to_noise_term_for_scaled_noise__chi_squared_is_0(self, li_hyper_no_blur_1x1):
#             # Setup as a ray trace instance, using a light profile for the lens
#
#             g0 = g.Galaxy(light_profile=MockLightProfile(value=1.0))
#             g1 = g.Galaxy(light_profile=MockLightProfile(value=0.0))
#
#             tracer = ray_tracing.TracerImagePlane(lens_galaxies=[g0, g1],
#                                                   image_plane_grids=[li_hyper_no_blur_1x1.grid_stacks])
#
#             li_hyper_no_blur_1x1.hyper_model_image = np.array([1.0])
#             li_hyper_no_blur_1x1.hyper_galaxy_images = [np.array([1.0]), np.array([1.0])]
#
#             tracer.image_plane.galaxies[0].hyper_galaxy = MockHyperGalaxy(contribution_factor=0.0, noise_factor=1.0,
#                                                                           noise_power=1.0)
#             tracer.image_plane.galaxies[1].hyper_galaxy = MockHyperGalaxy(contribution_factor=0.0, noise_factor=2.0,
#                                                                           noise_power=1.0)
#
#             fit = lensing_fitters.HyperLensingProfileFit(lensing_hyper_images=[li_hyper_no_blur_1x1], tracer=tracer)
#
#             chi_squared_term = 0.0
#             scaled_noise_term = np.log(2 * np.pi * 4.0 ** 2.0)
#
#             assert fit.scaled_likelihood == -0.5 * (chi_squared_term + scaled_noise_term)
#
#         def test__hyper_galaxy_adds_to_noise_term_for_scaled_noise__chi_squared_nonzero(self, no_galaxies,
#                                                                                         li_hyper_no_blur_1x1):
#             li_hyper_no_blur_1x1[0] = 2.0
#
#             g0 = g.Galaxy(light_profile=MockLightProfile(value=1.0))
#             g1 = g.Galaxy(light_profile=MockLightProfile(value=0.0))
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0, g1], source_galaxies=no_galaxies,
#                                                          image_plane_grids=[li_hyper_no_blur_1x1.grid_stacks])
#
#             li_hyper_no_blur_1x1.hyper_model_image = np.array([1.0])
#             li_hyper_no_blur_1x1.hyper_galaxy_images = [np.array([1.0]), np.array([1.0])]
#
#             tracer.image_plane.galaxies[0].hyper_galaxy = MockHyperGalaxy(contribution_factor=0.0, noise_factor=1.0,
#                                                                           noise_power=1.0)
#             tracer.image_plane.galaxies[1].hyper_galaxy = MockHyperGalaxy(contribution_factor=0.0, noise_factor=2.0,
#                                                                           noise_power=1.0)
#
#             fit = lensing_fitters.HyperLensingProfileFit(lensing_hyper_images=[li_hyper_no_blur_1x1], tracer=tracer)
#
#             scaled_chi_squared_term = (1.0 / (4.0)) ** 2.0
#             scaled_noise_term = np.log(2 * np.pi * 4.0 ** 2.0)
#
#             assert fit.scaled_likelihood == -0.5 * (scaled_chi_squared_term + scaled_noise_term)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0, g1], source_galaxies=no_galaxies,
#                                                          image_plane_grids=[li_hyper_no_blur_1x1.grid_stacks,
#                                                                             li_hyper_no_blur_1x1.grid_stacks])
#
#             tracer.image_plane.galaxies[0].hyper_galaxy = MockHyperGalaxy(contribution_factor=0.0, noise_factor=1.0,
#                                                                           noise_power=1.0)
#             tracer.image_plane.galaxies[1].hyper_galaxy = MockHyperGalaxy(contribution_factor=0.0, noise_factor=2.0,
#                                                                           noise_power=1.0)
#
#             fit = lensing_fitters.HyperLensingProfileFit(lensing_hyper_images=[li_hyper_no_blur_1x1,
#                                                                                li_hyper_no_blur_1x1], tracer=tracer)
#
#             scaled_chi_squared_term = (1.0 / (4.0)) ** 2.0
#             scaled_noise_term = np.log(2 * np.pi * 4.0 ** 2.0)
#
#             assert fit.scaled_chi_squared_terms[0] == scaled_chi_squared_term
#             assert fit.scaled_chi_squared_terms[1] == scaled_chi_squared_term
#             assert fit.scaled_noise_terms[0] == scaled_noise_term
#             assert fit.scaled_noise_terms[1] == scaled_noise_term
#
#             assert fit.scaled_likelihoods[0] == -0.5 * (scaled_chi_squared_term + scaled_noise_term)
#             assert fit.scaled_likelihoods[1] == -0.5 * (scaled_chi_squared_term + scaled_noise_term)
#             assert fit.scaled_likelihood == 2.0 * -0.5 * (scaled_chi_squared_term + scaled_noise_term)
#
#     class TestAbstractLogic:
#
#         def test__logic_in_abstract_fit(self, li_hyper_no_blur, galaxy_light):
#             tracer = ray_tracing.TracerImagePlane(lens_galaxies=[galaxy_light],
#                                                   image_plane_grids=[li_hyper_no_blur.grid_stacks])
#
#             fit = lensing_fitters.HyperLensingProfileFit(lensing_hyper_images=[li_hyper_no_blur], tracer=tracer)
#
#             assert fit.total_inversions == 0
#
#     class TestCompareToManual:
#
#         def test___manual_image_and_psf(self, li_hyper_manual):
#
#             hyper_galaxy = g.HyperGalaxy(contribution_factor=4.0, noise_factor=2.0, noise_power=3.0)
#
#             g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0), hyper_galaxy=hyper_galaxy)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0], source_galaxies=[g0],
#                                                          image_plane_grids=[li_hyper_manual.grid_stacks])
#
#             padded_tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0], source_galaxies=[g0],
#                                                                 image_plane_grids=[li_hyper_manual.padded_grids])
#
#             fit = lensing_fitters.fit_lensing_image_with_tracer(lensing_image=li_hyper_manual, tracer=tracer,
#                                                                 padded_tracer=padded_tracer)
#
#             image_im = tracer.image_plane_images_
#             blurring_im = tracer.image_plane_blurring_images_
#             model_images = lensing_fitting_util.blurred_image_from_1d_unblurred_and_blurring_images(image_=image_im, blurring_image_=blurring_im,
#                                                                              convolver=[li_hyper_manual.convolver_image])
#             residual_map = fitting_util.residuals_from_data_mask_and_model_data(datas=[li_hyper_manual], model_data=model_images)
#             chi_squared_map = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map=residual_map,
#                                                                                   noise_maps=[li_hyper_manual.noise_map_])
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(li_hyper_manual.noise_map_) == \
#                    pytest.approx(fit.noise_maps, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(model_images[0]) == \
#                    pytest.approx(fit.model_image, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(residual_map[0]) == \
#                    pytest.approx(fit.residual, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(chi_squared_map[0]) == \
#                    pytest.approx(fit.chi_squared, 1e-4)
#
#             chi_squared_terms = fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=chi_squared_map)
#             noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=li_hyper_manual.noise_map_)
#             likelihoods = fitting_util.likelihood_from_chi_squared_term_and_noise_term(
#                 chi_squared_term=chi_squared_terms,
#                 noise_term=noise_terms)
#
#             assert likelihoods[0] == pytest.approx(fit.likelihood, 1e-4)
#
#             contributions = fitting_util.contributions_from_hyper_images_and_galaxies(li_hyper_manual.hyper_model_image,
#                                                                                  li_hyper_manual.hyper_galaxy_images, [hyper_galaxy, hyper_galaxy],
#                                                                                  li_hyper_manual.hyper_minimum_values)
#
#             scaled_noise_maps = fitting_util.scaled_noise_maps_from_fitting_hyper_images_contributions_and_hyper_galaxies(
#                 fitting_hyper_images=[li_hyper_manual], contributions_=[contributions], hyper_galaxies=[hyper_galaxy,
#                                                                                                         hyper_galaxy])
#             scaled_chi_squareds = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map, scaled_noise_maps)
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[0]) == \
#                    pytest.approx(fit.contributions[0][0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[1]) == \
#                    pytest.approx(fit.contributions[0][1], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_noise_maps[0]) == \
#                    pytest.approx(fit.scaled_noise_map, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_chi_squareds[0]) == \
#                    pytest.approx(fit.scaled_chi_squared, 1e-4)
#
#             scaled_chi_squared_terms= fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=scaled_chi_squareds)
#             scaled_noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=scaled_noise_maps)
#             scaled_likelihoods = fitting_util.likelihood_from_chi_squared_term_and_noise_term(
#                 chi_squared_term=scaled_chi_squared_terms, noise_term=scaled_noise_terms)
#
#             assert scaled_likelihoods[0] == pytest.approx(fit.scaled_likelihood, 1e-4)
#
#             fast_scaled_likelihood = lensing_fitters.fast_likelihood_from_lensing_image_and_tracer(
#                 lensing_image=li_hyper_manual, tracer=tracer)
#
#             assert fast_scaled_likelihood == fit.scaled_likelihood
#
#             padded_model_image = fitting_util.unmasked_blurred_images_from_fitting_images(fitting_images=[li_hyper_manual],
#                                                                                      unmasked_images_=padded_tracer.image_plane_images_)
#
#             assert (padded_model_image == fit.unmasked_model_profile_images[0]).all()
#
#             padded_model_image_of_galaxies = \
#                 lensing_fitters.unmasked_model_images_of_galaxies_from_lensing_image_and_tracer(
#                     lensing_image=li_hyper_manual, tracer=padded_tracer, image_index=0)
#
#             assert (padded_model_image_of_galaxies[0][0] == fit.unmasked_model_profile_images_of_galaxies[0][0]).all()
#
#         def test___same_as_above__x2_images(self, li_hyper_manual, li_hyper_manual_1):
#
#             hyper_galaxy = g.HyperGalaxy(contribution_factor=4.0, noise_factor=2.0, noise_power=3.0)
#
#             g0 = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0), hyper_galaxy=hyper_galaxy)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0], source_galaxies=[g0],
#                                                          image_plane_grids=[li_hyper_manual.grid_stacks,
#                                                                             li_hyper_manual_1.grid_stacks])
#
#             padded_tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g0], source_galaxies=[g0],
#                                                                 image_plane_grids=[li_hyper_manual.padded_grids,
#                                                                                    li_hyper_manual_1.padded_grids])
#
#             fit = lensing_fitters.fit_multiple_lensing_images_with_tracer(lensing_images=[li_hyper_manual,
#                                                                                           li_hyper_manual_1], tracer=tracer,
#                                                                           padded_tracer=padded_tracer)
#
#             image_im = tracer.image_plane_images_
#             blurring_im = tracer.image_plane_blurring_images_
#             model_images = lensing_fitting_util.blurred_image_from_1d_unblurred_and_blurring_images(image_=image_im, blurring_image_=blurring_im,
#                                                                              convolver=[li_hyper_manual.convolver_image,
#                                                                                           li_hyper_manual_1.convolver_image])
#             residual_map = fitting_util.residuals_from_data_mask_and_model_data(datas=[li_hyper_manual, li_hyper_manual_1],
#                                                                              model_data=model_images)
#             chi_squared_map = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map=residual_map,
#                                                                                   noise_maps=[li_hyper_manual.noise_map_,
#                                                                                            li_hyper_manual_1.noise_map_])
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(li_hyper_manual.noise_map_) == \
#                    pytest.approx(fit.noise_maps[0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(model_images[0]) == \
#                    pytest.approx(fit.model_datas[0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(residual_map[0]) == \
#                    pytest.approx(fit.residual_map[0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(chi_squared_map[0]) == \
#                    pytest.approx(fit.chi_squared_map[0], 1e-4)
#
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(li_hyper_manual_1.noise_map_) == \
#                    pytest.approx(fit.noise_maps[1], 1e-4)
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(model_images[1]) == \
#                    pytest.approx(fit.model_datas[1], 1e-4)
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(residual_map[1]) == \
#                    pytest.approx(fit.residual_map[1], 1e-4)
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(chi_squared_map[1]) == \
#                    pytest.approx(fit.chi_squared_map[1], 1e-4)
#
#             chi_squared_terms = fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=chi_squared_map)
#             noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=[li_hyper_manual.noise_map_,
#                                                                                      li_hyper_manual_1.noise_map_])
#             likelihoods = fitting_util.likelihood_from_chi_squared_term_and_noise_term(
#                 chi_squared_term=chi_squared_terms,
#                 noise_term=noise_terms)
#
#             assert likelihoods[0] == pytest.approx(fit.likelihoods[0], 1e-4)
#             assert likelihoods[1] == pytest.approx(fit.likelihoods[1], 1e-4)
#             assert likelihoods[0] + likelihoods[1] == pytest.approx(fit.likelihood, 1e-4)
#
#             contributions = fitting_util.contributions_from_fitting_hyper_images_and_hyper_galaxies(
#                 fitting_hyper_images=[li_hyper_manual, li_hyper_manual_1],
#                 hyper_galaxies=[hyper_galaxy, hyper_galaxy])
#
#             scaled_noise_maps = fitting_util.scaled_noise_maps_from_fitting_hyper_images_contributions_and_hyper_galaxies(
#                 fitting_hyper_images=[li_hyper_manual, li_hyper_manual_1],
#                 contributions_=contributions, hyper_galaxies=[hyper_galaxy, hyper_galaxy])
#
#             scaled_chi_squareds = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map, scaled_noise_maps)
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[0][0]) == \
#                    pytest.approx(fit.contributions[0][0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[0][1]) == \
#                    pytest.approx(fit.contributions[0][1], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_noise_maps[0]) == \
#                    pytest.approx(fit.scaled_noise_maps[0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_chi_squareds[0]) == \
#                    pytest.approx(fit.scaled_chi_squareds[0], 1e-4)
#
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(contributions[1][0]) == \
#                    pytest.approx(fit.contributions[1][0], 1e-4)
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(contributions[1][1]) == \
#                    pytest.approx(fit.contributions[1][1], 1e-4)
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(scaled_noise_maps[1]) == \
#                    pytest.approx(fit.scaled_noise_maps[1], 1e-4)
#             assert li_hyper_manual_1.grid_stacks.regular.scaled_array_from_array_1d(scaled_chi_squareds[1]) == \
#                    pytest.approx(fit.scaled_chi_squareds[1], 1e-4)
#
#             scaled_chi_squared_terms= fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=scaled_chi_squareds)
#             scaled_noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=scaled_noise_maps)
#             scaled_likelihoods = fitting_util.likelihood_from_chi_squared_term_and_noise_term(
#                 chi_squared_term=scaled_chi_squared_terms, noise_term=scaled_noise_terms)
#
#             assert scaled_likelihoods[0] == pytest.approx(fit.scaled_likelihoods[0], 1e-4)
#             assert scaled_likelihoods[1] == pytest.approx(fit.scaled_likelihoods[1], 1e-4)
#             assert scaled_likelihoods[0] + scaled_likelihoods[1] == pytest.approx(fit.scaled_likelihood, 1e-4)
#
#             fast_scaled_likelihood = lensing_fitters.fast_likelihood_from_multiple_lensing_images_and_tracer(
#                 lensing_images=[li_hyper_manual, li_hyper_manual_1], tracer=tracer)
#
#             assert fast_scaled_likelihood == pytest.approx(fit.scaled_likelihood, 1e-2)
#
#             padded_model_images = fitting_util.unmasked_blurred_images_from_fitting_images(
#                 fitting_images=[li_hyper_manual, li_hyper_manual_1], unmasked_images_=padded_tracer.image_plane_images_)
#
#             assert (padded_model_images[0] == fit.unmasked_model_profile_images[0]).all()
#             assert (padded_model_images[1] == fit.unmasked_model_profile_images[1]).all()
#
#             padded_model_image_of_galaxies_0 = \
#                 lensing_fitters.unmasked_model_images_of_galaxies_from_lensing_image_and_tracer(lensing_image=li_hyper_manual,
#                                                                                                 tracer=padded_tracer,
#                                                                                                 image_index=0)
#
#             assert (padded_model_image_of_galaxies_0[0][0] == fit.unmasked_model_profile_images_of_galaxies[0][0][0]).all()
#             assert (padded_model_image_of_galaxies_0[1][0] == fit.unmasked_model_profile_images_of_galaxies[0][1][0]).all()
#
#             padded_model_image_of_galaxies_1 = \
#                 lensing_fitters.unmasked_model_images_of_galaxies_from_lensing_image_and_tracer(lensing_image=li_hyper_manual_1,
#                                                                                                 tracer=padded_tracer,
#                                                                                                 image_index=1)
#
#             assert (padded_model_image_of_galaxies_1[0][0] == fit.unmasked_model_profile_images_of_galaxies[1][0][0]).all()
#             assert (padded_model_image_of_galaxies_1[1][0] == fit.unmasked_model_profile_images_of_galaxies[1][1][0]).all()
#
#
# class TestInversionLensingFit:
#
#     class TestAbstractLogic:
#
#         def test__logic_in_abstract_fit(self, li_no_blur):
#
#             galaxy_pix = g.Galaxy(pixelization=pixelizations.Rectangular(shape=(3, 3)),
#                                   regularization=regularization.Constant(coefficients=(1.0,)))
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g.Galaxy()], source_galaxies=[galaxy_pix],
#                                                          image_plane_grids=[li_no_blur.grid_stacks],
#                                                          borders=None)
#
#             fit = lensing_fitters.LensingInversionFit(lensing_images=[li_no_blur], tracer=tracer)
#
#             assert fit.total_inversions == 1
#
#     class TestModelImageOfPlanes:
#
#         def test__model_images_are_none_and_an_image(self):
#
#             im = np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 0.0, 0.0, 0.0, 0.0]]).view(image.Image)
#
#             ma = np.array([[True, True, True, True, True],
#                            [True, False, False, False, True],
#                            [True, False, False, False, True],
#                            [True, False, False, False, True],
#                            [True, True, True, True, True]])
#
#             ma = masks.Mask(ma, pixel_scale=1.0)
#
#             psf = image.PSF(array=np.array([[0.0, 0.0, 0.0],
#                                             [0.0, 1.0, 0.0],
#                                             [0.0, 0.0, 0.0]]), pixel_scale=1.0)
#             im = image.Image(im, pixel_scale=1.0, psf=psf, noise_maps=np.ones((5, 5)))
#             li = lensing_image.LensingImage(im, ma, sub_grid_size=2)
#
#             galaxy_pix = g.Galaxy(pixelization=pixelizations.Rectangular(shape=(3, 3)),
#                                   regularization=regularization.Constant(coefficients=(1.0,)))
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g.Galaxy()], source_galaxies=[galaxy_pix],
#                                                          image_plane_grids=[li.grid_stacks], borders=None)
#             fit = lensing_fitters.LensingInversionFit(lensing_images=[li], tracer=tracer)
#
#             assert fit.model_images_of_planes[0][0] == None
#             assert fit.model_images_of_planes[0][1] == pytest.approx(np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
#                                                                             [0.0, 1.0, 1.0, 1.0, 0.0],
#                                                                             [0.0, 1.0, 1.0, 1.0, 0.0],
#                                                                             [0.0, 1.0, 1.0, 1.0, 0.0],
#                                                                             [0.0, 0.0, 0.0, 0.0, 0.0]]), 1e-2)
#
#     class TestRectangularInversion:
#
#         def test__image_all_1s__direct_image_to_source_mapping__perfect_fit_even_with_regularization(self):
#             im = np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 0.0, 0.0, 0.0, 0.0]]).view(image.Image)
#
#             ma = np.array([[True, True, True, True, True],
#                            [True, False, False, False, True],
#                            [True, False, False, False, True],
#                            [True, False, False, False, True],
#                            [True, True, True, True, True]])
#             ma = masks.Mask(ma, pixel_scale=1.0)
#
#             psf = image.PSF(array=np.array([[0.0, 0.0, 0.0],
#                                             [0.0, 1.0, 0.0],
#                                             [0.0, 0.0, 0.0]]), pixel_scale=1.0)
#             im = image.Image(im, pixel_scale=1.0, psf=psf, noise_maps=np.ones((5, 5)))
#             li = lensing_image.LensingImage(im, ma, sub_grid_size=2)
#
#             galaxy_pix = g.Galaxy(pixelization=pixelizations.Rectangular(shape=(3, 3)),
#                                   regularization=regularization.Constant(coefficients=(1.0,)))
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g.Galaxy()], source_galaxies=[galaxy_pix],
#                                                          image_plane_grids=[li.grid_stacks], borders=None)
#             fit = lensing_fitters.LensingInversionFit(lensing_images=[li], tracer=tracer)
#
#             cov_matrix = np.array([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                    [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                    [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                    [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
#                                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
#                                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
#                                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
#                                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]])
#             reg_matrix = np.array([[2.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                    [-1.0, 3.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
#                                    [0.0, -1.0, 2.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
#                                    [-1.0, 0.0, 0.0, 3.0, -1.0, 0.0, -1.0, 0.0, 0.0],
#                                    [0.0, -1.0, 0.0, -1.0, 4.0, -1.0, 0.0, -1.0, 0.0],
#                                    [0.0, 0.0, -1.0, 0.0, -1.0, 3.0, 0.0, 0.0, - 1.0],
#                                    [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 2.0, -1.0, 0.0],
#                                    [0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 3.0, -1.0],
#                                    [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 2.0]])
#             reg_matrix = reg_matrix + 1e-8 * np.identity(9)
#             cov_reg_matrix = cov_matrix + reg_matrix
#
#             chi_sq_term = 0.0
#             gl_term = 1e-8
#             det_cov_reg_term = np.log(np.linalg.det(cov_reg_matrix))
#             det_reg_term = np.log(np.linalg.det(reg_matrix))
#             noise_term = 9.0 * np.log(2 * np.pi * 1.0 ** 2.0)
#             evidence = -0.5 * (chi_sq_term + gl_term + det_cov_reg_term - det_reg_term + noise_term)
#
#             assert fit.evidence == pytest.approx(evidence, 1e-4)
#
#     class TestCompareToManual:
#
#         def test___manual_image_and_psf(self, li_manual):
#
#             pix = pixelizations.Rectangular(shape=(3, 3))
#             reg = regularization.Constant(coefficients=(1.0,))
#
#             g0 = g.Galaxy(pixelization=pix, regularization=reg)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g.Galaxy()], source_galaxies=[g0],
#                                                          image_plane_grids=[li_manual.grid_stacks],
#                                                          borders=None)
#
#             fit = lensing_fitters.fit_lensing_image_with_tracer(lensing_image=li_manual, tracer=tracer)
#
#             mapper = pix.mapper_from_grids_and_border(li_manual.grid_stacks, None)
#             inversion = inversions.inversion_from_lensing_image_mapper_and_regularization(mapper=mapper, regularization=reg,
#                                                                                           image=li_manual, noise_maps=li_manual.noise_map_,
#                                                                                           convolver=li_manual.convolver_mapping_matrix)
#
#             residual_map = fitting_util.residuals_from_data_mask_and_model_data(datas=[li_manual],
#                                                                              model_data=[inversion.reconstructed_data_vector])
#             chi_squared_map = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map=residual_map,
#                                                                                   noise_maps=[li_manual.noise_map_])
#
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(li_manual.noise_map_) == \
#                    pytest.approx(fit.noise_maps, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(inversion.reconstructed_data_vector) == \
#                    pytest.approx(fit.model_data, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(residual_map[0]) == \
#                    pytest.approx(fit.residual, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(chi_squared_map[0]) == \
#                    pytest.approx(fit.chi_squared, 1e-4)
#
#             chi_squared_terms = fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=chi_squared_map)
#             noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=[li_manual.noise_map_])
#             likelihoods_with_regularization = \
#                 fitting_util.likelihood_with_regularization_from_chi_squared_term_regularization_and_noise_term(
#                     chi_squared_terms, [inversion.regularization_term], noise_terms)
#
#             assert likelihoods_with_regularization[0] == pytest.approx(fit.likelihoods_with_regularization[0], 1e-4)
#
#             evidences = fitting_util.evidence_from_reconstruction_terms(chi_squared_terms, [inversion.regularization_term],
#                                                                         [inversion.log_det_curvature_reg_matrix_term],
#                                                                         [inversion.log_det_regularization_matrix_term],
#                                                                         noise_terms)
#
#             assert evidences[0] == fit.evidences[0]
#
#             fast_evidence = lensing_fitters.fast_likelihood_from_lensing_image_and_tracer(lensing_image=li_manual,
#                                                                                           tracer=tracer)
#             assert fast_evidence == fit.evidences[0]
#
#
# class TestHyperLensingInversionFit:
#
#     class TestRectangularInversion:
#
#         def test__image_all_1s__direct_image_to_source_mapping__perfect_fit_even_with_regularization(self):
#
#             im = np.array([[0.0, 0.0, 0.0, 0.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 1.0, 1.0, 1.0, 0.0],
#                            [0.0, 0.0, 0.0, 0.0, 0.0]]).view(image.Image)
#             ma = np.array([[True, True, True, True, True],
#                            [True, False, False, False, True],
#                            [True, False, False, False, True],
#                            [True, False, False, False, True],
#                            [True, True, True, True, True]])
#             ma = masks.Mask(ma, pixel_scale=1.0)
#             psf = image.PSF(array=np.array([[0.0, 0.0, 0.0],
#                                             [0.0, 1.0, 0.0],
#                                             [0.0, 0.0, 0.0]]), pixel_scale=1.0)
#             im = image.Image(im, pixel_scale=1.0, psf=psf, noise_maps=np.ones((5, 5)))
#             hyper_model_image = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
#             hyper_galaxy_images = [np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])]
#             li = lensing_image.LensingHyperImage(im, ma, hyper_model_image=hyper_model_image,
#                                                  hyper_galaxy_images=hyper_galaxy_images,
#                                                  hyper_minimum_values=[0.0, 0.0],
#                                                  sub_grid_size=2)
#
#             hyper_galaxy = g.HyperGalaxy(contribution_factor=0.0, noise_factor=1.0, noise_power=1.0)
#
#             galaxy_pix = g.Galaxy(pixelization=pixelizations.Rectangular(shape=(3, 3)),
#                                   regularization=regularization.Constant(coefficients=(1.0,)),
#                                   hyper_galaxy=hyper_galaxy)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g.Galaxy()], source_galaxies=[galaxy_pix],
#                                                          image_plane_grids=[li.grid_stacks], borders=None)
#
#             fit = lensing_fitters.HyperLensingInversionFit(lensing_hyper_images=[li], tracer=tracer)
#
#             curvature_matrix = np.array([[0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                          [0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                          [0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                          [0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                          [0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0],
#                                          [0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0],
#                                          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0],
#                                          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0],
#                                          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25]])
#             regularization_matrix = np.array([[2.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
#                                               [-1.0, 3.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0],
#                                               [0.0, -1.0, 2.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
#                                               [-1.0, 0.0, 0.0, 3.0, -1.0, 0.0, -1.0, 0.0, 0.0],
#                                               [0.0, -1.0, 0.0, -1.0, 4.0, -1.0, 0.0, -1.0, 0.0],
#                                               [0.0, 0.0, -1.0, 0.0, -1.0, 3.0, 0.0, 0.0, - 1.0],
#                                               [0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 2.0, -1.0, 0.0],
#                                               [0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 3.0, -1.0],
#                                               [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 2.0]])
#             regularization_matrix = regularization_matrix + 1e-8 * np.identity(9)
#             curvature_reg_matrix = curvature_matrix + regularization_matrix
#
#             scaled_chi_sq_term = 0.0
#             gl_term = 1e-8
#             det_curvature_reg_term = np.log(np.linalg.det(curvature_reg_matrix))
#             det_regularization_term = np.log(np.linalg.det(regularization_matrix))
#             scaled_noise_term = 9.0 * np.log(2 * np.pi * 2.0 ** 2.0)
#
#             scaled_evidence = -0.5 * (scaled_chi_sq_term + gl_term + det_curvature_reg_term - det_regularization_term +
#                                       scaled_noise_term)
#
#             assert fit.scaled_evidences == pytest.approx(scaled_evidence, 1e-4)
#
#     class TestAbstractLogic:
#
#         def test__logic_in_abstract_fit(self, li_hyper_no_blur):
#             galaxy_pix = g.Galaxy(pixelization=pixelizations.Rectangular(shape=(3, 3)),
#                                   regularization=regularization.Constant(coefficients=(1.0,)))
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[g.Galaxy()], source_galaxies=[galaxy_pix],
#                                                          image_plane_grids=[li_hyper_no_blur.grid_stacks],
#                                                          borders=None)
#
#             fit = lensing_fitters.HyperLensingInversionFit(lensing_hyper_images=[li_hyper_no_blur], tracer=tracer)
#
#             assert fit.total_inversions == 1
#
#     class TestCompareToManual:
#
#         def test___manual_image_and_psf(self, li_hyper_manual):
#
#             pix = pixelizations.Rectangular(shape=(3, 3))
#             mapper = pix.mapper_from_grids_and_border(li_hyper_manual.grid_stacks, li_hyper_manual.borders)
#             reg = regularization.Constant(coefficients=(1.0,))
#
#             hyper_galaxy = g.HyperGalaxy(contribution_factor=4.0, noise_factor=2.0, noise_power=3.0)
#             hyp_galaxy = g.Galaxy(hyper_galaxy=hyper_galaxy)
#             inv_galaxy = g.Galaxy(pixelization=pix, regularization=reg)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[hyp_galaxy, hyp_galaxy],
#                                                          source_galaxies=[inv_galaxy],
#                                                          image_plane_grids=[li_hyper_manual.grid_stacks],
#                                                          borders=None)
#
#             fit = lensing_fitters.fit_lensing_image_with_tracer(lensing_image=li_hyper_manual, tracer=tracer)
#
#             inversion = inversions.inversion_from_lensing_image_mapper_and_regularization(mapper=mapper,
#                                                                                           regularization=reg, image=li_hyper_manual, noise_maps=li_hyper_manual.noise_map_,
#                                                                                           convolver=li_hyper_manual.convolver_mapping_matrix)
#
#             residual_map = fitting_util.residuals_from_data_mask_and_model_data([li_hyper_manual],
#                                                                              [inversion.reconstructed_data_vector])
#             chi_squared_map = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map, [li_hyper_manual.noise_map_])
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(li_hyper_manual.noise_map_) == \
#                    pytest.approx(fit.noise_maps[0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(inversion.reconstructed_data_vector) == \
#                    pytest.approx(fit.model_datas[0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(residual_map[0]) == \
#                    pytest.approx(fit.residual_map[0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(chi_squared_map[0]) == \
#                    pytest.approx(fit.chi_squared_map[0], 1e-4)
#
#             chi_squared_terms = fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=chi_squared_map)
#             noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=[li_hyper_manual.noise_map_])
#
#             likelihoods_with_regularization = \
#                 fitting_util.likelihood_with_regularization_from_chi_squared_term_regularization_and_noise_term(chi_squared_terms,
#                                                                                                                 [inversion.regularization_term], noise_terms)
#
#             assert likelihoods_with_regularization[0] == pytest.approx(fit.likelihoods_with_regularization[0], 1e-2)
#
#             evidences = fitting_util.evidence_from_reconstruction_terms(chi_squared_terms, [inversion.regularization_term],
#                                                                         [inversion.log_det_curvature_reg_matrix_term],
#                                                                         [inversion.log_det_regularization_matrix_term],
#                                                                         noise_terms)
#
#             assert evidences[0] == fit.evidences[0]
#
#             contributions = fitting_util.contributions_from_hyper_images_and_galaxies(li_hyper_manual.hyper_model_image,
#                                                                                  li_hyper_manual.hyper_galaxy_images, [hyper_galaxy, hyper_galaxy],
#                                                                                  li_hyper_manual.hyper_minimum_values)
#
#             scaled_noise_maps = fitting_util.scaled_noise_maps_from_fitting_hyper_images_contributions_and_hyper_galaxies(
#                 fitting_hyper_images=[li_hyper_manual], contributions_=[contributions], hyper_galaxies=[hyper_galaxy,
#                                                                                                         hyper_galaxy])
#
#             scaled_inversion = inversions.inversion_from_lensing_image_mapper_and_regularization(mapper=mapper,
#                                                                                                  regularization=reg, image=li_hyper_manual, noise_maps=scaled_noise_maps[0],
#                                                                                                  convolver=li_hyper_manual.convolver_mapping_matrix)
#
#             scaled_residuals = fitting_util.residuals_from_data_mask_and_model_data(datas=[li_hyper_manual],
#                                                                                     model_data=[scaled_inversion.reconstructed_data_vector])
#
#             scaled_chi_squareds = fitting_util.chi_squareds_from_residuals_and_noise_map(scaled_residuals,
#                                                                                          scaled_noise_maps)
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[0]) == \
#                    pytest.approx(fit.contributions[0][0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[1]) == \
#                    pytest.approx(fit.contributions[0][1], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_noise_maps[0]) == \
#                    pytest.approx(fit.scaled_noise_map, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_residuals[0]) == \
#                    pytest.approx(fit.scaled_residual, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_chi_squareds[0]) == \
#                    pytest.approx(fit.scaled_chi_squared, 1e-4)
#
#             scaled_chi_squared_terms= fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=scaled_chi_squareds)
#             scaled_noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=scaled_noise_maps)
#
#             scaled_evidences = fitting_util.evidence_from_reconstruction_terms(scaled_chi_squared_terms,
#                                                                                [scaled_inversion.regularization_term], [scaled_inversion.log_det_curvature_reg_matrix_term],
#                                                                                [scaled_inversion.log_det_regularization_matrix_term], scaled_noise_terms)
#             assert scaled_evidences[0] == fit.scaled_evidences[0]
#
#             fast_scaled_evidence = \
#                 lensing_fitters.fast_likelihood_from_lensing_image_and_tracer(lensing_image=li_hyper_manual,
#                                                                               tracer=tracer)
#             assert fast_scaled_evidence == scaled_evidences[0]
#
#
# class TestLensingProfileInversionFit:
#
#     class TestModelImagesOfPLanes:
#
#         def test___model_images_of_planes_are_profile_and_inversion_images(self, li_manual):
#
#             galaxy_light = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
#
#             pix = pixelizations.Rectangular(shape=(3, 3))
#             reg = regularization.Constant(coefficients=(1.0,))
#             galaxy_pix = g.Galaxy(pixelization=pix, regularization=reg)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[galaxy_light], source_galaxies=[galaxy_pix],
#                                                          image_plane_grids=[li_manual.grid_stacks],
#                                                          borders=None)
#
#             fit = lensing_fitters.fit_lensing_image_with_tracer(lensing_image=li_manual, tracer=tracer)
#
#             assert (fit.model_images_of_planes[0][0] == fit.profile_model_images[0]).all()
#             assert (fit.model_images_of_planes[0][1] == fit.inversion_model_images[0]).all()
#
#     class TestCompareToManual:
#
#         def test___manual_image_and_psf(self, li_manual):
#
#             galaxy_light = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0))
#
#             pix = pixelizations.Rectangular(shape=(3, 3))
#             reg = regularization.Constant(coefficients=(1.0,))
#             galaxy_pix = g.Galaxy(pixelization=pix, regularization=reg)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[galaxy_light], source_galaxies=[galaxy_pix],
#                                                          image_plane_grids=[li_manual.grid_stacks],
#                                                          borders=None)
#
#             fit = lensing_fitters.fit_lensing_image_with_tracer(lensing_image=li_manual, tracer=tracer)
#
#             image_im = tracer.image_plane_images_
#             blurring_im = tracer.image_plane_blurring_images_
#             profile_model_images = lensing_fitting_util.blurred_image_from_1d_unblurred_and_blurring_images(image_=image_im,
#                                                                                      blurring_image_=blurring_im, convolver=[li_manual.convolver_image])
#             profile_subtracted_images = [li_manual[:] - profile_model_images[0]]
#
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(profile_model_images[0]) == \
#                    pytest.approx(fit.profile_model_image, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(profile_subtracted_images[0]) == \
#                    pytest.approx(fit.profile_subtracted_image, 1e-4)
#
#             mapper = pix.mapper_from_grids_and_border(li_manual.grid_stacks, None)
#             inversion = inversions.inversion_from_lensing_image_mapper_and_regularization(mapper=mapper, regularization=reg,
#                                                                                           image=profile_subtracted_images[0],
#                                                                                           noise_maps=li_manual.noise_map_,
#                                                                                           convolver=li_manual.convolver_mapping_matrix)
#
#             model_images = [profile_model_images[0] + inversion.reconstructed_data_vector]
#             residual_map = fitting_util.residuals_from_data_mask_and_model_data(datas=[li_manual], model_data=model_images)
#             chi_squared_map = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map=residual_map,
#                                                                                   noise_maps=[li_manual.noise_map_])
#
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(li_manual.noise_map_) == \
#                    pytest.approx(fit.noise_maps, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(inversion.reconstructed_data_vector) == \
#                    pytest.approx(fit.inversion_model_image, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(model_images[0]) == \
#                    pytest.approx(fit.model_image, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(residual_map[0]) ==\
#                    pytest.approx(fit.residual, 1e-4)
#             assert li_manual.grid_stacks.regular.scaled_array_from_array_1d(chi_squared_map[0]) == \
#                    pytest.approx(fit.chi_squared, 1e-4)
#
#             chi_squared_terms = fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map=chi_squared_map)
#             noise_terms = fitting_util.noise_term_from_mask_and_noise_map(noise_maps=[li_manual.noise_map_])
#             evidences = fitting_util.evidence_from_reconstruction_terms(chi_squared_terms,
#                                                                         [inversion.regularization_term],
#                                                                         [inversion.log_det_curvature_reg_matrix_term],
#                                                                         [inversion.log_det_regularization_matrix_term],
#                                                                         noise_terms)
#
#             assert evidences[0] == fit.evidences[0]
#
#             fast_evidence = lensing_fitters.fast_likelihood_from_lensing_image_and_tracer(lensing_image=li_manual,
#                                                                                           tracer=tracer)
#             assert fast_evidence == evidences[0]
#
#
# class TestHyperLensingProfileInversionFit:
#
#     class TestCompareToManual:
#
#         def test___manual_image_and_psf(self, li_hyper_manual):
#
#             pix = pixelizations.Rectangular(shape=(3, 3))
#             reg = regularization.Constant(coefficients=(1.0,))
#
#             hyper_galaxy = g.HyperGalaxy(contribution_factor=4.0, noise_factor=2.0, noise_power=3.0)
#             hyp_galaxy = g.Galaxy(light_profile=lp.EllipticalSersic(intensity=1.0), hyper_galaxy=hyper_galaxy)
#             inv_galaxy = g.Galaxy(pixelization=pix, regularization=reg)
#
#             tracer = ray_tracing.TracerImageSourcePlanes(lens_galaxies=[hyp_galaxy, hyp_galaxy],
#                                                          source_galaxies=[inv_galaxy],
#                                                          image_plane_grids=[li_hyper_manual.grid_stacks],
#                                                          borders=None)
#
#             fit = lensing_fitters.fit_lensing_image_with_tracer(lensing_image=li_hyper_manual, tracer=tracer)
#
#             image_im = tracer.image_plane_images_
#             blurring_im = tracer.image_plane_blurring_images_
#             profile_model_images = lensing_fitting_util.blurred_image_from_1d_unblurred_and_blurring_images(image_=image_im,
#                                                                                      blurring_image_=blurring_im, convolver=[li_hyper_manual.convolver_image])
#             profile_subtracted_images = [li_hyper_manual[:] - profile_model_images[0]]
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(profile_model_images[0]) == \
#                    pytest.approx(fit.profile_model_image, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(profile_subtracted_images[0]) == \
#                    pytest.approx(fit.profile_subtracted_image, 1e-4)
#
#             mapper = pix.mapper_from_grids_and_border(li_hyper_manual.grid_stacks, li_hyper_manual.borders)
#             inversion = inversions.inversion_from_lensing_image_mapper_and_regularization(mapper=mapper, regularization=reg,
#                                                                                           image=profile_subtracted_images[0], noise_maps=li_hyper_manual.noise_map_,
#                                                                                           convolver=li_hyper_manual.convolver_mapping_matrix)
#
#             model_images = [profile_model_images[0] + inversion.reconstructed_data_vector]
#             residual_map = fitting_util.residuals_from_data_mask_and_model_data([li_hyper_manual], model_images)
#             chi_squared_map = fitting_util.chi_squareds_from_residuals_and_noise_map(residual_map, [li_hyper_manual.noise_map_])
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(li_hyper_manual.noise_map_) == \
#                    pytest.approx(fit.noise_maps, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(inversion.reconstructed_data_vector) == \
#                    pytest.approx(fit.inversion_model_image, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(model_images[0]) ==\
#                    pytest.approx(fit.model_data, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(residual_map[0]) == \
#                    pytest.approx(fit.residual, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(chi_squared_map[0]) ==\
#                    pytest.approx(fit.chi_squared, 1e-4)
#
#             chi_squared_terms = fitting_util.chi_squared_term_from_chi_squareds(chi_squared_map)
#             noise_terms = fitting_util.noise_term_from_mask_and_noise_map([li_hyper_manual.noise_map_])
#             evidences = fitting_util.evidence_from_reconstruction_terms(chi_squared_terms, [inversion.regularization_term],
#                                                                         [inversion.log_det_curvature_reg_matrix_term],
#                                                                         [inversion.log_det_regularization_matrix_term],
#                                                                         noise_terms)
#
#             assert evidences[0] == fit.evidences[0]
#
#             contributions = fitting_util.contributions_from_hyper_images_and_galaxies(li_hyper_manual.hyper_model_image,
#                                                                                  li_hyper_manual.hyper_galaxy_images, [hyper_galaxy, hyper_galaxy],
#                                                                                  li_hyper_manual.hyper_minimum_values)
#
#             scaled_noise_maps = fitting_util.scaled_noise_maps_from_fitting_hyper_images_contributions_and_hyper_galaxies(
#                 fitting_hyper_images=[li_hyper_manual], contributions_=[contributions], hyper_galaxies=[hyper_galaxy,
#                                                                                                         hyper_galaxy])
#
#             scaled_inversion = inversions.inversion_from_lensing_image_mapper_and_regularization(mapper=mapper,
#                                                                                                  regularization=reg, image=profile_subtracted_images[0], noise_maps=scaled_noise_maps[0],
#                                                                                                  convolver=li_hyper_manual.convolver_mapping_matrix)
#
#             scaled_model_images = [profile_model_images[0] + scaled_inversion.reconstructed_data_vector]
#
#             scaled_residuals = fitting_util.residuals_from_data_mask_and_model_data(datas=[li_hyper_manual],
#                                                                                     model_data=scaled_model_images)
#
#             scaled_chi_squareds = fitting_util.chi_squareds_from_residuals_and_noise_map(scaled_residuals,
#                                                                                          scaled_noise_maps)
#
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[0]) == \
#                    pytest.approx(fit.contributions[0][0], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(contributions[1]) == \
#                    pytest.approx(fit.contributions[0][1], 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_noise_maps[0]) == \
#                    pytest.approx(fit.scaled_noise_map, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_model_images[0]) == \
#                    pytest.approx(fit.scaled_model_image, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_residuals[0]) == \
#                    pytest.approx(fit.scaled_residual, 1e-4)
#             assert li_hyper_manual.grid_stacks.regular.scaled_array_from_array_1d(scaled_chi_squareds[0]) == \
#                    pytest.approx(fit.scaled_chi_squared, 1e-4)
#
#             scaled_chi_squared_terms = fitting_util.chi_squared_term_from_chi_squareds(scaled_chi_squareds)
#             scaled_noise_terms = fitting_util.noise_term_from_mask_and_noise_map(scaled_noise_maps)
#             scaled_evidence = fitting_util.evidence_from_reconstruction_terms(
#                 scaled_chi_squared_terms, [scaled_inversion.regularization_term],
#                 [scaled_inversion.log_det_curvature_reg_matrix_term],
#                 [scaled_inversion.log_det_regularization_matrix_term],
#                 scaled_noise_terms)
#
#             assert scaled_evidence[0] == fit.scaled_evidences[0]
#
#             fast_scaled_evidence = lensing_fitters.fast_likelihood_from_lensing_image_and_tracer(
#                 lensing_image=li_hyper_manual, tracer=tracer)
#
#             assert fast_scaled_evidence == scaled_evidence[0]
#
#
# class MockTracerPositions:
#
#     def __init__(self, positions, noise=None):
#         self.positions = positions
#         self.noise = noise
#
#
# class TestPositionFit:
#
#     def test__x1_positions__mock_position_tracer__maximum_separation_is_correct(self):
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [0.0, 1.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == 1.0
#
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [1.0, 1.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(2)
#
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [1.0, 3.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(np.square(1.0) + np.square(3.0))
#
#         tracer = MockTracerPositions(positions=[np.array([[-2.0, -4.0], [1.0, 3.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(np.square(3.0) + np.square(7.0))
#
#         tracer = MockTracerPositions(positions=[np.array([[8.0, 4.0], [-9.0, -4.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(np.square(17.0) + np.square(8.0))
#
#     def test_multiple_positions__mock_position_tracer__maximum_separation_is_correct(self):
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [0.0, 1.0], [0.0, 0.5]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == 1.0
#
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [0.0, 0.0], [3.0, 3.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(18)
#
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [1.0, 1.0], [3.0, 3.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(18)
#
#         tracer = MockTracerPositions(positions=[np.array([[-2.0, -4.0], [1.0, 3.0], [0.1, 0.1], [-0.1, -0.1],
#                                                           [0.3, 0.4], [-0.6, 0.5]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(np.square(3.0) + np.square(7.0))
#
#         tracer = MockTracerPositions(positions=[np.array([[8.0, 4.0], [8.0, 4.0], [-9.0, -4.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.maximum_separations[0] == np.sqrt(np.square(17.0) + np.square(8.0))
#
#     def test_multiple_sets_of_positions__multiple_sets_of_max_distances(self):
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [0.0, 1.0], [0.0, 0.5]]),
#                                                 np.array([[0.0, 0.0], [0.0, 0.0], [3.0, 3.0]]),
#                                                 np.array([[0.0, 0.0], [1.0, 1.0], [3.0, 3.0]])])
#
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#
#         assert fit.maximum_separations[0] == 1.0
#         assert fit.maximum_separations[1] == np.sqrt(18)
#         assert fit.maximum_separations[2] == np.sqrt(18)
#
#     def test__likelihood__is_sum_of_separations_divided_by_noise(self):
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [0.0, 1.0], [0.0, 0.5]]),
#                                                 np.array([[0.0, 0.0], [0.0, 0.0], [3.0, 3.0]]),
#                                                 np.array([[0.0, 0.0], [1.0, 1.0], [3.0, 3.0]])])
#
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#         assert fit.chi_squared_map[0] == 1.0
#         assert fit.chi_squared_map[1] == pytest.approx(18.0, 1e-4)
#         assert fit.chi_squared_map[2] == pytest.approx(18.0, 1e-4)
#         assert fit.likelihood == pytest.approx(-0.5 * (1.0 + 18 + 18), 1e-4)
#
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=2.0)
#         assert fit.chi_squared_map[0] == (1.0 / 2.0) ** 2.0
#         assert fit.chi_squared_map[1] == pytest.approx((np.sqrt(18.0) / 2.0) ** 2.0, 1e-4)
#         assert fit.chi_squared_map[2] == pytest.approx((np.sqrt(18.0) / 2.0) ** 2.0, 1e-4)
#         assert fit.likelihood == pytest.approx(-0.5 * ((1.0 / 2.0) ** 2.0 + (np.sqrt(18.0) / 2.0) ** 2.0 +
#                                                        (np.sqrt(18.0) / 2.0) ** 2.0), 1e-4)
#
#     def test__threshold__if_not_met_returns_ray_tracing_exception(self):
#         tracer = MockTracerPositions(positions=[np.array([[0.0, 0.0], [0.0, 1.0]])])
#         fit = lensing_fitters.PositionFit(positions=tracer.positions, noise=1.0)
#
#         assert fit.maximum_separation_within_threshold(threshold=100.0) == True
#         assert fit.maximum_separation_within_threshold(threshold=0.1) == False
