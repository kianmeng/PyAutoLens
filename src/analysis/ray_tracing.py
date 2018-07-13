from src import exc

from astropy import constants
import math


class Tracer(object):

    def __init__(self, lens_galaxies, source_galaxies, masked_image, cosmology=None):
        """The ray-tracing calculations, defined by a lensing system with just one image-plane and source-plane.

        This has no associated cosmology, thus all calculations are performed in arc seconds and galaxies do not need
        known redshift measurements. For computational efficiency, it is recommend this ray-tracing class is used for
        lens modeling, provided cosmological information is not necessary.

        Parameters
        ----------
        lens_galaxies : [Galaxy]
            The list of lens galaxies in the image-plane.
        source_galaxies : [Galaxy]
            The list of source galaxies in the source-plane.
        masked_image : MaskedImage
            The image-plane coordinate masked_image where ray-tracing calculation are performed, (this includes the
            image-grid, sub-grid, blurring-grid, etc.).
        """
        self.cosmology = cosmology
        self.image_plane = Plane(lens_galaxies, masked_image, previous_redshift=None,
                                 next_redshift=source_galaxies[0].redshift, cosmology=cosmology,
                                 compute_deflections=True)

        source_plane_masked_image = self.image_plane.trace_to_next_plane()

        self.source_plane = Plane(source_galaxies, source_plane_masked_image,
                                  previous_redshift=lens_galaxies[0].redshift,
                                  next_redshift=None, cosmology=cosmology, compute_deflections=False)

    def generate_image_of_galaxy_light_profiles(self, mapping):
        """Generate the image of the galaxies over the entire ray trace."""
        return self.image_plane.generate_image_of_galaxy_light_profiles(
            mapping) + self.source_plane.generate_image_of_galaxy_light_profiles(mapping)

    def generate_blurring_image_of_galaxy_light_profiles(self):
        """Generate the image of all galaxy light profiles in the blurring regions of the image."""
        return self.image_plane.generate_blurring_image_of_galaxy_light_profiles(
        ) + self.source_plane.generate_blurring_image_of_galaxy_light_profiles()

    def generate_pixelization_matrices_of_source_galaxy(self, mapping):
        return self.source_plane.generate_pixelization_matrices_of_galaxy(mapping)


class MultiTracer(object):

    def __init__(self, galaxies, masked_image, cosmology, redshift_threshold=0.0):

        self.cosmology = cosmology
        self.galaxies_redshift_order = sorted(galaxies, key=lambda galaxy: galaxy.redshift, reverse=False)

        # Ideally we'd extract the planes_red_Shfit order from the list above. However, I dont know how to extract it
        # Using a list of class attributes so make a list of redshifts for now.

        galaxy_redshifts = list(map(lambda galaxy: galaxy.redshift, self.galaxies_redshift_order))
        self.planes_redshift_order = [redshift for i, redshift in enumerate(galaxy_redshifts)
                                      if redshift not in galaxy_redshifts[:i]]

        # TODO : Idea is to get a list of all galaxies in each plane - can you clean up the logic below?

        self.planes_galaxies = []

        for (i, plane_redshift) in enumerate(self.planes_redshift_order):
            self.planes_galaxies.append(list(map(lambda galaxy:
                                                 galaxy if galaxy.redshift == plane_redshift else None,
                                                 self.galaxies_redshift_order)))
            self.planes_galaxies[i] = list(filter(None, self.planes_galaxies[i]))

        self.planes = []

        for i in range(0, len(self.planes_redshift_order)):

            if i == 0:
                compute_deflections = True
                previous_redshift = None
                next_redshift = self.planes_redshift_order[i + 1]
                new_grid = masked_image
            elif i < len(self.planes_redshift_order) - 1:
                compute_deflections = True
                previous_redshift = self.planes_redshift_order[i - 1]
                next_redshift = self.planes_redshift_order[i + 1]
                new_grid = self.planes[i - 1].trace_to_next_plane()
            elif i == len(self.planes_redshift_order) - 1:
                compute_deflections = False
                previous_redshift = self.planes_redshift_order[i - 1]
                next_redshift = None
                new_grid = self.planes[i - 1].trace_to_next_plane()
            else:
                raise exc.RayTracingException('A galaxy was not corrected allocate its previous / next redshifts')

            self.planes.append(Plane(galaxies=self.planes_galaxies[i], masked_image=new_grid,
                                     previous_redshift=previous_redshift, next_redshift=next_redshift,
                                     cosmology=cosmology, compute_deflections=compute_deflections))


class Plane(object):

    def __init__(self, galaxies, masked_image, previous_redshift=None, next_redshift=None, cosmology=None,
                 compute_deflections=True):
        """

        Represents a plane, which is a set of galaxies and masked_image at a given redshift in the lens ray-tracing
        calculation.

        The image-plane coordinates are defined on the observed image's uniform regular grid_coords. Calculating its
        model images from its light profiles exploits this uniformity to perform more efficient and precise calculations
        via an iterative sub-griding approach.

        The light profiles of galaxies at higher redshifts (and therefore in different lens-planes) can be assigned to
        the ImagePlane. This occurs when:

        1) The efficiency and precision offered by computing the light profile on a uniform grid_coords is preferred and
        won't lead noticeable inaccuracy. For example, computing the light profile of the main lens galaxy, ignoring
        minor lensing effects due to a low mass foreground substructure.

        2) When evaluating the light profile in its lens-plane is inaccurate. For example, when modeling the
        point-source images of a lensed quasar, effects like micro-lensing mean lens-plane modeling will be inaccurate.


        Parameters
        ----------
        galaxies : [Galaxy]
            The galaxies in the plane.
        masked_image : masked_image.GridCoordsCollection
            The masked_image of (x,y) coordinates in the plane, including the image grid_coords, sub-grid_coords,
            blurring, grid_coords, etc.
        """

        if cosmology is not None:

            self.arcsec_per_kpc = cosmology.arcsec_per_kpc_proper(z=galaxies[0].redshift)
            self.kpc_per_arcsec = 1.0 / self.arcsec_per_kpc
            self.ang_to_earth_kpc = cosmology.angular_diameter_distance(z=galaxies[0].redshift).to('kpc')

            if previous_redshift is not None:
                self.ang_to_previous_plane_kpc = \
                    cosmology.angular_diameter_distance_z1z2(previous_redshift, galaxies[0].redshift).to('kpc')

            if next_redshift is not None:
                self.ang_to_next_plane_kpc = \
                    cosmology.angular_diameter_distance_z1z2(galaxies[0].redshift, next_redshift).to('kpc')
                self.ang_next_plane_to_earth_kpc = cosmology.angular_diameter_distance(z=next_redshift).to('kpc')

                # noinspection PyUnresolvedReferences
                constant_kpc = constants.c.to('kpc / s').value ** 2.0 / (
                        4 * math.pi * constants.G.to('kpc3 / M_sun s2').value)

                self.critical_density_kpc = constant_kpc * self.ang_next_plane_to_earth_kpc / (
                            self.ang_to_next_plane_kpc * self.ang_to_earth_kpc)

                self.critical_density_arcsec = self.critical_density_kpc * self.kpc_per_arcsec ** 2.0

        self.galaxies = galaxies
        self.masked_image = masked_image
        if compute_deflections:
            self.deflections = self.masked_image.deflection_masked_image_for_galaxies(self.galaxies)

    def trace_to_next_plane(self):
        """Trace the masked_image to the next plane.

        NOTE : This does not work for multi-plane lensing, which requires one to use the previous plane's deflection
        angles to perform the tracing. I guess we'll ultimately call this class 'LensPlanes' and have it as a list.
        """
        return self.masked_image.traced_masked_image_for_deflections(self.deflections)

    def generate_image_of_galaxy_light_profiles(self, mapping):
        """Generate the image of the galaxies in this plane."""
        return self.masked_image.sub.intensities_via_grid(self.galaxies, mapping)

    def generate_blurring_image_of_galaxy_light_profiles(self):
        """Generate the image of the galaxies in this plane."""
        return self.masked_image.blurring.intensities_via_grid(self.galaxies)

    def generate_pixelization_matrices_of_galaxy(self, mapping):

        pixelized_galaxies = list(filter(lambda galaxy: galaxy.has_pixelization, self.galaxies))

        if len(pixelized_galaxies) == 0:
            return None
        if len(pixelized_galaxies) == 1:
            return pixelized_galaxies[0].pixelization.inversion_from_pix_masked_image(self.masked_image.image,
                                                                                      self.masked_image.sub, mapping)
        elif len(pixelized_galaxies) > 1:
            raise exc.PixelizationException('The number of galaxies with pixelizations in one plane is above 1')
