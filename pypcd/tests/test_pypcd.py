"""
this is just a basic sanity check, not a really legit test suite.

TODO maybe download data here instead of having it in repo
"""

import pytest
import numpy as np
import os
import shutil
import tempfile

header1 = """\
# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z i
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH 500028
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS 500028
DATA binary_compressed
"""

header2 = """\
VERSION .7
FIELDS x y z normal_x normal_y normal_z curvature boundary k vp_x vp_y vp_z principal_curvature_x principal_curvature_y principal_curvature_z pc1 pc2
SIZE 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4 4
TYPE F F F F F F F F F F F F F F F F F
COUNT 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
WIDTH 19812
HEIGHT 1
VIEWPOINT 0.0 0.0 0.0 1.0 0.0 0.0 0.0
POINTS 19812
DATA ascii
"""


@pytest.fixture
def pcd_fname():
    import pypcd
    return os.path.join(pypcd.__path__[0], 'test_data',
                        'partial_cup_model.pcd')


@pytest.fixture
def ascii_pcd_fname():
    import pypcd
    return os.path.join(pypcd.__path__[0], 'test_data',
                        'ascii.pcd')


@pytest.fixture
def bin_pcd_fname():
    import pypcd
    return os.path.join(pypcd.__path__[0], 'test_data',
                        'bin.pcd')


def cloud_centroid(pc):
    xyz = np.empty((pc.points, 3), dtype=np.float)
    xyz[:, 0] = pc.pc_data['x']
    xyz[:, 1] = pc.pc_data['y']
    xyz[:, 2] = pc.pc_data['z']
    return xyz.mean(0)


def test_parse_header():
    from pypcd.pypcd import parse_header
    lines = header1.split('\n')
    md = parse_header(lines)
    assert (md['version'] == '0.7')
    assert (md['fields'] == ['x', 'y', 'z', 'i'])
    assert (md['size'] == [4, 4, 4, 4])
    assert (md['type'] == ['F', 'F', 'F', 'F'])
    assert (md['count'] == [1, 1, 1, 1])
    assert (md['width'] == 500028)
    assert (md['height'] == 1)
    assert (md['viewpoint'] == [0, 0, 0, 1, 0, 0, 0])
    assert (md['points'] == 500028)
    assert (md['data'] == 'binary_compressed')


def test_from_path(pcd_fname):
    import pypcd
    pc = pypcd.PointCloud.from_path(pcd_fname)

    fields = 'x y z normal_x normal_y normal_z curvature boundary k vp_x vp_y vp_z principal_curvature_x principal_curvature_y principal_curvature_z pc1 pc2'.split()
    for fld1, fld2 in zip(pc.fields, fields):
        assert(fld1 == fld2)
    assert (pc.width == 19812)
    assert (len(pc.pc_data) == 19812)


def test_add_fields(pcd_fname):
    import pypcd
    pc = pypcd.PointCloud.from_path(pcd_fname)

    old_md = pc.get_metadata()
    # new_dt = [(f, pc.pc_data.dtype[f]) for f in pc.pc_data.dtype.fields]
    # new_data = [pc.pc_data[n] for n in pc.pc_data.dtype.names]
    md = {'fields': ['bla', 'bar'], 'count': [1, 1], 'size': [4, 4],
          'type': ['F', 'F']}
    d = np.rec.fromarrays((np.random.random(len(pc.pc_data)),
                           np.random.random(len(pc.pc_data))))
    newpc = pypcd.add_fields(pc, md, d)

    new_md = newpc.get_metadata()
    # print len(old_md['fields']), len(md['fields']), len(new_md['fields'])
    # print old_md['fields'], md['fields'], new_md['fields']
    assert(len(old_md['fields'])+len(md['fields']) == len(new_md['fields']))


def test_path_roundtrip_ascii(pcd_fname):
    import pypcd
    pc = pypcd.PointCloud.from_path(pcd_fname)
    md = pc.get_metadata()

    tmp_dirname = tempfile.mkdtemp(suffix='_pypcd', prefix='tmp')

    tmp_fname = os.path.join(tmp_dirname, 'out.pcd')

    pc.save_pcd(tmp_fname, compression='ascii')

    assert(os.path.exists(tmp_fname))

    pc2 = pypcd.PointCloud.from_path(tmp_fname)
    md2 = pc2.get_metadata()
    assert(md == md2)

    np.testing.assert_equal(pc.pc_data, pc2.pc_data)

    if os.path.exists(tmp_fname):
        os.unlink(tmp_fname)
    os.removedirs(tmp_dirname)


def test_path_roundtrip_binary(pcd_fname):
    import pypcd
    pc = pypcd.PointCloud.from_path(pcd_fname)
    md = pc.get_metadata()

    tmp_dirname = tempfile.mkdtemp(suffix='_pypcd', prefix='tmp')

    tmp_fname = os.path.join(tmp_dirname, 'out.pcd')

    pc.save_pcd(tmp_fname, compression='binary')

    assert(os.path.exists(tmp_fname))

    pc2 = pypcd.PointCloud.from_path(tmp_fname)
    md2 = pc2.get_metadata()
    for k, v in md2.iteritems():
        if k == 'data':
            assert v == 'binary'
        else:
            assert v == md[k]

    np.testing.assert_equal(pc.pc_data, pc2.pc_data)

    if os.path.exists(tmp_fname):
        os.unlink(tmp_fname)
    os.removedirs(tmp_dirname)


def test_path_roundtrip_binary_compressed(pcd_fname):
    import pypcd
    pc = pypcd.PointCloud.from_path(pcd_fname)
    md = pc.get_metadata()

    tmp_dirname = tempfile.mkdtemp(suffix='_pypcd', prefix='tmp')

    tmp_fname = os.path.join(tmp_dirname, 'out.pcd')

    pc.save_pcd(tmp_fname, compression='binary_compressed')

    assert(os.path.exists(tmp_fname))

    pc2 = pypcd.PointCloud.from_path(tmp_fname)
    md2 = pc2.get_metadata()
    for k, v in md2.iteritems():
        if k == 'data':
            assert v == 'binary_compressed'
        else:
            assert v == md[k]

    np.testing.assert_equal(pc.pc_data, pc2.pc_data)

    if os.path.exists(tmp_dirname):
        shutil.rmtree(tmp_dirname)


def test_cat_pointclouds(pcd_fname):
    import pypcd
    pc = pypcd.PointCloud.from_path(pcd_fname)
    pc2 = pc.copy()
    pc2.pc_data['x'] += 0.1
    pc3 = pypcd.cat_point_clouds(pc, pc2)
    for fld, fld3 in zip(pc.fields, pc3.fields):
        assert(fld == fld3)
    assert(pc3.width == pc.width+pc2.width)


def test_ascii_bin1(ascii_pcd_fname, bin_pcd_fname):
    import pypcd
    apc1 = pypcd.point_cloud_from_path(ascii_pcd_fname)
    bpc1 = pypcd.point_cloud_from_path(bin_pcd_fname)
    am = cloud_centroid(apc1)
    bm = cloud_centroid(bpc1)
    assert(np.allclose(am, bm))
