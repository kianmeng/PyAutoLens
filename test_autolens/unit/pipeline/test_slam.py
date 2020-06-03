import autolens as al


class TestHyper:
    def test__hyper_fixed_after_source(self):
        hyper = al.slam.Hyper(hyper_fixed_after_source=False)
        assert hyper.hyper_fixed_after_source_tag == ""

        hyper = al.slam.Hyper(hyper_fixed_after_source=True)
        assert hyper.hyper_fixed_after_source_tag == "_fixed"

    def test__hyper_tag(self):

        hyper = al.slam.Hyper(
            hyper_galaxies=True,
            hyper_image_sky=True,
            hyper_background_noise=True,
            hyper_fixed_after_source=True,
        )

        assert hyper.hyper_tag == "__hyper_galaxies_bg_sky_bg_noise_fixed"

        hyper = al.slam.Hyper(hyper_galaxies=True, hyper_background_noise=True)

        assert hyper.hyper_tag == "__hyper_galaxies_bg_noise"

        hyper = al.slam.Hyper(
            hyper_fixed_after_source=True,
            hyper_galaxies=True,
            hyper_background_noise=True,
        )

        assert hyper.hyper_tag == "__hyper_galaxies_bg_noise_fixed"


class TestSource:
    def test__lens_light_bulge_only_tag(self):
        source = al.slam.Source(lens_light_bulge_only=False)
        assert source.lens_light_bulge_only_tag == ""
        source = al.slam.Source(lens_light_bulge_only=True)
        assert source.lens_light_bulge_only_tag == "__bulge_only"

    def test__tag(self):

        source = al.slam.Source(
            pixelization=al.pix.Rectangular,
            regularization=al.reg.Constant,
            lens_light_centre=(1.0, 2.0),
            lens_mass_centre=(3.0, 4.0),
            align_light_mass_centre=False,
            no_shear=True,
        )

        source.type_tag = source.inversion_tag

        assert (
            source.tag
            == "source____pix_rect__reg_const__no_shear__lens_light_centre_(1.00,2.00)__lens_mass_centre_(3.00,4.00)"
        )

        source = al.slam.Source(
            pixelization=al.pix.Rectangular,
            regularization=al.reg.Constant,
            align_light_mass_centre=True,
            number_of_gaussians=1,
            lens_light_bulge_only=True,
        )

        source.type_tag = "test"

        assert (
            source.tag
            == "source__test__gaussians_x1__with_shear__align_light_mass_centre__bulge_only"
        )


class TestLight:
    def test__tag(self):

        light = al.slam.Light(align_bulge_disk_phi=True)
        light.type_tag = ""

        assert light.tag == "light____align_bulge_disk_phi"

        light = al.slam.Light(
            align_bulge_disk_centre=True,
            align_bulge_disk_axis_ratio=True,
            disk_as_sersic=True,
        )

        light.type_tag = "lol"

        assert (
            light.tag == "light__lol__align_bulge_disk_centre_axis_ratio__disk_sersic"
        )

        light = al.slam.Light(
            align_bulge_disk_centre=True,
            align_bulge_disk_axis_ratio=True,
            disk_as_sersic=True,
            number_of_gaussians=2,
        )
        light.type_tag = "test"

        assert light.tag == "light__test__gaussians_x2"


class TestMass:
    def test__fix_lens_light_tag(self):
        mass = al.slam.Mass(fix_lens_light=False)
        assert mass.fix_lens_light_tag == ""
        mass = al.slam.Mass(fix_lens_light=True)
        assert mass.fix_lens_light_tag == "__fix_lens_light"

    def test__tag(self):

        mass = al.slam.Mass(
            no_shear=True, align_light_dark_centre=True, fix_lens_light=True
        )
        mass.type_tag = ""

        assert mass.tag == "mass____no_shear__align_light_dark_centre__fix_lens_light"

        mass = al.slam.Mass(align_bulge_dark_centre=True)

        mass.type_tag = "test"

        assert mass.tag == "mass__test__with_shear__align_bulge_dark_centre"