import numpy as np
from typing import Dict, Optional

from autoconf import conf
import autoarray as aa
import autogalaxy as ag

from autolens.lens.model.preloads import Preloads


class FitImaging(aa.FitImaging):
    def __init__(
        self,
        imaging,
        tracer,
        hyper_image_sky=None,
        hyper_background_noise=None,
        use_hyper_scaling=True,
        settings_pixelization=aa.SettingsPixelization(),
        settings_inversion=aa.SettingsInversion(),
        preloads=Preloads(),
        profiling_dict: Optional[Dict] = None,
    ):
        """
        An  lens fitter, which contains the tracer's used to perform the fit and functions to manipulate \
        the lens dataset's hyper_galaxies.

        Parameters
        -----------
        tracer : Tracer
            The tracer, which describes the ray-tracing and strong lens configuration.
        scaled_array_2d_from_array_1d : func
            A function which maps the 1D lens hyper_galaxies to its unmasked 2D arrays.
        """

        self.tracer = tracer

        self.hyper_image_sky = hyper_image_sky
        self.hyper_background_noise = hyper_background_noise
        self.use_hyper_scaling = use_hyper_scaling

        self.settings_pixelization = settings_pixelization
        self.settings_inversion = settings_inversion

        self.preloads = preloads

        self.profiling_dict = profiling_dict

        if use_hyper_scaling:

            image = hyper_image_from_image_and_hyper_image_sky(
                image=imaging.image, hyper_image_sky=hyper_image_sky
            )

            noise_map = hyper_noise_map_from_noise_map_tracer_and_hyper_background_noise(
                noise_map=imaging.noise_map,
                tracer=tracer,
                hyper_background_noise=hyper_background_noise,
            )

        else:

            image = imaging.image
            noise_map = imaging.noise_map

        if preloads.blurred_image is None:

            self.blurred_image = tracer.blurred_image_2d_from_grid_and_convolver(
                grid=imaging.grid,
                convolver=imaging.convolver,
                blurring_grid=imaging.blurring_grid,
            )

        else:

            self.blurred_image = preloads.blurred_image

        self.profile_subtracted_image = image - self.blurred_image

        if not tracer.has_pixelization:

            inversion = None
            model_image = self.blurred_image

        else:

            inversion = tracer.inversion_imaging_from_grid_and_data(
                grid=imaging.grid_inversion,
                image=self.profile_subtracted_image,
                noise_map=noise_map,
                convolver=imaging.convolver,
                w_tilde=imaging.w_tilde,
                settings_pixelization=settings_pixelization,
                settings_inversion=settings_inversion,
                preloads=preloads,
            )

            model_image = self.blurred_image + inversion.mapped_reconstructed_image

        fit = aa.FitData(
            data=image,
            noise_map=noise_map,
            model_data=model_image,
            mask=imaging.mask,
            inversion=inversion,
            use_mask_in_fit=False,
            profiling_dict=profiling_dict,
        )

        super().__init__(imaging=imaging, fit=fit, profiling_dict=profiling_dict)

    @property
    def grid(self):
        return self.imaging.grid

    @property
    def galaxy_model_image_dict(self) -> {ag.Galaxy: np.ndarray}:
        """
        A dictionary associating galaxies with their corresponding model images
        """
        galaxy_model_image_dict = self.tracer.galaxy_blurred_image_dict_from_grid_and_convolver(
            grid=self.grid,
            convolver=self.imaging.convolver,
            blurring_grid=self.imaging.blurring_grid,
        )

        # TODO : Extend to multiple inversioons across Planes

        for plane_index in self.tracer.plane_indexes_with_pixelizations:

            galaxy_model_image_dict.update(
                {
                    self.tracer.planes[plane_index].galaxies[
                        0
                    ]: self.inversion.mapped_reconstructed_image
                }
            )

        return galaxy_model_image_dict

    @property
    def model_images_of_planes(self):

        model_images_of_planes = self.tracer.blurred_images_of_planes_from_grid_and_psf(
            grid=self.grid,
            psf=self.imaging.psf,
            blurring_grid=self.imaging.blurring_grid,
        )

        for plane_index in self.tracer.plane_indexes_with_pixelizations:

            model_images_of_planes[
                plane_index
            ] += self.inversion.mapped_reconstructed_image

        return model_images_of_planes

    @property
    def subtracted_images_of_planes(self):

        subtracted_images_of_planes = []

        model_images_of_planes = self.model_images_of_planes

        for galaxy_index in range(len(self.tracer.planes)):

            other_planes_model_images = [
                model_image
                for i, model_image in enumerate(model_images_of_planes)
                if i != galaxy_index
            ]

            subtracted_image = self.image - sum(other_planes_model_images)

            subtracted_images_of_planes.append(subtracted_image)

        return subtracted_images_of_planes

    @property
    def unmasked_blurred_image(self):
        return self.tracer.unmasked_blurred_image_2d_from_grid_and_psf(
            grid=self.grid, psf=self.imaging.psf
        )

    @property
    def unmasked_blurred_image_of_planes(self):
        return self.tracer.unmasked_blurred_image_of_planes_from_grid_and_psf(
            grid=self.grid, psf=self.imaging.psf
        )

    @property
    def unmasked_blurred_image_of_planes_and_galaxies(self):
        return self.tracer.unmasked_blurred_image_of_planes_and_galaxies_from_grid_and_psf(
            grid=self.grid, psf=self.imaging.psf
        )

    @property
    def total_inversions(self):
        return len(list(filter(None, self.tracer.regularizations_of_planes)))

    def refit_with_new_preloads(self, preloads):

        if self.profiling_dict is not None:
            profiling_dict = {}
        else:
            profiling_dict = None

        return FitImaging(
            imaging=self.imaging,
            tracer=self.tracer,
            hyper_image_sky=self.hyper_image_sky,
            hyper_background_noise=self.hyper_background_noise,
            use_hyper_scaling=self.use_hyper_scaling,
            settings_pixelization=self.settings_pixelization,
            settings_inversion=self.settings_inversion,
            preloads=preloads,
            profiling_dict=profiling_dict,
        )


def hyper_image_from_image_and_hyper_image_sky(image, hyper_image_sky):

    if hyper_image_sky is not None:
        return hyper_image_sky.hyper_image_from_image(image=image)
    else:
        return image


def hyper_noise_map_from_noise_map_tracer_and_hyper_background_noise(
    noise_map, tracer, hyper_background_noise
):

    hyper_noise_map = tracer.hyper_noise_map_from_noise_map(noise_map=noise_map)

    if hyper_background_noise is not None:
        noise_map = hyper_background_noise.hyper_noise_map_from_noise_map(
            noise_map=noise_map
        )

    if hyper_noise_map is not None:
        noise_map = noise_map + hyper_noise_map
        noise_map_limit = conf.instance["general"]["hyper"]["hyper_noise_limit"]
        noise_map[noise_map > noise_map_limit] = noise_map_limit

    return noise_map
