# Modified from rtabmap_demos/launch/turtlebot3/turtlebot3_sim_rgbd_demo.launch.py
# RViz removed to reduce CPU/RAM load — use rtabmap_viz for visualization instead.
#
# Same setup requirements as the original demo:
# 1) Install Turtlebot3 packages
# 2) Modify turtlebot3_waffle SDF (see original file's header comment / your setup notes)
#
# Example:
# $ ros2 launch <path to this file> turtlebot3_sim_rgbd_demo_no_rviz.launch.py
#
# Teleop:
# $ ros2 run turtlebot3_teleop teleop_keyboard

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
import os

ROS_DISTRO = os.environ.get('ROS_DISTRO')


def launch_setup(context, *args, **kwargs):
    if not 'TURTLEBOT3_MODEL' in os.environ:
        os.environ['TURTLEBOT3_MODEL'] = 'waffle'

    # Directories
    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    pkg_rtabmap_demos = get_package_share_directory('rtabmap_demos')

    world = LaunchConfiguration('world').perform(context)

    if ROS_DISTRO == 'humble':
        nav2_params_file = PathJoinSubstitution(
            [FindPackageShare('rtabmap_demos'), 'params', 'humble', 'turtlebot3_rgbd_nav2_params.yaml']
        )
    else:
        nav2_params_file = PathJoinSubstitution(
            [FindPackageShare('rtabmap_demos'), 'params', 'turtlebot3_rgbd_nav2_params.yaml']
        )

    # Paths
    gazebo_launch = PathJoinSubstitution(
        [pkg_turtlebot3_gazebo, 'launch', f'turtlebot3_{world}.launch.py'])
    nav2_launch = PathJoinSubstitution(
        [pkg_nav2_bringup, 'launch', 'navigation_launch.py'])
    # NOTE: rviz_launch removed on purpose
    rtabmap_launch = PathJoinSubstitution(
        [pkg_rtabmap_demos, 'launch', 'turtlebot3', 'turtlebot3_rgbd.launch.py'])

    # Includes
    gazebo = [IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gazebo_launch]),
        launch_arguments=[
            ('x_pose', LaunchConfiguration('x_pose')),
            ('y_pose', LaunchConfiguration('y_pose'))
        ]
    )]

    if ROS_DISTRO != 'humble':
        start_gazebo_ros_depth_image_bridge_cmd = Node(
            package='ros_gz_image',
            executable='image_bridge',
            arguments=['/camera/depth/image_raw'],
            name='depth_image_bridge',
            output='screen',
        )
        gazebo.append(start_gazebo_ros_depth_image_bridge_cmd)

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([nav2_launch]),
        launch_arguments=[
            ('use_sim_time', 'true'),
            ('params_file', nav2_params_file)
        ]
    )

    max_ground_height = '0.05'
    if ROS_DISTRO == 'jazzy':
        max_ground_height = '0.02'  # for the demo, on new gazebo the depth is more accurate

    rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([rtabmap_launch]),
        launch_arguments=[
            ('localization', LaunchConfiguration('localization')),
            ('use_sim_time', 'true'),
            ('max_ground_height', max_ground_height)
        ]
    )

    return [
        # Nodes to launch (rviz removed)
         nav2,
         rtabmap
    ] + gazebo


def generate_launch_description():
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'localization', default_value='false',
            description='Launch in localization mode.'),
        DeclareLaunchArgument(
            'world', default_value='house',
            choices=['world', 'house', 'dqn_stage1', 'dqn_stage2', 'dqn_stage3', 'dqn_stage4'],
            description='Turtlebot3 gazebo world.'),
        DeclareLaunchArgument(
            'x_pose', default_value='-2.0',
            description='Initial position of the robot in the simulator.'),
        DeclareLaunchArgument(
            'y_pose', default_value='0.5',
            description='Initial position of the robot in the simulator.'),
        OpaqueFunction(function=launch_setup)
    ])