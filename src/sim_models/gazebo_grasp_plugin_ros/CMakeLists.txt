cmake_minimum_required(VERSION 3.5)
project(gazebo_grasp_plugin_ros)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(gazebo_dev REQUIRED)

find_package(gazebo_ros REQUIRED)
find_package(gazebo_msgs REQUIRED)
find_package(gazebo_grasp_plugin REQUIRED)

add_executable(grasp_event_republisher src/grasp_event_republisher.cpp)

include_directories(
  include
  msg
  ${rclcpp_INCLUDE_DIRS}
  ${gazebo_INCLUDE_DIRS}
)

ament_target_dependencies(
  grasp_event_republisher
  rclcpp
  gazebo_dev
  gazebo_msgs
  gazebo_ros
  gazebo_grasp_plugin
)

install(TARGETS
  grasp_event_republisher
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
