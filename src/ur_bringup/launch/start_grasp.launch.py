from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):


    grasp_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ur5e_gripper_control"), "/launch", "/demo.launch.py"]
        ),
    )

    nodes_to_launch = [

        grasp_launch,
    ]

    return nodes_to_launch


def generate_launch_description():
    declared_arguments = []

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
