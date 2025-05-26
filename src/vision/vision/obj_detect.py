import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
from .tracker import Tracker


class ObjDetect(Node):
    def __init__(self):
        super().__init__("obj_detect")
        self.declare_parameter("model_path", "/home/nack/UR5e_Vision_Assemble/src/vision/vision/yolov11/models/best.pt")
        self.declare_parameter("depth_topic", "/depth_registered/image_rect")
        self.declare_parameter("image_topic", "/color/image_raw")
        self.declare_parameter("cam_info_topic", "/color/camera_info")
        self.declare_parameter("view_image", True)
        self.declare_parameter("publish_result", True)

        # 参数读取
        model_path = self.get_parameter("model_path").value
        self.view_img = self.get_parameter("view_image").value
        self.publish_result = self.get_parameter("publish_result").value

        # 模型加载
        self.model = YOLO(model_path)
        self.names = self.model.names

        self.bridge = CvBridge()
        self.tracker = Tracker()

        self.depth_instrinsic_inv = np.eye(3)
        self.depth = None
        self.image = None

        # ROS2 订阅与发布
        self.create_subscription(Image, self.get_parameter("depth_topic").value, self.depth_callback, 10)
        self.create_subscription(Image, self.get_parameter("image_topic").value, self.image_callback, 10)
        self.create_subscription(CameraInfo, self.get_parameter("cam_info_topic").value, self.caminfo_callback, 10)
        self.detection_pub = self.create_publisher(Detection2DArray, "/detection", 10)
        self.image_pub = self.create_publisher(Image, "/detect_track", 10)

        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("YOLOv11 ObjDetect Node Initialized.")

    def caminfo_callback(self, msg):
        K = np.array(msg.k).reshape(3, 3)
        self.depth_instrinsic_inv = np.linalg.inv(K)

    def depth_callback(self, msg):
        self.depth = msg

    def image_callback(self, msg):
        self.image = msg

    def timer_callback(self):
        if self.depth is None or self.image is None:
            return

        # 获取图像
        dep = self.bridge.imgmsg_to_cv2(self.depth, desired_encoding='passthrough')
        img0 = self.bridge.imgmsg_to_cv2(self.image, desired_encoding='bgr8')

        # 模型推理
        results = self.model.predict(img0, verbose=False)
        res = results[0]
        boxes = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        clses = res.boxes.cls.cpu().numpy()

        # 目标追踪
        detections = [[int(x1), int(y1), int(x2), int(y2)] for x1, y1, x2, y2 in boxes]
        tracks = self.tracker.update(detections)

        # 构造 Detection2DArray
        detection_result = Detection2DArray()
        detections_list = []

        for (x1, y1, x2, y2), conf, cls_id in zip(boxes, confs, clses):
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            detection = Detection2D()
            detection.id = self.names[int(cls_id)]
            detection.bbox.center.position.x = float(cx)
            detection.bbox.center.position.y = float(cy)
            detection.bbox.size_x = float(x2 - x1)
            detection.bbox.size_y = float(y2 - y1)

            # 深度估计
            Z = dep[cy, cx] * 1e-3
            if Z <= 0 or np.isnan(Z):  # 防止无效的深度值
                continue
            uv1 = np.array([cx, cy, 1.0])
            XYZ = self.depth_instrinsic_inv @ uv1 * Z

            obj_hypothesis = ObjectHypothesisWithPose()
            obj_hypothesis.hypothesis.class_id = self.names[int(cls_id)]
            obj_hypothesis.hypothesis.score = float(conf)
            obj_hypothesis.pose.pose.position.x = float(XYZ[0])
            obj_hypothesis.pose.pose.position.y = float(XYZ[1])
            obj_hypothesis.pose.pose.position.z = float(XYZ[2])
            detection.results.append(obj_hypothesis)

            detections_list.append(detection)

            # 可视化
            if self.view_img:
                cv2.circle(img0, (cx, cy), 3, (0, 0, 255), -1)

        # 按 x 坐标（从左到右）排序目标检测结果
        sorted_detections = sorted(detections_list, key=lambda det: det.bbox.center.position.x)
        detection_result.detections.extend(sorted_detections)

        # 画 track ID
        sorted_tracks = sorted(tracks, key=lambda track: track['bbox'][0])

        for visual_idx, track in enumerate(sorted_tracks):
            x1, y1, x2, y2 = track['bbox']
            # 显示 ID（绿色）+ 排序编号（蓝色）
            cv2.putText(img0, f"Rank {visual_idx+1}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            # 画框
            cv2.rectangle(img0, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 发布检测结果和追踪图像
        if self.view_img:
            image_msg = self.bridge.cv2_to_imgmsg(img0, encoding='bgr8')
            image_msg.header.stamp = self.get_clock().now().to_msg()
            self.image_pub.publish(image_msg)

        if self.publish_result:
            detection_result.header.stamp = self.get_clock().now().to_msg()
            self.detection_pub.publish(detection_result)


def main(args=None):
    rclpy.init(args=args)
    node = ObjDetect()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
