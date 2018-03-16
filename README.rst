``pypcd``
=========

What?
-----

Pure Python module to read and write point clouds stored in the
`PCD file format <http://pointclouds.org/documentation/tutorials/pcd_file_format.php>`__,
used by the `Point Cloud Library <http://pointclouds.org/>`__.

Why?
----

You want to mess around with your point cloud data without writing C++
and waiting hours for the template-heavy PCL code to compile.

You tried to get some of the Python bindings for PCL to compile
and just gave up.

How does it work?
-----------------

It parses the PCD header and loads the data (whether in ``ascii``,
``binary`` or ``binary_compressed`` format) as a
`Numpy <http://www.numpy.org>`__ structured array. It creates an
instance of the ``PointCloud``
class, containing the point cloud data as ``pc_data``, and
some convenience functions for I/O and metadata access.
See the comments in ``pypcd.py`` for some info on the point cloud
structure.

Example
-------

.. code:: python

    import pypcd
    # also can read from file handles.
    pc = pypcd.PointCloud.from_path('foo.pcd')
    # pc.pc_data has the data as a structured array
    # pc.fields, pc.count, etc have the metadata

    # center the x field
    pc.pc_data['x'] -= pc.pc_data['x'].mean()

    # save as binary compressed
    pc.save_pcd('bar.pcd', compression='binary_compressed')


How to install
--------------

.. code:: bash

    pip install pypcd

That's it! You may want to install optional dependencies such as `pandas
<https://pandas.pydata.org>`__.

You can also clone this repo and use setup.py. 

.. code:: bash

    git clone https://github.com/dimatura/pypcd

Note that downloading data assets will
require `git-lfs <https://git-lfs.github.com>`__.


Using with ROS
---------------

You can also use this library with ROS ``sensor_msgs``, but it is *not* a dependency.
You don't need to install this package with catkin -- using `pip` should be fine --
but if you want to it is possible:

Steps:

.. code:: bash
    # you need to do this manually in this case
    pip install python-lzf
    cd your_workspace/src
    git clone https://github.com/dimatura/pypcd
    mv setup_ros.py setup.py
    catkin build pypcd
    source ../devel/setup.bash


Then you can do something like this:

.. code:: python

    import pypcd
    import rospy
    from sensor_msgs.msg import PointCloud2


    def cb(msg):
        pc = PointCloud.from_msg(msg)
        pc.save('foo.pcd', compression='binary_compressed')
        # maybe manipulate your pointcloud
        pc.pc_data['x'] *= -1
        outmsg = pc.to_msg()
        # you'll probably need to set the header
        outmsg.header = msg.header
        pub.publish(outmsg)

    # ...
    sub = rospy.Subscriber('incloud', PointCloud2)
    pub = rospy.Publisher('outcloud', PointCloud2, cb)
    rospy.init('pypcd_node')
    rospy.spin()



Is it beautiful, production-ready code?
---------------------------------------

No.

What else can it do?
--------------------

There's a bunch of functionality accumulated
over time, much of it hackish and untested.
In no particular order,

-  Supports ``ascii``, ``binary`` and ``binary_compressed`` data.
   The latter requires the ``lzf`` module.
-  Decode and encode RGB into a single ``float32`` number. If
   you don't know what I'm talking about consider yourself lucky.
-  Point clouds to `pandas <https://pandas.pydata.org>`__ dataframes. 
   This in particular is quite useful,
   since `pandas` is pretty powerful and makes various operations
   such as merging point clouds or manipulating values easy.
   Conceptually, data frames are a good match to the point cloud format, since
   many point clouds in reality have heterogeneous data types - e.g.
   `x`, `y` and `z` are float fields but `label` is an int.
-  Convert to and from `ROS <http://www.ros.org>`__ PointCloud2
   messages.
   Requires the ROS ``sensor_msgs`` package with Python bindings
   installed.
   This functionality uses code developed by Jon Binney under
   the BSD license, included as ``numpy_pc2.py``.

What can't it do?
-----------------

There's no synchronization between the metadata fields in
``PointCloud``
and the data in ``pc_data``. If you change the shape of ``pc_data``
without updating the metadata fields you'll run into trouble.

I've only used it for unorganized point cloud data
(in PCD conventions, ``height=1``), not organized
data like what you get from RGBD.
However, some things may still work.

While padding and fields with count larger
than 1 seem to work, this is a somewhat
ad-hoc aspect of the PCD format, so be careful.
If you want to be safe, you're probably better off
using neither -- just name each component
of your field something like ``FIELD_00``, ``FIELD_01``, etc.

It also can't run on Python 3, yet, but there's a PR to fix this
that might get pulled in the near future.

It's slow!
----------

Try using ``binary`` or ``binary_compressed``; using
ASCII is slow and takes up a lot of space, not to
mention possibly inaccurate if you're not careful
with how you format your floats.

I found a bug / I added a feature / I made your code cleaner
------------------------------------------------------------

Thanks! You can submit a pull request. But honestly, I'm not too good
at keeping up with my github :(


TODO
----

- Better API for various operations.
- Clean up, get rid of cruft.
- Add a cli for common use cases like file type conversion.
- Better support for structured point clouds, with tests.
- Better testing.
- Better docs. More examples.
- More testing of padding
- Improve handling of multicount fields
- Better support for rgb nonsense
- Export to ply?
- Figure out if it's acceptable to use "pointcloud" as a single word.
- Package data assets in pypi?


Credits
-------

The code for compressed point cloud data was informed by looking at
`Matlab
PCL <https://www.mathworks.com/matlabcentral/fileexchange/40382-matlab-to-point-cloud-library?requestedDomain=true>`__.

@wkentaro for some minor changes.

I used `cookiecutter <https://github.com/audreyr/cookiecutter>`__ to
help with the packaging.

The code in ``numpy_pc2.py`` was developed by Jon Binney under
the BSD license for `ROS <http://www.ros.org>`__.

I want to congratulate you / insult you
---------------------------------------

My email is ``dimatura@cmu.edu``.

Copyright (C) 2015-2017 Daniel Maturana
