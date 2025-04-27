# Subscribe Detection result and broadcast tf
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster, TransformStamped
from vision_msgs.msg import Detection2DArray, Detection2D
from geometry_msgs.msg import Point
import time

class DetTF(Node):
    def __init__(self):
        super().__init__('det_tf')
        self.subscription = self.create_subscription(
            Detection2DArray,
            'detection',
            self.det_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.tf_broadcaster = TransformBroadcaster(self)

    def det_callback(self, msg: Detection2DArray):
        cls_name = 'cube'
        objs = []

        for det in msg.detections:
            if det.id == cls_name:
                pos = det.results[0].pose.pose.position
                objs.append(pos)

        # 按照 y 坐标升序排序
        objs.sort(key=lambda p: p.x)

        # 广播 TF，按排序后的位置命名
        for idx, pos in enumerate(objs, start=1):
            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = 'camera_color_optical_frame'
            t.child_frame_id = f'cube{idx}'

            t.transform.translation.x = pos.x
            t.transform.translation.y = pos.y
            t.transform.translation.z = pos.z
            t.transform.rotation.w = 1.0
            t.transform.rotation.x = 0.0
            t.transform.rotation.y = 0.0
            t.transform.rotation.z = 0.0

            self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)

    det_tf = DetTF()

    try:
        rclpy.spin(det_tf)
    except KeyboardInterrupt:
        pass

    det_tf.destroy_node()
    rclpy.shutdown()
