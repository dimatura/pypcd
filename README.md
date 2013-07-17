
PyPcd
=====

Python module to read and write point clouds stored in the [PCD file
format](http://pointclouds.org/documentation/tutorials/pcd_file_format.php),
used by the [Point Cloud Library](http://pointclouds.org/).

Point cloud data is internally stored as a structured
[Numpy](http://www.numpy.org) array, so you need Numpy installed.

Arbitrary fields (not only XYZ) are supported.

This code is still in alpha state.

Limitations/TODO 
================

- Decent tests.
- Only unstructured (i.e. height==1, usually from LIDAR) point clouds supported. Add support for structured (i.e. Kinect) point clouds.
- Only ASCII point cloud supported. Add support for binary point clouds.
- Interact with ROS using PointCloud2 messages.
