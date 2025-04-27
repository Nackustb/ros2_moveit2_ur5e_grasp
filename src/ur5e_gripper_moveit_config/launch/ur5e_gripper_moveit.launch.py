import os

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ur_moveit_config.launch_common import load_yaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution


def launch_setup(context, *args, **kwargs):

    # General arguments
    description_package = LaunchConfiguration("description_package")
    description_file = LaunchConfiguration("description_file")
    moveit_config_package = LaunchConfiguration("moveit_config_package")
    moveit_joint_limits_file = LaunchConfiguration("moveit_joint_limits_file")
    moveit_config_file = LaunchConfiguration("moveit_config_file")
    prefix = LaunchConfiguration("prefix")
    use_sim_time = LaunchConfiguration("use_sim_time")
    # launch_rviz = LaunchConfiguration("launch_rviz")


    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare(description_package), "urdf", description_file]),
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    # MoveIt Configuration
    robot_description_semantic_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare(moveit_config_package), "srdf", moveit_config_file]
            ),
        ]
    )
    robot_description_semantic = {"robot_description_semantic": robot_description_semantic_content}

    robot_description_kinematics = PathJoinSubstitution(
        [FindPackageShare(moveit_config_package), "config", "kinematics.yaml"]
    )

    robot_description_planning = {
        "robot_description_planning": load_yaml(
            str(moveit_config_package.perform(context)),
            os.path.join("config", str(moveit_joint_limits_file.perform(context))),
        )
    }

    # Planning Configuration
    ompl_planning_pipeline_config = {
        "move_group": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": """default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints""",
            "start_state_max_bounds_error": 0.1,
        }
    }
    ompl_planning_yaml = load_yaml("ur5e_gripper_moveit_config", "config/ompl_planning.yaml")
    ompl_planning_pipeline_config["move_group"].update(ompl_planning_yaml)

    # Trajectory Execution Configuration
    controllers_yaml = load_yaml("ur5e_gripper_moveit_config", "config/moveit_controllers.yaml")
    
    moveit_controllers = {
        "moveit_simple_controller_manager": controllers_yaml,
        "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager",
        "trajectory_execution" : {
            "allowed_execution_duration_scaling": 2.0,  # change execution time scaling here
            "allowed_goal_duration_margin": 0.5,
            "allowed_start_tolerance": 0.01,
        }
    }

    trajectory_execution = {
        "moveit_manage_controllers": False,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "publish_robot_description":True,
        "publish_robot_description_semantic":True,
    }

    octomap_config = {'octomap_frame': 'camera_depth_optical_frame', 'octomap_resolution': 0.02}
    octomap_updater_config = load_yaml('ur5e_gripper_moveit_config', 'config/sensors_3d.yaml')    
    # Start the actual move_group node/action server
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            ompl_planning_pipeline_config,
            trajectory_execution,
            moveit_controllers,
            planning_scene_monitor_parameters,
            {"use_sim_time": use_sim_time},
            octomap_config,
            octomap_updater_config,
        ],
    )


    nodes_to_start = [
        move_group_node, 
        # rviz_node, 
    ]

    return nodes_to_start


def generate_launch_description():
    declared_arguments = []
    # General arguments
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_package",
            default_value="ur5e_gripper_moveit_config",
            description="Description package with robot URDF/XACRO files. Usually the argument \
        is not set, it enables use of a custom description.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "description_file",
            default_value="ur5e_gripper.urdf.xacro",
            description="URDF/XACRO description file with the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_config_package",
            default_value="ur5e_gripper_moveit_config",
            description="MoveIt config package with robot SRDF/XACRO files. Usually the argument \
        is not set, it enables use of a custom moveit config.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_config_file",
            default_value="ur5e_gripper.srdf.xacro",
            description="MoveIt SRDF/XACRO description file with the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_joint_limits_file",
            default_value="joint_limits.yaml",
            description="MoveIt joint limits that augment or override the values from the URDF robot_description.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Make MoveIt to use simulation time. This is needed for the trajectory planing in simulation.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "prefix",
            default_value='""',
            description="Prefix of the joint names, useful for \
        multi-robot setup. If changed than also joint names in the controllers' configuration \
        have to be updated.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument("launch_rviz", default_value="true", description="Launch RViz?")
    )

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
