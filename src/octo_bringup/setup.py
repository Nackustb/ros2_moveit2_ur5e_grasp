from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'octo_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.*'))),
        (os.path.join('share', package_name, 'rviz'), glob(os.path.join('rviz', '*.*'))),        
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nack',
    maintainer_email='2249314748@qq.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [

        ],
    },
)
