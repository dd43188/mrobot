cmake_minimum_required(VERSION 2.8.3)

project(mrobot_bringup)

#find_package(catkin REQUIRED)
find_package(
  catkin REQUIRED COMPONENTS
  message_generation
  roscpp
  rospy
  std_msgs
)

add_message_files(
  FILES
  sr04.msg
)

generate_messages(
  DEPENDENCIES
  std_msgs
) 

#catkin_package()
catkin_package(
  CATKIN_DEPENDS message_runtime
)
