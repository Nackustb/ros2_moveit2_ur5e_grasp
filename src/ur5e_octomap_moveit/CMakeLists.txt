cmake_minimum_required(VERSION 3.8)
project(ur5e_octomap_moveit)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(octomap_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)

add_executable(octo_map_to_planning_scene_node src/octomap_to_planning_scene_node.cpp)
ament_target_dependencies(octo_map_to_planning_scene_node rclcpp moveit_ros_planning_interface octomap_msgs moveit_msgs)

install(TARGETS
  octo_map_to_planning_scene_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
