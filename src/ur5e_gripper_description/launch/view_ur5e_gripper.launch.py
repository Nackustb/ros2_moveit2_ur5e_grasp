# Copyright (c) 2022 PickNik, Inc.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the {copyright_holder} nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import launch
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
import launch_ros
import os


def generate_launch_description():
    pkg_share = launch_ros.substitutions.FindPackageShare(
        package="ur5e_gripper_description"
    ).find("ur5e_gripper_description")
    default_model_path = os.path.join(
        pkg_share, "urdf", "ur5e_gripper.urdf.xacro"
    )
    default_rviz_config_path = os.path.join(pkg_share, "rviz", "view_ur5e_gripper.rviz")

    args = []
    args.append(
        launch.actions.DeclareLaunchArgument(
            name="model",
            default_value=default_model_path,
            description="Absolute path to gripper URDF file",
        )
    )
    args.append(
        launch.actions.DeclareLaunchArgument(
            name="rvizconfig",
            default_value=default_rviz_config_path,
            description="Absolute path to rviz config file",
        )
    )

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            LaunchConfiguration("model"),
        ]
    )
    robot_description_param = {
        "robot_description": launch_ros.parameter_descriptions.ParameterValue(
            robot_description_content, value_type=str
        )
    }

    robot_state_publisher_node = launch_ros.actions.Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description_param],
    )

    joint_state_publisher_node = launch_ros.actions.Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )

    rviz_node = launch_ros.actions.Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rvizconfig")],
    )

    nodes = [
        robot_state_publisher_node,
        joint_state_publisher_node,
        rviz_node,
    ]

    return launch.LaunchDescription(args + nodes)
