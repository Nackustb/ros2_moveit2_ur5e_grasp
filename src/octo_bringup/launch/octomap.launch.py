from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    return LaunchDescription([
        # 启动 octomap_server_node
        Node(
            package='octomap_server',
            executable='octomap_server_node',
            name='octomap_server',
            output='screen',
            parameters=[
                {
                    'frame_id': 'camera_depth_optical_frame',
                    'base_frame_id': 'base_link',  # 输出 OctoMap 的坐标系
                    'sensor_model': 'beam',
                    'resolution': 0.02,
                    'max_range': 5.0,
                    'color': False
                }
            ],
            remappings=[
                ('/cloud_in', '/depth/points')
            ]
        ),
        
        # 启动 ur5e_octomap_moveit 的 octo_map_to_planning_scene_node
        # ExecuteProcess(
        #     cmd=['ros2', 'run', 'ur5e_octomap_moveit', 'octo_map_to_planning_scene_node'],
        #     output='screen'
        # )
    ])
