# Copyright 2020 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

import xacro

def generate_launch_description():
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('gazebo_ros'), 'launch'), '/gazebo.launch.py']),
             )

    realsense_path = os.path.join(get_package_share_directory('realsense2_description'))
        
    xacro_file = os.path.join(realsense_path, 'urdf', 'test_d435_camera.urdf.xacro')

    robot_description_config = xacro.process_file(xacro_file)
    params = {'robot_description': robot_description_config.toxml(), 'use_sim_time': True}

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    spawn_realsense = Node(package='gazebo_ros', executable='spawn_entity.py',
                           arguments=['-topic', 'robot_description',
                                     '-entity', 'realsense',
                                     '-x', '0.0',
                                     '-y', '0.0',
                                     '-z', '0.0'],
                           output='screen')
                         
    
    return LaunchDescription([

        # RegisterEventHandler(
        #     event_handler=OnProcessExit(
        #         target_action=spawn_realsense,
        #         on_exit=[load_joint_state_controller],
        #     )
        # ),

        gazebo,
        node_robot_state_publisher,
        spawn_realsense
    ])