
import re
import pprint
import numpy as np

def parse_header(lines):
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

def write_header(metadata):
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

def metadata_is_consistent(metadata):
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

def build_dtype(metadata):
    fieldnames = []
    typenames = []
    for f,c,t,s in zip(metadata['fields'],
            metadata['count'],
            metadata['type'],
            metadata['size']):
        #print f, c, t, s
        # TODO  short, 2 bytes
        typedict = {'F' : { 4:np.float32, 8:np.float64 },
                    'I' : { 1:np.int8, 2:np.int16, 4:np.int32, 8:np.int64 },
                    'U' : { 1:np.uint8 }}
        if c==1:
            fieldnames.append(f)
            typenames.append(typedict[t][s])
        else:
            fieldnames.extend(['%s_%04d'%(f,i) for i in xrange(c)])
            typenames.extend([typedict[t][s]]*c)
    dtype = np.dtype(zip(fieldnames, typenames))
    return dtype

def load_point_cloud(fname):
    # extract header
    with open(fname) as f:
        header = []
        while True:
            ln = f.next().strip()
            header.append(ln)
            if ln.startswith('DATA'):
                metadata = parse_header(header)
                break
        dtype = build_dtype(metadata)
        data = np.loadtxt(f, dtype=dtype, delimiter=' ')
    #pprint.pprint(metadata)
    pc = PointCloud(metadata, data)
    return pc

def save_point_cloud(pc, fname):
    header = write_header(pc.get_metadata())
    with open(fname, 'w') as f:
        f.write(header)
        # TODO what is the best fmt
        np.savetxt(f, pc.data, fmt='%.4f')

class PointCloud(object):

    def __init__(self, metadata, data):
        self.metadata_keys = metadata.keys()
        # hack to avoid confusing metadata data key with data
        self.data_ = metadata.pop('data')
        self.__dict__.update(metadata)
        self.data = data

    def get_metadata(self):
        metadata = {}
        for k in self.metadata_keys:
            metadata[k] = getattr(self, k)
        metadata['data'] = self.data_
        return metadata

    def save(self, fname):
        save_point_cloud(self, fname)

if __name__ == '__main__':
    #parse_header(header)
    #metadata = load_point_cloud('/home/aeroscout/data/pcl_examples/partial_cup_model.pcd')
    #metadata,data = load_point_cloud('/home/aeroscout/data/pcl_examples/office_scene.pcd')
    #metadata,data = load_point_cloud('/home/aeroscout/lidardet_workspaces/2013-03-12/laser_data_009_feat.pcd')
    #pc = load_point_cloud('/home/aeroscout/lidardet_workspaces/2013-03-26/ulb_laserdata/ulb_laserdata_0050.pcd')
    pc = load_point_cloud('/home/aeroscout/data/pcl_examples/partial_cup_model.pcd')

    md = pc.get_metadata()
    #print write_header()

    save_point_cloud(pc, 'bla.pcd')
