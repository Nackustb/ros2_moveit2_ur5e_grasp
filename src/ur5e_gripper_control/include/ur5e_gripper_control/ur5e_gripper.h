#pragma once
#include <memory>
#include <string>
#include <vector>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

#include <control_msgs/action/gripper_command.hpp>

using GripperCommand = control_msgs::action::GripperCommand;
using GoalHandleGripperCommand = rclcpp_action::ClientGoalHandle<GripperCommand>;

class UR5eGripper : public rclcpp::Node {
public:
  explicit UR5eGripper(const rclcpp::NodeOptions &options);
  void init();

  void get_target_pose_list(std::vector<std::vector<double>> &target_pose_list);
  void get_joint_target_positions(
      moveit::planning_interface::MoveGroupInterfacePtr move_group,
      const std::vector<double> &target_pose, const std::string &reference_frame,
      std::vector<double> &joint_target_positions);
  bool plan_and_execute(const std::vector<double> &target_pose);
  bool grasp(double gripper_position);
  void get_cube_pose(const std::string &from_frame, const std::string &to_frame,
                    std::vector<double> &cube_pose);
  void go_to_ready_position();

private:
  void goal_response_callback(const GoalHandleGripperCommand::SharedPtr &goal_handle);
  void feedback_callback(GoalHandleGripperCommand::SharedPtr,
                        const std::shared_ptr<const GripperCommand::Feedback> feedback);
  void result_callback(const GoalHandleGripperCommand::WrappedResult &result);
  void str_list_2_double_list(const std::vector<std::string> &str_list,
                              std::vector<std::vector<double>> &double_list);

  std::shared_ptr<moveit::planning_interface::MoveGroupInterface> move_group_;
  moveit::planning_interface::PlanningSceneInterface planning_scene_interface_;
  rclcpp_action::Client<GripperCommand>::SharedPtr gripper_action_client_;
  rclcpp_action::Client<GripperCommand>::SendGoalOptions send_goal_options_;
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

  std::vector<std::vector<double>> target_pose_list_;
  std::string gripper_action_name_ = "/gripper_controller/gripper_cmd";
  const std::string PLANNING_GROUP = "ur_manipulator";
};
