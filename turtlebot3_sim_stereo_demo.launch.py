# Stereo test variant — based on turtlebot3_sim_rgbd_demo.launch.py, retargeted
# to feed RTAB-Map two mono cameras (stereo) instead of RGB-D.
#
# Requires: SDF edit adding a second "camera_right" sensor (see chat notes).
#
# Usage:
#   ros2 launch ~/turtlebot3_ws/turtlebot3_sim_stereo_demo.launch.py
#   Teleop:
#     $ ros2 run turtlebot3_teleop teleop_keyboard

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os

ROS_DISTRO = os.environ.get('ROS_DISTRO')


def launch_setup(context, *args, **kwargs):
    if not 'TURTLEBOT3_MODEL' in os.environ:
        os.environ['TURTLEBOT3_MODEL'] = 'waffle'

    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    pkg_rtabmap_launch = get_package_share_directory('rtabmap_launch')

    import shutil
    sdf_dir = os.path.join(pkg_turtlebot3_gazebo, 'models', 'turtlebot3_waffle')
    shutil.copy(os.path.join(sdf_dir, 'model_rgbd.sdf'), os.path.join(sdf_dir, 'model.sdf'))
    shutil.copy(os.path.join(sdf_dir, 'model_stereo.sdf'), os.path.join(sdf_dir, 'model.sdf'))

    world = LaunchConfiguration('world').perform(context)
    gazebo_launch = PathJoinSubstitution(
        [pkg_turtlebot3_gazebo, 'launch', f'turtlebot3_{world}.launch.py'])
    rtabmap_launch = PathJoinSubstitution(
        [pkg_rtabmap_launch, 'launch', 'rtabmap.launch.py'])

    gazebo = [IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gazebo_launch]),
        launch_arguments=[
            ('x_pose', LaunchConfiguration('x_pose')),
            ('y_pose', LaunchConfiguration('y_pose'))
        ]
    )]

    # Bridge both raw camera streams from Gazebo into ROS
    left_image_bridge = Node(
        package='ros_gz_image', executable='image_bridge',
        arguments=['/camera/image_raw'], output='screen',
    )
    right_image_bridge = Node(
        package='ros_gz_image', executable='image_bridge',
        arguments=['/camera_right/image_raw'], output='screen',
    )
    right_camera_info_bridge = Node(
    package='ros_gz_bridge', executable='parameter_bridge',
    arguments=['/camera_right/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo'],
    output='screen',
)
    gazebo += [left_image_bridge, right_image_bridge, right_camera_info_bridge]

    # Rectify both streams — RTAB-Map's stereo mode expects rectified images
    stereo_image_proc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution(
            [get_package_share_directory('stereo_image_proc'), 'launch', 'stereo_image_proc.launch.py'])]),
        launch_arguments=[
            ('left_namespace', 'camera'),
            ('right_namespace', 'camera_right'),
        ]
    )

    rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([rtabmap_launch]),
        launch_arguments=[
            ('stereo', 'true'),
            ('use_sim_time', 'true'),
            ('frame_id', 'base_footprint'),
            ('left_image_topic', '/camera/image_rect'),
            ('right_image_topic', '/camera_right/image_rect'),
            ('left_camera_info_topic', '/camera/camera_info'),
            ('right_camera_info_topic', '/camera_right/camera_info'),
            ('approx_sync', 'true'),
            ('rtabmap_viz', 'true'),
            ('rviz', 'false'),
        ]
    )

    return [stereo_image_proc, rtabmap] + gazebo


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='house',
            choices=['world', 'house', 'dqn_stage1', 'dqn_stage2', 'dqn_stage3', 'dqn_stage4']),
        DeclareLaunchArgument('x_pose', default_value='-2.0'),
        DeclareLaunchArgument('y_pose', default_value='0.5'),
        OpaqueFunction(function=launch_setup)
    ])