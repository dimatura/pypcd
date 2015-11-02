``pypcd``
=======

What?
----
Pure Python module to read and write point clouds stored in the [PCD file
format](http://pointclouds.org/documentation/tutorials/pcd_file_format.php),
used by the [Point Cloud Library](http://pointclouds.org/).

Why?
---
You want to mess around with your point cloud data without writing C++
and waiting hours for the template-heavy PCL code to compile.

You tried to get some of the Python bindings for PCL to compile
and just gave up.

How does it work?
-----------------
It parses the PCD header and loads the data (whether in `ascii`, `binary` or `binary_compressed` format) as a [Numpy](http://www.numpy.org) structured array. It creates an instance of the `PointCloud`
class, containing the point cloud data as `pc_data`, and
some convenience functions for I/O and metadata access.

Example
-------

```python
import pypcd
# also can read from file handles.
pc = pypcd.PointCloud.from_path('foo.pcd')
# pc.pc_data has the data as a structured array
# pc.fields, pc.count, etc have the metadata

# center the x field
pc.pc_data['x'] -= pc.pc_data['x'].mean()

# save as binary compressed
pc.save_pcd('bar.pcd', compression='binary_compressed')
```

Is it beautiful, production-ready code?
----------------------------------------
No.

What else can it do?
---------------------

There's a bunch of functionality accumulated
over time, much of it hackish and untested.
In no particular order,
- Supports `ascii`, `binary` and `binary_compressed` data.
  The latter requires the `lzf` module.
- Decode and encode RGB into a single `float32` number. If
  you don't know what I'm talking about consider yourself lucky.
- Point clouds from `pandas` dataframes.
- Convert to and from [ROS](http://www.ros.org) PointCloud2 messages.
  Requires the ROS `sensor_msgs` package with Python bindings installed.
  This functionality uses code developed by Jon Binney under
  the BSD license, included as `numpy_pc2.py`.


What can't it do?
-----------------

There's no synchronization between the metadata fields in `PointCloud`
and the data in `pc_data`. If you change the shape of `pc_data` 
without updating the metadata fields you'll run into trouble.


I've only used it for unorganized point cloud data
(in PCD conventions, `height=1`), not organized
data like what you get from RGBD.

While padding and fields with count larger
than 1 seem to work, this is a somewhat
ad-hoc aspect of the PCD format, so be careful.
If you want to be safe, you're probably better off
using neither -- just name each component
of your field something like ``FIELD_00``, ``FIELD_01``, etc.

It's slow!
----------

Try using `binary` or `binary_compressed`; using
ASCII is slow and takes up a lot of space, not to
mention possibly inaccurate if you're not careful
with how you format your floats.

I found a bug / I added a feature / I made your code cleaner
-------------

Thanks! Please submit a pull request.

I want to congratulate you / insult you
----------
My email is `dimatura@cmu.edu`.

Copyright (C) 2015 Daniel Maturana
