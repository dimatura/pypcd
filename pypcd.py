
"""
Read and write PCL .pcd files in python.
dimatura@cmu.edu, 2013
"""

import sys
import re
import pdb
import pprint
import copy
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
    # add some reasonable defaults
    if not 'count' in metadata:
        metadata['count'] = [1]*len(metadata['fields'])
    if not 'viewpoint' in metadata:
        metadata['viewpoint'] = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    if not 'version' in metadata:
        metadata['version'] = '.7'
    return metadata

def _write_header(metadata):
    """ given metadata as dictionary return a string header.
    """
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
    """ sanity check for metadata. just some basic checks.
    """
    checks = []
    required = ('version', 'fields', 'size', 'width', 'height', 'points', 'viewpoint', 'data')
    for f in required:
        if not f in metadata:
            print '%s required'%f
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
    checks.append((lambda m: m['data'].lower()=='ascii',
        'only ascii data supported'))
    ok = True
    for check, msg in checks:
        if not check(metadata):
            print 'error:', msg
            ok = False
    return ok

def _pcd_type_to_numpy(pcd_type, pcd_sz):
    """ convert from a pcd type string and size to numpy dtype.
    """
    typedict = {'F' : { 4:np.float32, 8:np.float64 },
                'I' : { 1:np.int8, 2:np.int16, 4:np.int32, 8:np.int64 },
                'U' : { 1:np.uint8 }}
    return typedict[pcd_type][pcd_sz]

def _build_dtype(metadata):
    """ buld numpy structured array dtype from pcl metadata.
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
        # get header
        while True:
            ln = f.next().strip()
            header.append(ln)
            if ln.startswith('DATA'):
                metadata = _parse_header(header)
                break
        dtype = _build_dtype(metadata)
        pc_data = np.loadtxt(f, dtype=dtype, delimiter=' ')
    #pprint.pprint(metadata)
    pc = PointCloud(metadata, pc_data)
    return pc

def save_point_cloud(pc, fname):
    """ save pointcloud to fname
    """
    header = _write_header(pc.get_metadata())
    with open(fname, 'w') as f:
        f.write(header)
        fmtstr = []
        # TODO what is the best format string for numpy savetext?
        # TODO make configurable
        for t in pc.type:
            if t=='F': fmtstr.append('%.6f')
            elif t=='I': fmtstr.append('%d')
            elif t=='U': fmtstr.append('%d')
            else: assert ("don't know about type %s"%t)
        np.savetxt(f, pc.pc_data, fmt=fmtstr)

def save_xyz_label(pc, fname, use_default_lbl=False):
    """ save a simple (x y z label) pointcloud, ignoring all other features.
    label is initialized to 1000, for jptview.
    """
    md = pc.get_metadata()
    if not use_default_lbl and not 'label' in md['fields']:
        raise Exception('label is not a field in this point cloud')
    with open(fname, 'w') as f:
        for i in xrange(pc.points):
            x,y,z = ['%.4f'%d for d in pc.pc_data['x'][i], pc.pc_data['y'][i], pc.pc_data['z'][i] ]
            lbl = '1000' if use_default_lbl else pc.pc_data['label'][i]
            f.write(' '.join((x,y,z,lbl))+'\n')

def save_xyz_intensity_label(pc, fname, use_default_lbl=False):
    md = pc.get_metadata()
    if not use_default_lbl and not 'label' in md['fields']:
        raise Exception('label is not a field in this point cloud')
    if not 'intensity' in md['fields']:
        raise Exception('intensity is not a field in this point cloud')
    with open(fname, 'w') as f:
        for i in xrange(pc.points):
            x,y,z = ['%.4f'%d for d in pc.pc_data['x'][i], pc.pc_data['y'][i], pc.pc_data['z'][i]]
            intensity = '%.4f'%pc.pc_data['intensity'][i]
            lbl = '1000' if use_default_lbl else pc.pc_data['label'][i]
            f.write(' '.join((x,y,z,intensity,lbl))+'\n')

def save_txt(pc, fname):
    with open(fname, 'w') as f:
        header = ' '.join(pc.fields)+'\n'
        f.write(header)
        fmtstr = []
        for t in pc.type:
            if t=='F': fmtstr.append('%.6f')
            elif t=='I': fmtstr.append('%d')
            elif t=='U': fmtstr.append('%d')
            else: raise Exception("don't know about type %s"%t)
        np.savetxt(f, pc.pc_data, fmt=fmtstr)

def update_field(pc, field, pc_data):
    """ updates field in-place.
    """
    pc.pc_data[field] = pc_data
    return pc

def add_fields(pc, metadata, pc_data):
    """ builds copy of pointcloud with extra fields
    """

    if len(set(metadata['fields']).intersection(set(pc.fields))) > 0:
        raise Exception("Fields with that name exist.")

    if pc.points != len(pc_data):
        raise Exception("Mismatch in number of points.")

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
    new_dtype = [(f, pc.pc_data.dtype[f]) for f in pc.pc_data.dtype.names]+dtype

    new_data = np.empty(len(pc.pc_data), new_dtype)
    for n in pc.pc_data.dtype.names:
        new_data[n] = pc.pc_data[n]
    for n,n_tmp in zip(fieldnames, pc_data.dtype.names):
        new_data[n] = pc_data[n_tmp]

    # TODO maybe just all the metadata in the dtype.
    # TODO maybe use composite structured arrays for fields with count > 1

    newpc = PointCloud(new_metadata, new_data)
    return newpc

def cat_point_clouds(pc1, pc2):
    if len(pc1.fields)!=len(pc2.fields):
        raise ValueError("Pointclouds must have same fields")
    new_metadata = pc1.get_metadata()
    new_data = np.concatenate((pc1.pc_data, pc2.pc_data))
    # TODO this only makes sense for unstructured pc?
    new_metadata['width'] = pc1.width+pc2.width
    new_metadata['points'] = pc1.points+pc2.points
    pc3 = PointCloud(new_metadata, new_data)
    return pc3

def make_xyz_point_cloud(xyz):
    md = {'version':.7,
          'fields':['x','y','z'],
          'size':[4,4,4],
          'type':['F','F','F'],
          'count':[1,1,1],
          'width':len(xyz),
          'height':1,
          'viewpoint':[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
          'points':len(xyz),
          'data':'ASCII'}
    xyz = xyz.astype(np.float32)
    dt = np.dtype([('x',np.float32), ('y',np.float32), ('z',np.float32)])
    pc_data = np.rec.fromarrays([xyz[:,0], xyz[:,1], xyz[:,2]], dtype=dt)
    #data = np.rec.fromarrays([xyz.T], dtype=dt)
    pc = PointCloud(md, pc_data)
    return pc

def make_xyz_label_point_cloud(xyzl):
    md = {'version':.7,
          'fields':['x','y','z','label'],
          'size':[4,4,4,4],
          'type':['F','F','F','F'],
          'count':[1,1,1,1],
          'width':len(xyzl),
          'height':1,
          'viewpoint':[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
          'points':len(xyzl),
          'data':'ASCII'}
    xyzl = xyzl.astype(np.float32)
    dt = np.dtype([('x',np.float32), ('y',np.float32), ('z',np.float32), ('label',np.float32)])
    pc_data = np.rec.fromarrays([xyzl[:,0], xyzl[:,1], xyzl[:,2], xyzl[:,3]], dtype=dt)
    pc = PointCloud(md, pc_data)
    return pc

class PointCloud(object):
    def __init__(self, metadata, pc_data):
        self.metadata_keys = metadata.keys()
        self.__dict__.update(metadata)
        self.pc_data = pc_data
        self.check_sanity()

    def get_metadata(self):
        """ returns copy of metadata """
        metadata = {}
        for k in self.metadata_keys:
            metadata[k] = copy.copy(getattr(self, k))
        return metadata

    def check_sanity(self):
        #pdb.set_trace()
        md = self.get_metadata()
        assert(_metadata_is_consistent(md))
        #print >>sys.stderr, 'bla', self.points, len(self.pc_data), self.pc_data.shape
        assert(len(self.pc_data)==self.points)
        assert(self.width*self.height==self.points)

    def save(self, fname):
        save_point_cloud(self, fname)

    def save_txt(self, fname):
        save_txt(self, fname)

    def save_xyz_label(self, fname, **kwargs):
        save_xyz_label(self, fname, **kwargs)

    def save_xyz_intensity_label(self, fname, **kwargs):
        save_xyz_intensity_label(self, fname, **kwargs)

    def copy(self):
        new_pc_data = np.copy(self.pc_data)
        new_metadata = self.get_metadata()
        return PointCloud(new_metadata, new_pc_data)

