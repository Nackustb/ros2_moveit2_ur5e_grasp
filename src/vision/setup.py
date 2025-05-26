from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'vision'
submodule_model_name = 'vision/yolov11/models'
submodule_utils_name = 'vision/yolov11/ultralytics/utils'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name, submodule_model_name, submodule_utils_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.py'))),
        # install rviz folder
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nack',
    maintainer_email='2249314748@qq.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'obj_detect = vision.obj_detect:main',
            'obj_seg = vision.obj_seg:main',
            'record = vision.record:main',
            'det_tf = vision.det_tf:main',
            'point_cloud_processor = vision.point_cloud_processor:main',
        ],
    },
)
