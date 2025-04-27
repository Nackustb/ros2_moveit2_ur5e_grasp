# This script is for recording images from the camera to collect data for yolo training

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import time
import numpy as np
from rcl_interfaces.msg import ParameterDescriptor
from pathlib import Path

class Record(Node):
    def __init__(self):
        super().__init__('record')
        self.get_logger().info("Record node started")

        self.declare_parameter("init_cnt", 0, ParameterDescriptor(
            name="init_cnt", description="initial count of images"))

        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, '/color/image_raw', self.image_callback, 10)
        self.image = Image()

        self.timer = self.create_timer(3.0, self.timer_callback)
        
        self.cnt = self.get_parameter("init_cnt").value

    def image_callback(self, msg:Image):
        self.image = msg
    
    def timer_callback(self):
        img = self.bridge.imgmsg_to_cv2(self.image, desired_encoding='bgr8')
        
        save_path = os.path.join(Path.home(), 'Pictures', 'record')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        cv2.imwrite(os.path.join(save_path, str(self.cnt) + '.jpg'), img)
        self.get_logger().info("Saved image %d in %s" % (self.cnt, save_path))
        self.cnt += 1

def main(args=None):
    rclpy.init(args=args)

    record = Record()

    rclpy.spin(record)

    record.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
