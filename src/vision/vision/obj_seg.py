# ros2 import
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage, Image
from sensor_msgs.msg import CameraInfo
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
import cv2
from cv_bridge import CvBridge
import time
import numpy as np
from .wait_for_message import wait_for_message

# address path 
import os
import sys
from pathlib import Path
# add conda env path
# sys.path.append(str(Path.home()) + '/miniforge3/envs/yolo/lib/python3.10/site-packages')

# yolov5 import

from pathlib import Path

# 使用 Path() 让 ROOT 成为 Path 类型
FILE = Path(__file__).resolve()
ROOT = Path("/home/nack/UR5e_Vision_Assemble/src/vision/vision")
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# 如果要切换到 yolov5 目录
ROOT = ROOT / "yolov5"  # 使用 / 拼接路径
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import torch
from ultralytics.utils.plotting import Annotator, colors
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.torch_utils import select_device
from yolov5.utils.general import check_img_size, check_imshow, non_max_suppression, scale_boxes
from yolov5.utils.augmentations import letterbox
from yolov5.utils.segment.general import process_mask, masks2segments

class ObjSegmentation(Node):
    def __init__(self):
        super().__init__('obj_segmentation')
        self.get_logger().info("ObjSegmentation node started")
        self.bridge = CvBridge()

        # ROS2 parameters declaration
        self.declare_parameter("weights_path", str(ROOT / 'best.pt'), ParameterDescriptor(
            name="weights_path", description="path to weights file"))
        
        self.declare_parameter("data_path", str(ROOT / 'data/gazebo_seg.yaml'), ParameterDescriptor(
            name="data_path", description="path to dataset.yaml"))

        self.declare_parameter("image_topic", "/color/image_raw/compressed", ParameterDescriptor(
            name="image_topic", description="image topic"))
        
        self.declare_parameter("image_info_topic", "/color/camera_info", ParameterDescriptor(
            name="camera_info_topic", description="camera info topic"))
        
        self.declare_parameter("depth_topic", "/depth_registered/image_rect", ParameterDescriptor(
            name="depth_topic", description="depth image topic"))
        
        self.declare_parameter("depth_info_topic", "/depth_registered/camera_info", ParameterDescriptor(
            name="depth_info_topic", description="depth camera info topic"))
        
        self.declare_parameter("segmentation_freq", 30, ParameterDescriptor(
            name="segmentation_freq", description="detection frequency [Hz]"))
        
        self.declare_parameter("view_image", True, ParameterDescriptor(
            name="view_image", description="whether to show the detect result in a window"))

        self.declare_parameter("publish_result", True, ParameterDescriptor(
            name="publish_result", description="whether to publish the detect result"))
        
        # set parameter use_sim_time to true
        use_sim_time = rclpy.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)
        self.set_parameters([use_sim_time])

        # ROS2 camera info subscriber
        image_info_topic = self.get_parameter("image_info_topic").value
        depth_info_topic = self.get_parameter("depth_info_topic").value
        success, self.image_info = wait_for_message(CameraInfo, self, image_info_topic, time_to_wait=10.0)
        if not success:
            self.get_logger().error(f"cannot get camera info from {image_info_topic}")
            exit()
        success, self.depth_info = wait_for_message(CameraInfo, self, depth_info_topic, time_to_wait=10.0)
        if not success:
            self.get_logger().error(f"cannot get depth camera info from {depth_info_topic}")
            exit()
        self.imgsz = (self.image_info.height, self.image_info.width)
        self.depth_instrinsic = np.array(self.depth_info.k, dtype=np.float32).reshape(3, 3)
        self.depth_instrinsic_inv = np.linalg.inv(self.depth_instrinsic)

        # ROS2 detection/segmentation publisher
        self.publish_result = self.get_parameter("publish_result").value
        self.detection_pub = self.create_publisher(Detection2DArray, 'obj_detection', 10)
        self.detection_result = Detection2DArray()

        # load yolov5 model
        self.half = False # use FP16 half-precision inference
        device = select_device('0')
        weights = self.get_parameter("weights_path").value
        data = self.get_parameter("data_path").value
        self.get_logger().info(f"loading model with weights in {weights}")
        self.model = DetectMultiBackend(weights, device=device, dnn=False, data=data, fp16=self.half)
        self.stride, self.names, self.pt = self.model.stride, self.model.names, self.model.pt
        self.imgsz = check_img_size(self.imgsz, s=self.stride)
        self.get_logger().info(f'yolov5 model warmup')
        self.model.warmup(imgsz=(1, 3, *self.imgsz)) # BCHW
        self.view_img = check_imshow(warn=True) and self.get_parameter("view_image").value # check if we can view image

        # ROS2 image, depth subscriber
        # the callback function depends on yolov5 model, thus init after model
        image_topic = self.get_parameter("image_topic").value
        depth_topic = self.get_parameter("depth_topic").value

        self.image = CompressedImage() # for color image, we use compressed image so that we can get the image faster
        self.depth = Image() # for depth image, it is very strange that using compressed image would slow down the transport, thus we use raw image
        self.image_sub = self.create_subscription(CompressedImage, image_topic, self.image_callback, 10)
        self.depth_sub = self.create_subscription(Image, depth_topic, self.depth_callback, 10)
        
        # ROS2 timer
        self.segmentation_freq = self.get_parameter("segmentation_freq").value
        self.timer = self.create_timer(1.0 / self.segmentation_freq, self.timer_callback)


    def depth_callback(self, msg:CompressedImage):
        self.depth = msg
    
    def image_callback(self, msg:CompressedImage):
        self.image = msg

    def timer_callback(self):
        """
        Callback function for timer
        Process the image and depth data, and publish the detection result
        in frequency of segmentation_freq
        """
        # check if we have received up to date image and depth
        tol_sec = 0.5
        image_stamp = self.image.header.stamp.sec + self.image.header.stamp.nanosec * 1e-9
        depth_stamp = self.depth.header.stamp.sec + self.depth.header.stamp.nanosec * 1e-9
        now_stamp = self.get_clock().now().nanoseconds * 1e-9
        if abs(image_stamp - now_stamp) > tol_sec or abs(depth_stamp - now_stamp) > tol_sec:
            self.get_logger().warn(f"image stamp = {image_stamp}, depth stamp = {depth_stamp}, now stamp = {now_stamp}")
            if abs(image_stamp - now_stamp) > tol_sec:
                self.get_logger().warn(f"image stamp is not up to date")
            if abs(depth_stamp - now_stamp) > tol_sec:
                self.get_logger().warn(f"depth stamp is not up to date")
            return
        
        # image preprocessing
        img = self.bridge.compressed_imgmsg_to_cv2(self.image, desired_encoding='rgb8') # HWC
        dep = self.bridge.imgmsg_to_cv2(self.depth, desired_encoding='passthrough') # HWC, unit: mm

        img0 = img.copy() # for visualization
        # Padded resize
        img = letterbox(img, new_shape=self.imgsz, stride=self.stride, auto=self.pt)[0]
        img = img.transpose(2, 0, 1) # HWC to CHW
        img = np.ascontiguousarray(img) # contiguous array for memory efficiency
        img = torch.from_numpy(img).to(self.model.device) # convert to torch gpu
        img = img.half() if self.half else img.float()
        img /= 255.0 # 0 - 255 to 0.0 - 1.0
        if len(img.shape) == 3:
            img = img[None] # expand for batch dim

        # inference
        augment = False # augmented inference
        # pred, proto = self.model(img, augment=augment, visualize=False)[:2]
        pred = self.model(img, augment=augment, visualize=False)


        # NMS
        conf_thres = 0.25
        iou_thres = 0.45
        classes = None # optional filter by class
        agnostic_nms = False # class-agnostic NMS
        max_det = 1000 # maximum detections per image
        # pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det, nm=32)
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        # process predictions
        det = pred[0] # we only has one image
        proto = proto[0]
        annotator = Annotator(img0, line_width=3, example=str(self.names))
        self.detection_result = Detection2DArray()
        if len(det):
            masks = process_mask(proto, det[:, 6:], det[:, :4], img.shape[2:], upsample=True)  # HWC
            det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], img0.shape).round()  # rescale boxes to im0 size

            # mask plotting
            annotator.masks(
                masks, 
                colors=[colors(x, True) for x in det[:, 5]], 
                im_gpu=img[0]
            )

            for j, (*xyxy, conf, cls) in enumerate(reversed(det[:, :6])):
                # prepare detection result msg
                detection = Detection2D()
                detection.id = self.names[int(cls)]
                x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                detection.bbox.center.position.x = (x1 + x2) / 2.0
                detection.bbox.center.position.y = (y1 + y2) / 2.0
                detection.bbox.size_x = float(x2 - x1)
                detection.bbox.size_y = float(y2 - y1)
                # add hypothesis to detection result msg
                obj_hypothesis = ObjectHypothesisWithPose()
                obj_hypothesis.hypothesis.class_id = self.names[int(cls)]
                obj_hypothesis.hypothesis.score = float(conf)
                Z = dep[int(detection.bbox.center.position.y), int(detection.bbox.center.position.x)]
                Z = Z * 1e-3 # mm to m
                uv1 = np.array([detection.bbox.center.position.x, detection.bbox.center.position.y, 1.0])
                XZ_YZ_1 = np.dot(self.depth_instrinsic_inv, uv1)
                XYZ = np.array([XZ_YZ_1[0] * Z, XZ_YZ_1[1] * Z, Z])
                obj_hypothesis.pose.pose.position.x = XYZ[0]
                obj_hypothesis.pose.pose.position.y = XYZ[1]
                obj_hypothesis.pose.pose.position.z = XYZ[2]
                detection.results.append(obj_hypothesis)
                self.detection_result.detections.append(detection)

                if self.view_img:
                    c = int(cls)  # integer class
                    label = f'{self.names[c]} {conf:.2f}'
                    annotator.box_label(xyxy, label, color=colors(c, True))
                    # use cv2 draw a red point labeled with XYZ[2] in img0
                    cv2.circle(img0, (int(detection.bbox.center.position.x), int(detection.bbox.center.position.y)), 2, (0, 0, 255), -1)
                    cv2.putText(img0, f'{XYZ[2]:.2f}', (int(detection.bbox.center.position.x), int(detection.bbox.center.position.y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv2.LINE_AA)
        print(len(self.detection_result.detections))
        self.detection_result.header.stamp = self.get_clock().now().to_msg()
        self.detection_result.header.frame_id = 'camera_color_optical_frame'
        self.detection_pub.publish(self.detection_result)


        if self.view_img:
            img0 = annotator.result()
            cv2.namedWindow('obj_detect', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow('obj_detect', img0.shape[1], img0.shape[0])
            cv2.imshow('obj_detect', img0)
            cv2.waitKey(1)
        
def main(args=None):
    rclpy.init(args=args)
    obj_segmentation = ObjSegmentation()
    rclpy.spin(obj_segmentation)
    obj_segmentation.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()