from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):

    # load urdf, launch gazebo
    dual_ur5e_gripper_control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ur5e_gripper_moveit_config"), "/launch", "/ur5e_gripper_sim_control.launch.py"]
        ),
        launch_arguments={
            "launch_rviz": "true",
        }.items(),
    )

    # load moveit config
    dual_ur5e_gripper_moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ur5e_gripper_moveit_config"), "/launch", "/ur5e_gripper_moveit.launch.py"]
        ),
        launch_arguments={
            "use_sim_time": "true",
        }.items(),
    )

    # depth image registered (align to color image)
    register_depth_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("vision"), "/launch", "/register_depth.launch.py"]
        ),
    )

    vision_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("vision"), "/launch", "/seg_and_det.launch.py"]
        ),
    )
    octo_launch =  IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("octo_bringup"), "/launch", "/octomap.launch.py"]
        ),
    )
    nodes_to_launch = [
        dual_ur5e_gripper_control_launch,
        dual_ur5e_gripper_moveit_launch,
        register_depth_launch,
        vision_launch,
        # octo_launch,
    ]

    return nodes_to_launch


def generate_launch_description():
    declared_arguments = []

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
