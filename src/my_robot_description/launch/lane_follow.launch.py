import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():
    package_directory = get_package_share_directory(
        'my_robot_description'
    )

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                package_directory,
                'launch',
                'simulation.launch.py'
            )
        )
    )

    lane_tracker = Node(
        package='my_robot_controller',
        executable='camera_node',
        name='camera_node',
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        simulation,
        lane_tracker
    ])
