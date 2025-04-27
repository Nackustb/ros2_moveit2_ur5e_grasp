cmake_minimum_required(VERSION 3.5)
project(gazebo_version_helpers)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(gazebo_ros_pkgs REQUIRED)
find_package(rclcpp REQUIRED)

find_package(gazebo REQUIRED)

include_directories(
  include
  ${rclcpp_INCLUDE_DIRS}
  ${gazebo_ros_pkgs_INCLUDE_DIRS}
  ${GAZEBO_INCLUDE_DIRS}
)

add_library(${PROJECT_NAME} SHARED
  src/GazeboVersionHelpers.cpp
)

ament_target_dependencies(${PROJECT_NAME}
  rclcpp
  gazebo_ros_pkgs
)

install(TARGETS ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

ament_export_include_directories(include)
ament_export_libraries(${PROJECT_NAME})
ament_export_dependencies(rclcpp gazebo_ros_pkgs)

ament_package()


