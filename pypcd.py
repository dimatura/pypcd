
import re
import pprint
import numpy as np

def _parse_header(lines):
    metadata = {}
    for ln in lines:
        if ln.startswith('#') or len(ln) < 2: continue
        match = re.match('(\w+)\s+([\w\s\.]+)', ln)
        if not match:
            print "warning: can't understand line: %s"%ln
            continue
        key, value = match.group(1).lower(), match.group(2)
        if key=='version':
            metadata[key] = value
        elif key in ('fields', 'type'):
            metadata[key] = value.split()
        elif key in ('size', 'count'):
            metadata[key] = map(int, value.split())
        elif key in ('width', 'height', 'points'):
            metadata[key] = int(value)
        elif key=='viewpoint':
            metadata[key] = map(float, value.split())
        elif key=='data':
            metadata[key] = value
        # TODO apparently count is not required?
    if not 'count' in metadata:
        metadata['count'] = [1]*len(metadata['fields'])
    if not 'viewpoint' in metadata:
        metadata['viewpoint'] = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    if not 'version' in metadata:
        metadata['version'] = '.7'
    return metadata

def _write_header(metadata):
    template ="""\
VERSION {version}
FIELDS {fields}
SIZE {size}
TYPE {type}
COUNT {count}
WIDTH {width}
HEIGHT {height}
VIEWPOINT {viewpoint}
POINTS {points}
DATA {data}
"""
    str_metadata = metadata.copy()
    str_metadata['fields'] = ' '.join(metadata['fields'])
    str_metadata['size'] = ' '.join(map(str, metadata['size']))
    str_metadata['type'] = ' '.join(metadata['type'])
    str_metadata['count'] = ' '.join(map(str, metadata['count']))
    str_metadata['width'] = str(metadata['width'])
    str_metadata['height'] = str(metadata['height'])
    str_metadata['viewpoint'] = ' '.join(map(str, metadata['viewpoint']))
    str_metadata['points'] = str(metadata['points'])
    tmpl = template.format(**str_metadata)
    return tmpl

def _metadata_is_consistent(metadata):
    checks = []
    required = ('version', 'fields', 'size', 'width', 'height', 'points', 'viewpoint', 'data')
    checks.append((lambda m: all([k in m for k in required]),
        'missing field'))
    checks.append((lambda m: len(m['type'])==len(m['count'])==len(m['fields']),
        'length of type, count and fields must be equal'))
    checks.append((lambda m: m['height'] > 0,
        'height must be greater than 0'))
    checks.append((lambda m: m['width'] > 0,
        'width must be greater than 0'))
    checks.append((lambda m: m['points'] > 0,
        'points must be greater than 0'))
    checks.append((lambda m: m['data']=='ascii',
        'only ascii data supported'))
    ok = True
    for check, msg in checks:
        if not check(metadata):
            print 'error:', msg
            ok = False
    return ok


def _pcd_type_to_numpy(pcd_type, pcd_sz):
    typedict = {'F' : { 4:np.float32, 8:np.float64 },
                'I' : { 1:np.int8, 2:np.int16, 4:np.int32, 8:np.int64 },
                'U' : { 1:np.uint8 }}
    return typedict[pcd_type][pcd_sz]

def _build_dtype(metadata):
    """ buld dtype from pcl metadata
    """
    fieldnames = []
    typenames = []
    for f,c,t,s in zip(metadata['fields'],
            metadata['count'],
            metadata['type'],
            metadata['size']):
        np_type = _pcd_type_to_numpy(t, s)
        if c==1:
            fieldnames.append(f)
            typenames.append(np_type)
        else:
            fieldnames.extend(['%s_%04d'%(f,i) for i in xrange(c)])
            typenames.extend([np_type]*c)
    dtype = np.dtype(zip(fieldnames, typenames))
    return dtype

def load_point_cloud(fname):
    """ load pointcloud from fname
    """
    with open(fname) as f:
        header = []
        while True:
            ln = f.next().strip()
            header.append(ln)
            if ln.startswith('DATA'):
                metadata = _parse_header(header)
                break
        dtype = _build_dtype(metadata)
        data = np.loadtxt(f, dtype=dtype, delimiter=' ')
    #pprint.pprint(metadata)
    pc = PointCloud(metadata, data)
    return pc

def save_point_cloud(pc, fname):
    """ save pointcloud to fname
    """
    header = _write_header(pc.get_metadata())
    with open(fname, 'w') as f:
        f.write(header)
        # TODO what is the best fmt
        np.savetxt(f, pc.data, fmt='%.4f')

def add_fields(pc, metadata, data):
    """ builds copy of pointcloud with extra fields
    """
    new_metadata = pc.get_metadata()
    new_metadata['fields'].extend(metadata['fields'])
    new_metadata['count'].extend(metadata['count'])
    new_metadata['size'].extend(metadata['size'])
    new_metadata['type'].extend(metadata['type'])

    # parse metadata to add
    # TODO factor this
    fieldnames, typenames = [], []
    for f,c,t,s in zip(metadata['fields'],
            metadata['count'],
            metadata['type'],
            metadata['size']):
        np_type = _pcd_type_to_numpy(t, s)
        if c==1:
            fieldnames.append(f)
            typenames.append(np_type)
        else:
            fieldnames.extend(['%s_%04d'%(f,i) for i in xrange(c)])
            typenames.extend([np_type]*c)
    dtype = zip(fieldnames, typenames)
    # new dtype. could be inferred?
    new_dtype = [(f, pc.data.dtype[f]) for f in pc.data.dtype.names]+dtype

    # new data as list of arrays
    new_data_cols = [pc.data[n] for n in pc.data.dtype.names]
    for n in data.dtype.names:
        new_data_cols.append(data[n])
    # new data as recarray
    new_data = np.rec.fromarrays(new_data_cols, new_dtype)
    # new pc
    newpc = PointCloud(new_metadata, new_data)
    return newpc

def cat_point_clouds(pc1, pc2):
    if len(pc1.fields)!=len(pc2.fields):
        raise ValueError("Pointclouds must have same fields")
    new_metadata = pc1.get_metadata()
    new_data = np.concatenate((pc1.data, pc2.data))
    # TODO this only makes sense for unstructured pc?
    new_metadata['width'] = pc1.width+pc2.width
    new_metadata['points'] = pc1.points+pc2.points
    pc3 = PointCloud(new_metadata, new_data)
    return pc3

class PointCloud(object):
    def __init__(self, metadata, data):
        self.metadata_keys = metadata.keys()
        # hack to avoid confusing metadata data key with data
        self.data_ = metadata.pop('data')
        self.__dict__.update(metadata)
        self.data = data
        self.check_sanity()

    def get_metadata(self):
        """ returns copy of metadata """
        metadata = {}
        for k in self.metadata_keys:
            metadata[k] = getattr(self, k)
        metadata['data'] = self.data_
        return metadata

    def check_sanity(self):
        md = self.get_metadata()
        assert(_metadata_is_consistent(md))
        assert(len(self.data)==self.points)
        if self.height==1:
            assert(self.width==self.points)

    def save(self, fname):
        save_point_cloud(self, fname)

    def copy(self):
        new_data = np.copy(self.data)
        new_metadata = self.get_metadata()
        return PointCloud(new_metadata, new_data)

"""
#_parse_header(header)
#metadata = load_point_cloud('/home/aeroscout/data/pcl_examples/partial_cup_model.pcd')
#metadata,data = load_point_cloud('/home/aeroscout/data/pcl_examples/office_scene.pcd')
#metadata,data = load_point_cloud('/home/aeroscout/lidardet_workspaces/2013-03-12/laser_data_009_feat.pcd')
#pc = load_point_cloud('/home/aeroscout/lidardet_workspaces/2013-03-26/ulb_laserdata/ulb_laserdata_0050.pcd')
pc = load_point_cloud('/home/aeroscout/data/pcl_examples/partial_cup_model.pcd')
md = pc.get_metadata()
#print _write_header()
save_point_cloud(pc, 'bla.pcd')
"""

"""
pc = load_point_cloud('/home/aeroscout/data/pcl_examples/partial_cup_model.pcd')
new_dt = [(f, pc.data.dtype[f]) for f in pc.data.dtype.fields]
new_data = [pc.data[n] for n in pc.data.dtype.names]
md = {'fields' : ['bla', 'bar'], 'count' : [1, 1], 'size' : [4, 4], 'type' : ['F', 'F']}
d = np.rec.fromarrays( (np.random.random(len(pc.data)), np.random.random(len(pc.data))) )
newpc = add_fields(pc, md, d)
"""

"""
pc = load_point_cloud('/home/aeroscout/data/pcl_examples/partial_cup_model.pcd')
pc2 = pc.copy()
pc2.data['x'] += 0.1
pc2.save('pc2.pcd')
pc3 = cat_point_clouds(pc, pc2)
pc3.save('pc3.pcd')
"""
