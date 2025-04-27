import numpy as np
from filterpy.kalman import KalmanFilter

class Track:
    def __init__(self, track_id, bbox):
        self.id = track_id
        self.kf = self.create_kalman_filter(bbox)
        self.bbox = bbox  # 用于输出可视化
        self.age = 0
        self.time_since_update = 0

    def create_kalman_filter(self, bbox):
        x1, y1, x2, y2 = bbox
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        w, h = x2 - x1, y2 - y1
        state = [cx, cy, w, h, 0, 0, 0, 0]

        kf = KalmanFilter(dim_x=8, dim_z=4)
        kf.F = np.eye(8)
        for i in range(4):
            kf.F[i, i+4] = 1  # 位置-速度关联

        kf.H = np.eye(4, 8)  # 只测量位置宽高
        kf.R *= 5      # 观测噪声（保守信任观测）
        kf.P *= 1000    # 初始协方差（对初始状态不自信）
        kf.Q[4:, 4:] *= 5  # 从 10 减小到 5


        kf.x[:4] = np.array(state[:4]).reshape((4, 1))
        return kf

    def predict(self):
        self.kf.predict()
        self.age += 1
        self.time_since_update += 1
        self.bbox = self.get_bbox()
        return self.bbox

    def update(self, bbox):
        x1, y1, x2, y2 = bbox
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        w, h = x2 - x1, y2 - y1
        z = np.array([cx, cy, w, h])
        self.kf.update(z)
        self.time_since_update = 0
        self.bbox = self.get_bbox()

    def get_bbox(self):
        cx, cy, w, h = self.kf.x[:4].flatten()
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2
        return [x1, y1, x2, y2]


class Tracker:
    def __init__(self, iou_threshold=0.05, max_age=10):
        self.tracks = []
        self.next_id = 0
        self.iou_threshold = iou_threshold
        self.max_age = max_age

    def update(self, detections):
        # 1. 预测所有轨迹
        for track in self.tracks:
            track.predict()

        # 2. 匹配
        matches, unmatched_tracks, unmatched_dets = self.match(detections)

        # 3. 更新匹配的轨迹
        for t_idx, d_idx in matches:
            self.tracks[t_idx].update(detections[d_idx])

        # 4. 初始化新的轨迹
        for d_idx in unmatched_dets:
            self.tracks.append(Track(self.next_id, detections[d_idx]))
            self.next_id += 1

        # 5. 移除太旧的轨迹
        self.tracks = [t for t in self.tracks if t.time_since_update < self.max_age]

        return [{'id': t.id, 'bbox': list(map(int, t.bbox))} for t in self.tracks]


    def match(self, detections):
        iou_matrix = np.zeros((len(self.tracks), len(detections)), dtype=np.float32)

        for t, track in enumerate(self.tracks):
            if track.time_since_update > self.max_age:  # 太旧的就跳过匹配
                continue
            for d, det in enumerate(detections):
                iou_matrix[t, d] = self.iou(track.bbox, det)

        matched_indices = []
        unmatched_tracks = list(range(len(self.tracks)))
        unmatched_dets = list(range(len(detections)))

        used_dets = set()

        for t in range(len(self.tracks)):
            if track.time_since_update > self.max_age:
                continue
            best_match = np.argmax(iou_matrix[t])
            if iou_matrix[t, best_match] > self.iou_threshold and best_match not in used_dets:
                matched_indices.append((t, best_match))
                unmatched_tracks.remove(t)
                unmatched_dets.remove(best_match)
                used_dets.add(best_match)

        return matched_indices, unmatched_tracks, unmatched_dets


    def iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

    

# import numpy as np

# class Track:
#     def __init__(self, track_id, bbox):
#         self.id = track_id
#         self.bbox = bbox  # (x1, y1, x2, y2)
#         self.age = 0  # 用于判断是否失效

# class Tracker:
#     def __init__(self, iou_threshold=0.3):
#         self.tracks = []
#         self.next_id = 0
#         self.iou_threshold = iou_threshold

#     def update(self, detections):
#         new_tracks = []
#         for det in detections:
#             matched = False
#             for track in self.tracks:
#                 if self.iou(track.bbox, det) > self.iou_threshold:
#                     track.bbox = det
#                     track.age = 0
#                     new_tracks.append(track)
#                     matched = True
#                     break
#             if not matched:
#                 new_tracks.append(Track(self.next_id, det))
#                 self.next_id += 1
#         # 增加 age，并删除太旧的 track
#         for track in new_tracks:
#             track.age += 1
#         self.tracks = [t for t in new_tracks if t.age < 30]
#         return [{'id': t.id, 'bbox': t.bbox} for t in self.tracks]


#     def iou(self, boxA, boxB):
#         xA = max(boxA[0], boxB[0])
#         yA = max(boxA[1], boxB[1])
#         xB = min(boxA[2], boxB[2])
#         yB = min(boxA[3], boxB[3])
#         interArea = max(0, xB - xA) * max(0, yB - yA)
#         boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
#         boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
#         iou = interArea / float(boxAArea + boxBArea - interArea)
#         return iou

