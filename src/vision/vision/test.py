import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker


class ObjDetect:
    def __init__(self, model_path, view_img=True):
        self.view_img = view_img

        # 加载模型
        self.model = YOLO(model_path)
        self.names = self.model.names
        self.tracker = Tracker()

        self.depth_instrinsic_inv = np.eye(3)  # 默认深度矩阵
        self.depth = None  # 这里没有深度信息，设为 None
        self.image = None

    def load_image(self, image_path):
        # 读取图像
        self.image = cv2.imread(image_path)

    def process_image(self):
        if self.image is None:
            return

        img0 = self.image

        # 模型推理
        results = self.model.predict(img0, verbose=False)
        res = results[0]
        boxes = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        clses = res.boxes.cls.cpu().numpy()

        # 目标追踪
        detections = [[int(x1), int(y1), int(x2), int(y2)] for x1, y1, x2, y2 in boxes]
        tracks = self.tracker.update(detections)

        # 构造检测结果
        detections_list = []

        for (x1, y1, x2, y2), conf, cls_id in zip(boxes, confs, clses):
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            detection = {"id": self.names[int(cls_id)], "bbox": [x1, y1, x2, y2]}

            # 可视化
            if self.view_img:
                cv2.circle(img0, (cx, cy), 3, (0, 0, 255), -1)

            detections_list.append(detection)

        # 按 x 坐标排序检测框
        sorted_detections = sorted(detections_list, key=lambda det: det['bbox'][0])

        # 画 track ID
        sorted_tracks = sorted(tracks, key=lambda track: track['bbox'][0])
        for visual_idx, track in enumerate(sorted_tracks):
            x1, y1, x2, y2 = track['bbox']
            track_id = track['id']  # 追踪器分配的稳定 ID

            # 显示 ID（绿色）+ 排序编号（蓝色）
            cv2.putText(img0, f"Rank {visual_idx+1}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            # 画框
            cv2.rectangle(img0, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # 显示结果图像
        if self.view_img:
            cv2.imshow("Detection & Tracking", img0)
            cv2.waitKey(0)  # 等待按键事件

    def run(self, image_path):
        self.load_image(image_path)
        self.process_image()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # 模型路径
    model_path = "/home/nack/UR5e_Vision_Assemble/src/vision/vision/yolov11/models/best.pt"
    image_path = "/home/nack/UR5e_Vision_Assemble/src/vision/vision/1.png"  # 替换为你的本地图像路径

    # 创建并运行检测对象
    obj_detect = ObjDetect(model_path)
    obj_detect.run(image_path)

