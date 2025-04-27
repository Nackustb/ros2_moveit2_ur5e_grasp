#include <rclcpp/rclcpp.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <octomap_msgs/msg/octomap.hpp>
#include <octomap_msgs/msg/octomap_with_pose.hpp>
#include <moveit_msgs/msg/planning_scene.hpp>

class OctoMapToPlanningSceneNode : public rclcpp::Node {
public:
  OctoMapToPlanningSceneNode() : Node("octo_map_to_planning_scene_node") {
    // 创建 PlanningSceneInterface，不传递 shared_from_this()
    planning_scene_interface_ = std::make_shared<moveit::planning_interface::PlanningSceneInterface>();

    // 订阅 OctoMap 主题
    octomap_sub_ = this->create_subscription<octomap_msgs::msg::Octomap>(
      "octomap_binary", 10, [this](const octomap_msgs::msg::Octomap::SharedPtr msg) {
        // 创建 OctomapWithPose 消息
        octomap_msgs::msg::OctomapWithPose octomap_with_pose;
        octomap_with_pose.header.frame_id = "camera_depth_optical_frame"; // 调整为你的帧
        octomap_with_pose.octomap = *msg;
        // 设置原点
        octomap_with_pose.origin.position.x = 0.0;
        octomap_with_pose.origin.position.y = 0.0;
        octomap_with_pose.origin.position.z = 0.0;
        octomap_with_pose.origin.orientation.w = 1.0;

        // 创建 PlanningScene 消息
        moveit_msgs::msg::PlanningScene planning_scene;
        planning_scene.is_diff = true;
        planning_scene.world.octomap = octomap_with_pose;

        // 应用到规划场景
        planning_scene_interface_->applyPlanningScene(planning_scene);
      });
  }

private:
  std::shared_ptr<moveit::planning_interface::PlanningSceneInterface> planning_scene_interface_;
  rclcpp::Subscription<octomap_msgs::msg::Octomap>::SharedPtr octomap_sub_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<OctoMapToPlanningSceneNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
