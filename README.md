# ros2_moveit2_ur5e_grasp
# 项目简介

**UR5e Dynamic Grasping System** 是一个基于 **ROS2** 和 **MoveIt2** 框架开发的智能抓取系统。该项目结合深度相机感知、目标定位、动态环境建图（OctoMap）与路径规划，实现了 **UR5e机械臂**在动态环境中的实时避障与抓取任务。
 系统具备良好的扩展性和开源性，适用于机器人抓取、动态避障、人机协作等场景研究与开发。

------

# 项目特点

- 🚀 **ROS2 + MoveIt2 深度集成**：基于现代机器人系统开发标准，支持高效通信与规划。
- 🖐️ **UR5e机械臂控制**：通过MoveIt2精准控制UR5e机械臂执行目标抓取动作。
- 🧠 **基于深度感知的目标定位**：使用深度相机实时检测与定位目标物体，生成三维抓取点。
- 🗺️ **动态环境建图与避障**：集成OctoMap，实现障碍物动态感知与规划路径避障。
- 📦 **模块化设计**：方便在不同机器人平台或不同抓取任务中快速移植和应用。
- 🛠️ **开源友好**：代码结构清晰，配套完整的安装与使用指南。

------

# 技术栈

- **ROS2 Humble**
- **MoveIt2**
- **UR5e机器人（Universal Robots）**
- **OctoMap 动态建图**
- **深度相机（ RealSense ）**
- **RViz2可视化**

# 功能包说明

| 功能包                         | 描述                                                         |
| ------------------------------ | ------------------------------------------------------------ |
| **ur_bringup**                 | UR5e机械臂的启动包，负责加载UR驱动节点，配置通信与控制接口。 |
| **ur5e_gripper_description**   | 机械爪（Robotiq Gripper）的URDF描述文件，用于建模与可视化。  |
| **ur5e_gripper_control**       | 控制机械爪的功能包，负责发布抓取、开合等指令。               |
| **ur5e_gripper_moveit_config** | 机械爪在MoveIt2中的运动规划配置包，包含规划组、末端执行器设置等。 |
| **robotiq_description**        | Robotiq Gripper的详细描述文件，包括网格模型、关节参数等。    |
| **robotiq_moveit_config**      | Robotiq Gripper专用的MoveIt2运动规划配置包。                 |
| **vision**                     | 深度相机感知模块，负责目标物体检测与三维定位。               |
| **octo_bringup**               | OctoMap建图模块的启动包，实时生成环境的三维占据栅格地图。    |
| **ur5e_octomap_moveit**        | 基于OctoMap进行动态避障的MoveIt2配置包，集成环境感知与路径规划。 |
| **sim_models**                 | 仿真模型资源包，包括UR5e、机械爪、深度相机等Gazebo仿真用模型文件。 |

# 环境配置

本项目基于 **ROS2 Humble** 和 **MoveIt2** 开发，推荐在 **Ubuntu 22.04** 环境下进行部署。

## 1. 系统要求

- Ubuntu 22.04 LTS
- ROS2 Humble Hawksbill
- MoveIt2 Humble 版本
- Python 3.10+
- C++14/17 编译支持

------

## 2. 安装ROS2 Humble

参考官方安装指南，或使用以下命令快速安装：

```
sudo apt update && sudo apt install curl gnupg2 lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list'
sudo apt update
sudo apt install ros-humble-desktop
```

安装后配置环境变量：

```
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

------

## 3. 安装MoveIt2

```
sudo apt update
sudo apt install ros-humble-moveit-*
```

如果需要仿真支持（如Gazebo），额外安装：

```
sudo apt install ros-humble-moveit-common ros-humble-moveit-ros-visualization
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control
sudo apt install ros-humble-image-pipeline
sudo apt install ros-humble-compressed-image-transport
sudo apt install ros-humble-compressed-depth-image-transport
sudo apt install ros-humble-vision-msgs
```

------

## 4. 安装UR5e机械臂依赖

```
sudo apt install ros-humble-ur-client-library
sudo apt install ros-humble-ur-description ros-humble-ur-moveit-config
```

> 注：本项目中部分UR描述文件已进行了自定义优化。

------

## 5. 安装OctoMap依赖

```
sudo apt install ros-humble-octomap-*
```

------

## 6. 安装深度相机驱动与目标检测环境（示例）

以 RealSense 相机为例（如果你用的是别的如 Orbbec，相应替换）：

```
sudo apt install ros-humble-realsense2-camera
pip install ultralytics
```

------

## 7. 克隆并编译本项目

首先新建工作区：

```
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

克隆项目源码（替换成你的GitHub仓库链接）：

```
git clone https://github.com/Nackustb/ros2_moveit2_ur5e_grasp
```

回到工作区根目录，安装依赖并编译：

```
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

编译完成后，记得 source 工作区：

```
source ~/ros2_ws/install/setup.bash
```

------

## 8. 启动示例

一键启动完整系统（建议顺序）：

```
1. 启动仿真环境 
ros2 launch ur_bringup simulation.launch.py
2. 启动抓取demo
ros2 launch ur_bringup start_grasp.launch.py
```

# 参考与致谢

本项目参考并借鉴了以下优秀开源项目与文档：

- [zitongbai/UR5e_Vision_Assemble](https://github.com/zitongbai/UR5e_Vision_Assemble)：基于ROS2的UR5e机械臂视觉装配项目，提供了UR5e机械臂与视觉模块集成的参考。
- [Universal Robots ROS2 Driver](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver)：官方UR机械臂ROS2驱动程序，支持UR5e系列机械臂的控制与反馈。
- MoveIt2: MoveIt2官方文档与示例工程，为本项目提供了路径规划、运动控制与避障功能支持。
- [Intel RealSense ROS2 Wrapper](https://github.com/IntelRealSense/realsense-ros)：深度相机集成示例（如使用RealSense D435系列），为视觉模块搭建提供了参考。
- [OctoMap ROS Integration](https://github.com/OctoMap/octomap_mapping)：OctoMap在ROS环境下的建图与感知支持，用于本项目中的动态避障功能。
