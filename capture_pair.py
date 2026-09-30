#!/usr/bin/env python3
"""
capture_pair.py

Grabs ONE matched RGB image + depth image from your running Gazebo
simulation and saves them to disk, so you can feed the RGB one into
Depth-Anything-V2 and compare its guess against Gazebo's real depth.

HOW TO USE:
1. Start your existing RGB-D launch file (the one that gets you the
   "33+ successful mapping cycles" result) in one terminal.
2. In another terminal (with TURTLEBOT3_MODEL=waffle exported, and
   your ROS 2 environment sourced), run:
       python3 capture_pair.py
3. It will grab the first matching pair it sees and then exit.
4. Check this folder for: captured_rgb.png and captured_depth.npy

If your topic names are different from the TurtleBot3 defaults below,
edit RGB_TOPIC and DEPTH_TOPIC to match (run `ros2 topic list` to check).
"""

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import message_filters
import cv2

RGB_TOPIC = "/camera/image_raw"
DEPTH_TOPIC = "/camera/depth/image_raw"


class PairCapture(Node):
    def __init__(self):
        super().__init__("pair_capture")
        self.bridge = CvBridge()
        self.saved = False

        rgb_sub = message_filters.Subscriber(self, Image, RGB_TOPIC)
        depth_sub = message_filters.Subscriber(self, Image, DEPTH_TOPIC)

        # Matches messages that arrive within 0.05s of each other
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [rgb_sub, depth_sub], queue_size=10, slop=0.05
        )
        self.ts.registerCallback(self.callback)

        self.get_logger().info(
            f"Waiting for a matched pair on {RGB_TOPIC} and {DEPTH_TOPIC} ..."
        )

    def callback(self, rgb_msg, depth_msg):
        if self.saved:
            return

        rgb = self.bridge.imgmsg_to_cv2(rgb_msg, desired_encoding="bgr8")
        # Gazebo depth is usually 32-bit float, in meters
        depth = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding="passthrough")
        depth = np.array(depth, dtype=np.float32)

        cv2.imwrite("captured_rgb.png", rgb)
        np.save("captured_depth.npy", depth)

        self.get_logger().info(
            f"Saved captured_rgb.png ({rgb.shape}) and "
            f"captured_depth.npy ({depth.shape}, "
            f"min={np.nanmin(depth):.3f}m, max={np.nanmax(depth):.3f}m)"
        )
        self.saved = True
        rclpy.shutdown()


def main():
    rclpy.init()
    node = PairCapture()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass


if __name__ == "__main__":
    main()