# This is for use with ROS catkin only.

cmake_minimum_required(VERSION 2.8.3)
project(pypcd)

find_package(catkin REQUIRED COMPONENTS
  rospy
  sensor_msgs
)

catkin_python_setup()

catkin_package(
  CATKIN_DEPENDS rospy sensor_msgs
)
