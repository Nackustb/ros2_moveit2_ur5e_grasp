cmake_minimum_required(VERSION 3.5)
project(gazebo_grasp_plugin)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find packages
find_package(ament_cmake REQUIRED)
find_package(gazebo_dev REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(gazebo_version_helpers REQUIRED)

# Find protobuf
find_package(Protobuf REQUIRED)

# Generate protobuf messages
set(msgs
 msgs/grasp_event.proto
)
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${msgs})
add_library(gazebo_grasp_msgs SHARED ${PROTO_SRCS})
target_link_libraries(gazebo_grasp_msgs ${PROTOBUF_LIBRARY})

# Add a custom command that will be run after protobuf_generate_cpp
add_custom_command(TARGET gazebo_grasp_msgs POST_BUILD
                   COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_BINARY_DIR}/msgs
                   COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_BINARY_DIR}/grasp_event.pb.h ${CMAKE_CURRENT_BINARY_DIR}/msgs/
                   COMMENT "Moving protobuf headers to msgs directory")

# Specify additional locations of header files
include_directories(
  include
  ${GAZEBO_INCLUDE_DIRS}
  ${CMAKE_CURRENT_BINARY_DIR}
  ${CMAKE_CURRENT_BINARY_DIR}/msgs
)

# Declare a cpp library
add_library(gazebo_grasp_fix SHARED src/GazeboGraspFix.cpp src/GazeboGraspGripper.cpp)

# Specify libraries to link a library
ament_target_dependencies(gazebo_grasp_fix
  gazebo_dev
  gazebo_ros
  geometry_msgs
  rclcpp
  std_msgs
  gazebo_version_helpers
)
target_link_libraries(gazebo_grasp_fix gazebo_grasp_msgs)

# Install targets
install(TARGETS gazebo_grasp_fix gazebo_grasp_msgs
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR} 
  DESTINATION include
  FILES_MATCHING PATTERN "*.pb.h"
)

#install(DIRECTORY launch
#  DESTINATION share/${PROJECT_NAME}
#)

# Ament packaging
ament_export_include_directories(include)
ament_export_libraries(gazebo_grasp_fix gazebo_grasp_msgs)
ament_export_dependencies(rclcpp gazebo_ros geometry_msgs std_msgs) # Include gazebo_version_helpers if necessary

ament_package()

