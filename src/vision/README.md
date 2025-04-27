This package is used for object detection and segmentation

# Dependences

First, create a conda env for yolov5 (we recommend python 3.10), e.g.
```bash
conda create -n yolo python=3.10
conda activate yolo
```
Then, in the folder of yolov5, install the requirements:
```bash
# in yolov5 path, e.g. src/vision/vision/yolov5
pip install -r requirements.txt
```

In order to use both python modules in ROS2 and those in conda env, you should change the conda env path mannully in the file `src/vision/vision/obj_seg.py`, `src/vision/vision/obj_detect.py`, etc. 
```python
# you should change the path here according to your conda env
sys.path.append(str(Path.home()) + '/miniforge3/envs/yolo/lib/python3.10/site-packages')
```

# Train the network

Go to the path of yolov5

```bash
# make sure you have activated the conda env. 
# otherwise:
conda activate yolo
```

Then train the model.

```shell
python segment/train.py --img 960 --batch 8 --epochs 300 --data gazebo_seg.yaml --weights yolov5s-seg.pt --cache
```

the datasets and weights will be downloaded automatically. 

* datasets in `vision/datasets`
* weights in `yolov5/yolov5s-seg.pt`

Remember to copy the training result (weights) from `yolov5/runs/exp*/weights/best.pt` to `yolov5`

