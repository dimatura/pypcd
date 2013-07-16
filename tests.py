"""
this is just a basic sanity check, not a really legit test suite.
"""

import nose
import numpy as np
import pypcd

header1 ="""\
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

header2 ="""\
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

def test1():
    lines = header1.split('\n')
    md = pypcd._parse_header(lines)
    assert (md['version']=='0.7')
    assert (md['fields']==['x', 'y', 'z', 'i'])
    assert (md['size']==[4,4,4,4])
    assert (md['type']==['F','F','F','F'])
    assert (md['count']==[1,1,1,1])
    assert (md['width']==500028)
    assert (md['height']==1)
    assert (md['viewpoint']==[0, 0, 0, 1, 0, 0, 0])
    assert (md['points']==500028)
    assert (md['data']=='binary_compressed')

def test2():
    pc = pypcd.load_point_cloud('test_data/partial_cup_model.pcd')
    old_md = pc.get_metadata()
    print old_md['fields']
    new_dt = [(f, pc.data.dtype[f]) for f in pc.data.dtype.fields]
    new_data = [pc.data[n] for n in pc.data.dtype.names]
    md = {'fields' : ['bla', 'bar'], 'count' : [1, 1], 'size' : [4, 4], 'type' : ['F', 'F']}
    d = np.rec.fromarrays( (np.random.random(len(pc.data)), np.random.random(len(pc.data))) )
    newpc = pypcd.add_fields(pc, md, d)

    new_md = newpc.get_metadata()
    print len(old_md['fields']), len(md['fields']), len(new_md['fields'])
    print old_md['fields'], md['fields'], new_md['fields']

    assert( len(old_md['fields'])+len(md['fields']) == len(new_md['fields']) )


#def test3():
    #pc = pypcd.load_point_cloud('test_data/partial_cup_model.pcd')
    #md = pc.get_metadata()
    #pypcd.save_point_cloud(pc, 'tmp.pcd')
    #pc2 = pypcd.load_point_cloud('tmp.pcd')
    #md2 = pc2.get_metadata()
    #assert (md


#def test4():
    #pc = load_point_cloud('/home/aeroscout/data/pcl_examples/partial_cup_model.pcd')
    #pc2 = pc.copy()
    #pc2.data['x'] += 0.1
    #pc2.save('pc2.pcd')
    #pc3 = cat_point_clouds(pc, pc2)
    #pc3.save('pc3.pcd')


#test1()
#test2()
nose.main()
