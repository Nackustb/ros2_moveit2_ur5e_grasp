# Copyright 2022 Stogl Robotics Consulting UG (haftungsbeschränkt)
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
#
# Author: Denis Stogl

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros


def generate_launch_description():

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [FindPackageShare(
                    'ur5e_gripper_description'),
                    'urdf',
                    'ur5e_gripper.urdf.xacro']
            ),
        ]
    )
    robot_description = {'robot_description': robot_description_content}

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('gazebo_ros'), '/launch', '/gazebo.launch.py']
        ),
    )

    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'ur5e_gripper'],
                        output='screen')

    joint_state_broadcaster_spawner = launch_ros.actions.Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    gripper_controller_spawner = launch_ros.actions.Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
    )

    ur5e_arm_controller_spawner = launch_ros.actions.Node(
        package="controller_manager",
        executable="spawner",
        arguments=["ur5e_arm_controller", "-c", "/controller_manager"],
    )

    return LaunchDescription([
        # RegisterEventHandler(
        #   event_handler=OnProcessExit(
        #         target_action=spawn_entity,
        #         on_exit=[load_joint_state_controller],
        #     )
        # ),
        # RegisterEventHandler(
        #     event_handler=OnProcessExit(
        #         target_action=load_joint_state_controller,
        #         on_exit=[load_gripper_controller],
        #     )
        # ),
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        joint_state_broadcaster_spawner,
        gripper_controller_spawner,
        ur5e_arm_controller_spawner
    ])
