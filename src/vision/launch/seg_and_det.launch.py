from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='vision',
            executable='obj_detect',
            name='obj_detect',
            output='screen'
        ),
        Node(
            package='vision',
            executable='det_tf',
            name='det_tf',
            output='screen'
        ),
        Node(
            package='vision',
            executable='point_cloud_processor',
            name='point_cloud_processor',
            output='screen'
        )
    ])