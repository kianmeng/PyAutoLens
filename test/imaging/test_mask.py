import numpy as np
from autolens.imaging import array_util
from autolens.imaging import scaled_array
from autolens.imaging import mask
import pytest


class TestMask(object):

    def test__constructor(self):

        msk = np.array([[True, True, True, True],
                        [True, False, False, True],
                        [True, True, True, True]])

        msk = mask.Mask(msk, pixel_scale=1)

        assert (msk == np.array([[True, True, True, True],
                                 [True, False, False, True],
                                 [True, True, True, True]])).all()
        assert msk.pixel_scale == 1.0
        assert msk.central_pixel_coordinates == (1.0, 1.5)
        assert msk.shape == (3, 4)
        assert msk.shape_arc_seconds == (3.0, 4.0)

    def test__mask_circular__compare_to_array_util(self):

        msk_util = array_util.mask_circular_from_shape_pixel_scale_and_radius(shape=(5, 4), pixel_scale=2.7,
                                                                              radius_arcsec=3.5, centre=(1.0, 1.0))

        msk = mask.Mask.circular(shape=(5, 4), pixel_scale=2.7, radius_mask_arcsec=3.5, centre=(1.0, 1.0))

        assert (msk == msk_util).all()

    def test__mask_annulus__compare_to_array_util(self):

        msk_util = array_util.mask_annular_from_shape_pixel_scale_and_radii(shape=(5, 4), pixel_scale=2.7,
                                                                            inner_radius_arcsec=0.8,
                                                                            outer_radius_arcsec=3.5,
                                                                            centre=(1.0, 1.0))

        msk = mask.Mask.annular(shape=(5, 4), pixel_scale=2.7, inner_radius_arcsec=0.8, outer_radius_arcsec=3.5,
                                 centre=(1.0, 1.0))

        assert (msk == msk_util).all()

    def test__mask_unmasked__5x5__input__all_are_false(self):

        msk = mask.Mask.unmasked(shape_arc_seconds=(5, 5), pixel_scale=1)

        assert msk.shape == (5, 5)
        assert (msk == np.array([[False, False, False, False, False],
                                 [False, False, False, False, False],
                                 [False, False, False, False, False],
                                 [False, False, False, False, False],
                                 [False, False, False, False, False]])).all()

    def test__grid_to_pixel__compare_to_array_utill(self):

        msk = np.array([[True, True, True],
                        [True, False, False],
                        [True, True, False]])

        msk = mask.Mask(msk, pixel_scale=7.0)

        grid_to_pixel_util = array_util.grid_to_pixel_from_mask(msk)

        assert msk.grid_to_pixel == pytest.approx(grid_to_pixel_util, 1e-4)

    def test__map_2d_array_to_masked_1d_array__compare_to_array_util(self):

        array_2d = np.array([[1, 2, 3],
                             [4, 5, 6],
                             [7, 8, 9],
                             [10, 11, 12]])

        msk = np.array([[True, False, True],
                        [False, False, False],
                        [True, False, True],
                        [True, True, True]])

        array_1d_util = array_util.map_2d_array_to_masked_1d_array_from_array_2d_and_mask(msk, array_2d)

        msk = mask.Mask(msk, pixel_scale=3.0)

        array_1d = msk.map_2d_array_to_masked_1d_array(array_2d)

        assert (array_1d == array_1d_util).all()

    def test__map_masked_1d_array_to_2d_array__compare_to_array_util(self):

        array_1d = np.array([1.0, 6.0, 4.0, 5.0, 2.0])

        msk = np.array([[True, False, True],
                        [False, False, False],
                        [True, False, True],
                        [True, True, True]])

        one_to_two = np.array([[0,1], [1,0], [1,1], [1,2], [2,1]])

        array_2d_util = array_util.map_masked_1d_array_to_2d_array_from_array_1d_shape_and_one_to_two(array_1d=array_1d,
                                                                        shape=(4,3), one_to_two=one_to_two)

        msk = mask.Mask(msk, pixel_scale=3.0)

        array_2d = msk.map_masked_1d_array_to_2d_array(array_1d)

        assert (array_2d == array_2d_util).all()

    def test__masked_image_grid_from_mask__compare_to_array_util(self):

        msk = np.array([[True, True, False, False],
                        [True, False, True, True],
                        [True, True, False, False]])

        image_grid_util = array_util.image_grid_masked_from_mask_and_pixel_scale(mask=msk, pixel_scale=2.0)

        msk = mask.Mask(msk, pixel_scale=2.0)

        assert msk.masked_image_grid == pytest.approx(image_grid_util, 1e-4)

    def test__blurring_mask_for_psf_shape__compare_to_array_util(self):

        msk = np.array([[True, True, True, True, True, True, True, True],
                         [True, False, True, True, True, False, True, True],
                         [True, True, True, True, True, True, True, True],
                         [True, True, True, True, True, True, True, True],
                         [True, True, True, True, True, True, True, True],
                         [True, False, True, True, True, False, True, True],
                         [True, True, True, True, True, True, True, True],
                         [True, True, True, True, True, True, True, True],
                         [True, True, True, True, True, True, True, True]])

        blurring_mask_util = array_util.mask_blurring_from_mask_and_psf_shape(mask=msk, psf_shape=(3,3))

        msk = mask.Mask(msk, pixel_scale=1.0)
        blurring_mask = msk.blurring_mask_for_psf_shape(psf_shape=(3, 3))

        assert (blurring_mask == blurring_mask_util).all()

    def test__border_image_pixels__compare_to_array_util(self):

        msk = np.array([[True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True],
                        [True, True, True, False, True, True, True],
                        [True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True]])

        border_pixels_util = array_util.border_pixels_from_mask(msk)

        msk = mask.Mask(msk, pixel_scale=3.0)

        border_pixels = msk.border_pixel_indices

        assert border_pixels == pytest.approx(border_pixels_util, 1e-4)

    def test__border_sub_pixels__compare_to_array_util(self):

        msk = np.array([[True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True],
                        [True, True, False, False, False, True, True],
                        [True, True, False, False, False, True, True],
                        [True, True, False, False, False, True, True],
                        [True, True, True, True, False, False, True],
                        [True, True, True, True, True, False, True]])

        border_sub_pixels_util = array_util.border_sub_pixels_from_mask_pixel_scale_and_sub_grid_size(mask=msk,
                                                                                                 pixel_scale=3.0,
                                                                                                 sub_grid_size=2)

        msk = mask.Mask(msk, pixel_scale=3.0)

        border_sub_pixels = msk.border_sub_pixel_indices(sub_grid_size=2)

        assert border_sub_pixels == pytest.approx(border_sub_pixels_util, 1e-4)


@pytest.fixture(name="msk")
def make_mask():
    return mask.Mask(np.array([[True, False, True],
                               [False, False, False],
                               [True, False, True]]))


@pytest.fixture(name="centre_mask")
def make_centre_mask():
    return mask.Mask(np.array([[True, True, True],
                               [True, False, True],
                               [True, True, True]]))


@pytest.fixture(name="sub_grid")
def make_sub_grid(msk):
    return mask.SubGrid.from_mask_and_sub_grid_size(msk, sub_grid_size=1)

@pytest.fixture(name="grids")
def make_grids(centre_mask):
    return mask.GridCollection.from_mask_sub_grid_size_and_blurring_shape(centre_mask, 2, (3, 3))


class TestImageGrid:

    def test__compute_xticks_property__include_round_to_2dp(self):

        grid = mask.ImageGrid(arr=np.array([[0.0, 0.0], [0.0, 0.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.xticks == pytest.approx(np.array([-0.3, -0.1, 0.1, 0.3]), 1e-3)

        grid = mask.ImageGrid(arr=np.array([[-6.0, -10.5], [6.0, 0.5], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.xticks == pytest.approx(np.array([-6.0, -2.0, 2.0, 6.0]), 1e-3)

        grid = mask.ImageGrid(arr=np.array([[-1.0, -0.5], [1.0, 0.5], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.xticks == pytest.approx(np.array([-1.0, -0.33, 0.33, 1.0]), 1e-3)

    def test__compute_yticks_property__include_round_to_2dp(self):

        grid = mask.ImageGrid(arr=np.array([[0.0, 0.0], [0.0, 0.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.yticks == pytest.approx(np.array([-0.3, -0.1, 0.1, 0.3]), 1e-3)

        grid = mask.ImageGrid(arr=np.array([[-10.5, -6.0], [0.5, 6.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.yticks == pytest.approx(np.array([-6.0, -2.0, 2.0, 6.0]), 1e-3)

        grid = mask.ImageGrid(arr=np.array([[-0.5, -1.0], [0.5, 1.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.yticks == pytest.approx(np.array([-1.0, -0.33, 0.33, 1.0]), 1e-3)

    def test__blurring_grid_from_mask__compare_to_array_util(self):

        msk = np.array([[True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, False, True, True, True, False, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, False, True, True, True, False, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True]])

        blurring_mask_util = array_util.mask_blurring_from_mask_and_psf_shape(msk, psf_shape=(3,5))
        blurring_grid_util = array_util.image_grid_masked_from_mask_and_pixel_scale(blurring_mask_util, pixel_scale=2.0)

        msk = mask.Mask(msk, pixel_scale=2.0)
        blurring_grid = mask.ImageGrid.blurring_grid_from_mask_and_psf_shape(mask=msk, psf_shape=(3,5))

        assert blurring_grid == pytest.approx(blurring_grid_util, 1e-4)


class TestSubGrid(object):

    def test_sub_grid(self, sub_grid):
        assert sub_grid.shape == (5, 2)
        assert (sub_grid == np.array([[-1, 0], [0, -1], [0, 0], [0, 1], [1, 0]])).all()

    def test_sub_to_pixel(self, sub_grid):
        assert (sub_grid.sub_to_image == np.array(range(5))).all()

    def test__from_mask(self):

        msk = np.array([[True, True, True],
                        [True, False, False],
                        [True, True, False]])

        sub_grid_util = array_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask=msk, pixel_scale=3.0,
                                                                                           sub_grid_size=2)

        msk = mask.Mask(msk, pixel_scale=3.0)

        sub_grid = mask.SubGrid.from_mask_and_sub_grid_size(msk, sub_grid_size=2)

        assert sub_grid == pytest.approx(sub_grid_util, 1e-4)

    def test_sub_data_to_image(self, sub_grid):
        assert (sub_grid.sub_data_to_image(np.array(range(5))) == np.array(range(5))).all()

    def test_sub_to_image__compare_to_array_util(self):

        msk = np.array([[True, False, True],
                        [False, False, False],
                        [True, False, False]])

        sub_to_image_util = array_util.sub_to_image_from_mask(msk, sub_grid_size=2)

        msk = mask.Mask(msk, pixel_scale=3.0)

        sub_grid = mask.SubGrid.from_mask_and_sub_grid_size(mask=msk, sub_grid_size=2)
        assert sub_grid.sub_grid_size == 2
        assert sub_grid.sub_grid_fraction == (1.0 / 4.0)
        assert (sub_grid.sub_to_image == sub_to_image_util).all()


class TestGridsMappers:

    def test__map_unmasked_1d_array_to_2d_array__compare_to_array_utils(self):

        grid_1d = np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                            [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                            [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                            [1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0]])

        image_mapper = mask.ImageGridMapper(arr=grid_1d, original_shape=(2 , 2), padded_shape=(4 , 4))

        array_1d = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
        array_2d_util = array_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(array_1d, shape=(4, 4))
        array_2d = image_mapper.map_unmasked_1d_array_to_2d_array(array_1d)

        assert (array_2d == array_2d_util).all()

    def test__same_as_above_for_sub_grid_mapper(self):

        msk = np.array([[False, False],
                        [False, False]])

        msk = mask.Mask(msk, pixel_scale=3.0)

        grid_1d = np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0]])

        grid = mask.SubGridMapper(arr=grid_1d, mask=msk, original_shape=(1 , 1), padded_shape=(2 , 2), sub_grid_size=2)

        array_1d = np.array([1.0, 2.0, 3.0, 4.0])
        array_2d_util = array_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(array_1d, shape=(2, 2))
        array_2d = grid.map_unmasked_1d_array_to_2d_array(array_1d)

        assert (array_2d == array_2d_util).all()

    def test__image_grid_mapper_from_scaled_array(self):

        sca = scaled_array.ScaledArray(np.array([[0.0, 0.0, 0.0],
                                                 [0.0, 0.0, 0.0],
                                                 [0.0, 0.0, 0.0]]), pixel_scale=1.0)
        
        image_mapper = mask.ImageGridMapper.from_scaled_array_and_psf_shape(scaled_array=sca, psf_shape=(3,3))

        image_mapper_util = array_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((5,5), False),
                                                                                   pixel_scale=1.0)

        assert (image_mapper == image_mapper_util).all()
        assert image_mapper.original_shape == (3,3)
        assert image_mapper.padded_shape == (5,5)

    def test__sub_grid_mapper_from_mask(self):

        msk = np.array([[False, False, False],
                        [False, False, False],
                        [False, False, False]])

        msk = mask.Mask(msk, pixel_scale=1.0)

        sub_mapper = mask.SubGridMapper.from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=2,
                                                                              psf_shape=(3, 3))

        sub_mapper_util = array_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask=np.full((5, 5), False),
                                                                         pixel_scale=1.0, sub_grid_size=2)

        assert (sub_mapper == sub_mapper_util).all()
        assert sub_mapper.original_shape == (3, 3)
        assert sub_mapper.padded_shape == (5, 5)


class TestGridCollection(object):

    def test_grids(self, grids):

        assert (grids.image == np.array([[0., 0.]])).all()
        np.testing.assert_almost_equal(grids.sub, np.array([[-0.16666667, -0.16666667],
                                                            [-0.16666667, 0.16666667],
                                                            [0.16666667, -0.16666667],
                                                            [0.16666667, 0.16666667]]))
        assert (grids.blurring == np.array([[-1., -1.],
                                            [-1., 0.],
                                            [-1., 1.],
                                            [0., -1.],
                                            [0., 1.],
                                            [1., -1.],
                                            [1., 0.],
                                            [1., 1.]])).all()

    def test_mapper_grids(self):

        msk = np.array([[False, False],
                        [False, False]])

        msk = mask.Mask(msk, pixel_scale=1.0)

        grid_mappers = mask.GridCollection.grid_mappers_from_mask_sub_grid_size_and_psf_shape(msk, sub_grid_size=2,
                                                                                              psf_shape=(3,3))

        image_mapper_util = array_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((4,4), False),
                                                                                   pixel_scale=1.0)

        sub_mapper_util = array_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask=np.full((4, 4), False),
                                                                         pixel_scale=1.0, sub_grid_size=2)

        assert (grid_mappers.image == image_mapper_util).all()
        assert grid_mappers.image.original_shape == (2 ,2)
        assert grid_mappers.image.padded_shape == (4 ,4)

        assert (grid_mappers.sub == sub_mapper_util).all()
        assert grid_mappers.sub.original_shape == (2 ,2)
        assert grid_mappers.sub.padded_shape == (4 ,4)

        assert grid_mappers.blurring == None

    def test_apply_function(self, grids):
        def add_one(coords):
            return np.add(1, coords)

        new_collection = grids.apply_function(add_one)
        assert isinstance(new_collection, mask.GridCollection)
        assert (new_collection.image == np.add(1, np.array([[0., 0.]]))).all()
        np.testing.assert_almost_equal(new_collection.sub, np.add(1, np.array([[-0.16666667, -0.16666667],
                                                                               [-0.16666667, 0.16666667],
                                                                               [0.16666667, -0.16666667],
                                                                               [0.16666667, 0.16666667]])))
        assert (new_collection.blurring == np.add(1, np.array([[-1., -1.],
                                                               [-1., 0.],
                                                               [-1., 1.],
                                                               [0., -1.],
                                                               [0., 1.],
                                                               [1., -1.],
                                                               [1., 0.],
                                                               [1., 1.]]))).all()

    def test_map_function(self, grids):
        def add_number(coords, number):
            return np.add(coords, number)

        new_collection = grids.map_function(add_number, [1, 2, 3])

        assert isinstance(new_collection, mask.GridCollection)
        assert (new_collection.image == np.add(1, np.array([[0., 0.]]))).all()
        np.testing.assert_almost_equal(new_collection.sub, np.add(2, np.array([[-0.16666667, -0.16666667],
                                                                               [-0.16666667, 0.16666667],
                                                                               [0.16666667, -0.16666667],
                                                                               [0.16666667, 0.16666667]])))
        assert (new_collection.blurring == np.add(3, np.array([[-1., -1.],
                                                               [-1., 0.],
                                                               [-1., 1.],
                                                               [0., -1.],
                                                               [0., 1.],
                                                               [1., -1.],
                                                               [1., 0.],
                                                               [1., 1.]]))).all()


class TestBorderCollection(object):

    class TestSetup:

        def test__simple_setup_using_constructor(self):

            image_border = mask.ImageGridBorder(arr=np.array([1, 2, 5]), polynomial_degree=4, centre=(1.0, 1.0))
            sub_border = mask.SubGridBorder(arr=np.array([1, 2, 3]), polynomial_degree=2, centre=(0.0, 1.0))

            border_collection = mask.BorderCollection(image=image_border, sub=sub_border)

            assert (border_collection.image == np.array([1, 2, 5])).all()
            assert border_collection.image.polynomial_degree == 4
            assert border_collection.image.centre == (1.0, 1.0)

            assert (border_collection.sub == np.array([1, 2, 3])).all()
            assert border_collection.sub.polynomial_degree == 2
            assert border_collection.sub.centre == (0.0, 1.0)

        def test__setup_from_mask(self):

            msk = np.array([[True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, False, False, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True]])

            msk = mask.Mask(msk, pixel_scale=3.0)

            border_collection = mask.BorderCollection.from_mask_and_sub_grid_size(mask=msk, sub_grid_size=2)

            assert (border_collection.image == np.array([0, 1])).all()
            assert (border_collection.sub == np.array([0, 5])).all()

    class TestRelocatedGridsFromGrids:

        def test__simple_case__new_grids_have_relocates(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            image_grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            image_grid = image_grid_circle
            image_grid.append(np.array([0.1, 0.0]))
            image_grid.append(np.array([-0.2, -0.3]))
            image_grid.append(np.array([0.5, 0.4]))
            image_grid.append(np.array([0.7, -0.1]))
            image_grid = np.asarray(image_grid)

            image_border = mask.ImageGridBorder(arr=np.arange(32), polynomial_degree=3)

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            sub_grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            sub_grid = sub_grid_circle
            sub_grid.append(np.array([2.5, 0.0]))
            sub_grid.append(np.array([0.0, 3.0]))
            sub_grid.append(np.array([-2.5, 0.0]))
            sub_grid.append(np.array([-5.0, 5.0]))
            sub_grid = np.asarray(sub_grid)

            sub_border = mask.SubGridBorder(arr=np.arange(32), polynomial_degree=3)

            borders = mask.BorderCollection(image=image_border, sub=sub_border)

            grids = mask.GridCollection(image=image_grid, sub=sub_grid, blurring=None)

            relocated_grids = borders.relocated_grids_from_grids(grids)

            assert relocated_grids.image[0:32] == pytest.approx(np.asarray(image_grid_circle)[0:32], 1e-3)
            assert relocated_grids.image[32] == pytest.approx(np.array([0.1, 0.0]), 1e-3)
            assert relocated_grids.image[33] == pytest.approx(np.array([-0.2, -0.3]), 1e-3)
            assert relocated_grids.image[34] == pytest.approx(np.array([0.5, 0.4]), 1e-3)
            assert relocated_grids.image[35] == pytest.approx(np.array([0.7, -0.1]), 1e-3)

            assert relocated_grids.sub[0:32] == pytest.approx(np.asarray(sub_grid_circle)[0:32], 1e-3)
            assert relocated_grids.sub[32] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert relocated_grids.sub[33] == pytest.approx(np.array([0.0, 1.0]), 1e-3)
            assert relocated_grids.sub[34] == pytest.approx(np.array([-1.0, 0.0]), 1e-3)
            assert relocated_grids.sub[35] == pytest.approx(np.array([-0.707, 0.707]), 1e-3)


class TestIGridBorder(object):

    class TestFromMask:

        def test__simple_mask_border_pixel_is_pixel(self):

            msk = np.array([[True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, False, False, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True]])

            msk = mask.Mask(msk, pixel_scale=3.0)

            border = mask.ImageGridBorder.from_mask(msk)

            assert (border == np.array([0, 1])).all()

    class TestThetasAndRadii:

        def test__four_grid_in_circle__all_in_border__correct_radii_and_thetas(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = mask.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            radii = border.grid_to_radii(grid)
            thetas = border.grid_to_thetas(grid)

            assert (radii == np.array([1.0, 1.0, 1.0, 1.0])).all()
            assert (thetas == np.array([0.0, 90.0, 180.0, 270.0])).all()

        def test__other_thetas_radii(self):
            grid = np.array([[2.0, 0.0], [2.0, 2.0], [-1.0, -1.0], [0.0, -3.0]])

            border = mask.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            radii = border.grid_to_radii(grid)
            thetas = border.grid_to_thetas(grid)

            assert (radii == np.array([2.0, 2.0 * np.sqrt(2), np.sqrt(2.0), 3.0])).all()
            assert (thetas == np.array([0.0, 45.0, 225.0, 270.0])).all()

        def test__border_centre_offset__grid_same_r_and_theta_shifted(self):

            grid = np.array([[2.0, 1.0], [1.0, 2.0], [0.0, 1.0], [1.0, 0.0]])

            border = mask.ImageGridBorder(arr=np.arange(4), polynomial_degree=3, centre=(1.0, 1.0))
            radii = border.grid_to_radii(grid)
            thetas = border.grid_to_thetas(grid)

            assert (radii == np.array([1.0, 1.0, 1.0, 1.0])).all()
            assert (thetas == np.array([0.0, 90.0, 180.0, 270.0])).all()

    class TestBorderPolynomialFit(object):

        def test__four_grid_in_circle__thetas_at_radius_are_each_grid_radius(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = mask.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            poly = border.polynomial_fit_to_border(grid)

            assert np.polyval(poly, 0.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 90.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 180.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 270.0) == pytest.approx(1.0, 1e-3)

        def test__eight_grid_in_circle__thetas_at_each_grid_are_the_radius(self):

            grid = np.array([[1.0, 0.0], [0.5 * np.sqrt(2), 0.5 * np.sqrt(2)],
                             [0.0, 1.0], [-0.5 * np.sqrt(2), 0.5 * np.sqrt(2)],
                             [-1.0, 0.0], [-0.5 * np.sqrt(2), -0.5 * np.sqrt(2)],
                             [0.0, -1.0], [0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]])

            border = mask.ImageGridBorder(arr=
                                          np.arange(8), polynomial_degree=3)
            poly = border.polynomial_fit_to_border(grid)

            assert np.polyval(poly, 0.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 45.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 90.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 135.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 180.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 225.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 270.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 315.0) == pytest.approx(1.0, 1e-3)

    class TestMoveFactors(object):

        def test__inside_border__move_factor_is_1(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = mask.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            move_factors = border.move_factors_from_grid(grid)

            assert move_factors[0] == pytest.approx(1.0, 1e-4)
            assert move_factors[1] == pytest.approx(1.0, 1e-4)
            assert move_factors[2] == pytest.approx(1.0, 1e-4)
            assert move_factors[3] == pytest.approx(1.0, 1e-4)

        def test__outside_border_double_its_radius__move_factor_is_05(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0],
                             [2.0, 0.0], [0.0, 2.0], [-2.0, 0.0], [0.0, -2.0]])

            border = mask.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            move_factors = border.move_factors_from_grid(grid)

            assert move_factors[0] == pytest.approx(1.0, 1e-4)
            assert move_factors[1] == pytest.approx(1.0, 1e-4)
            assert move_factors[2] == pytest.approx(1.0, 1e-4)
            assert move_factors[3] == pytest.approx(1.0, 1e-4)
            assert move_factors[4] == pytest.approx(0.5, 1e-4)
            assert move_factors[5] == pytest.approx(0.5, 1e-4)
            assert move_factors[6] == pytest.approx(0.5, 1e-4)
            assert move_factors[7] == pytest.approx(0.5, 1e-4)

        def test__outside_border_as_above__but_shift_for_source_plane_centre(self):

            grid = np.array([[2.0, 1.0], [1.0, 2.0], [0.0, 1.0], [1.0, 0.0],
                             [3.0, 1.0], [1.0, 3.0], [1.0, 3.0], [3.0, 1.0]])

            border = mask.ImageGridBorder(arr=np.arange(4), polynomial_degree=3, centre=(1.0, 1.0))
            move_factors = border.move_factors_from_grid(grid)

            assert move_factors[0] == pytest.approx(1.0, 1e-4)
            assert move_factors[1] == pytest.approx(1.0, 1e-4)
            assert move_factors[2] == pytest.approx(1.0, 1e-4)
            assert move_factors[3] == pytest.approx(1.0, 1e-4)
            assert move_factors[4] == pytest.approx(0.5, 1e-4)
            assert move_factors[5] == pytest.approx(0.5, 1e-4)
            assert move_factors[6] == pytest.approx(0.5, 1e-4)
            assert move_factors[7] == pytest.approx(0.5, 1e-4)

    class TestRelocateCoordinates(object):

        def test__inside_border_no_relocations(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            grid = grid_circle
            grid.append(np.array([0.1, 0.0]))
            grid.append(np.array([-0.2, -0.3]))
            grid.append(np.array([0.5, 0.4]))
            grid.append(np.array([0.7, -0.1]))
            grid = np.asarray(grid)

            border = mask.ImageGridBorder(arr=np.arange(32), polynomial_degree=3)
            relocated_grid = border.relocated_grid_from_grid(grid)

            assert relocated_grid[0:32] == pytest.approx(np.asarray(grid_circle)[0:32], 1e-3)
            assert relocated_grid[32] == pytest.approx(np.array([0.1, 0.0]), 1e-3)
            assert relocated_grid[33] == pytest.approx(np.array([-0.2, -0.3]), 1e-3)
            assert relocated_grid[34] == pytest.approx(np.array([0.5, 0.4]), 1e-3)
            assert relocated_grid[35] == pytest.approx(np.array([0.7, -0.1]), 1e-3)

        def test__outside_border_simple_cases__relocates_to_source_border(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            grid = grid_circle
            grid.append(np.array([2.5, 0.0]))
            grid.append(np.array([0.0, 3.0]))
            grid.append(np.array([-2.5, 0.0]))
            grid.append(np.array([-5.0, 5.0]))
            grid = np.asarray(grid)

            border = mask.ImageGridBorder(arr=np.arange(32), polynomial_degree=3)
            relocated_grid = border.relocated_grid_from_grid(grid)

            assert relocated_grid[0:32] == pytest.approx(np.asarray(grid_circle)[0:32], 1e-3)
            assert relocated_grid[32] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert relocated_grid[33] == pytest.approx(np.array([0.0, 1.0]), 1e-3)
            assert relocated_grid[34] == pytest.approx(np.array([-1.0, 0.0]), 1e-3)
            assert relocated_grid[35] == pytest.approx(np.array([-0.707, 0.707]), 1e-3)

        def test__6_grid_total__2_outside_border__different_border__relocate_to_source_border(self):

            grid = np.array([[1.0, 0.0], [20., 20.], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [1.0, 1.0]])
            border_pixels = np.array([0, 2, 3, 4])

            border = mask.ImageGridBorder(border_pixels, polynomial_degree=3)

            relocated_grid = border.relocated_grid_from_grid(grid)

            assert relocated_grid[0] == pytest.approx(grid[0], 1e-3)
            assert relocated_grid[1] == pytest.approx(np.array([0.7071, 0.7071]), 1e-3)
            assert relocated_grid[2] == pytest.approx(grid[2], 1e-3)
            assert relocated_grid[3] == pytest.approx(grid[3], 1e-3)
            assert relocated_grid[4] == pytest.approx(grid[4], 1e-3)
            assert relocated_grid[5] == pytest.approx(np.array([0.7071, 0.7071]), 1e-3)

    class TestSubGridBorder(object):

        def test__simple_mask_border_pixel_is_pixel(self):

            msk = np.array([[True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, False, False, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True]])

            msk = mask.Mask(msk, pixel_scale=3.0)

            border = mask.SubGridBorder.from_mask(msk, sub_grid_size=2)

            assert (border == np.array([0, 5])).all()
