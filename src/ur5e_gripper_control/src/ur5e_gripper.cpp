#include "ur5e_gripper_control/ur5e_gripper.h"

UR5eGripper::UR5eGripper(const rclcpp::NodeOptions &options)
    : Node("ur5e_gripper", options) {
  /* get the target pose list from parameter server */
  std::vector<std::string> target_pose_str_list = this->get_parameter("target_pose_list").as_string_array();
  str_list_2_double_list(target_pose_str_list, target_pose_list_);

  /* create action client */
  gripper_action_client_ = rclcpp_action::create_client<GripperCommand>(this, gripper_action_name_);
  /* wait for the action server to be available */
  while (!gripper_action_client_->wait_for_action_server(std::chrono::seconds(1))) {
    RCLCPP_INFO_THROTTLE(this->get_logger(), *this->get_clock(), 500,
                         "Waiting for gripper action server to be available...");
  }
  send_goal_options_.goal_response_callback =
      std::bind(&UR5eGripper::goal_response_callback, this, std::placeholders::_1);
  send_goal_options_.feedback_callback =
      std::bind(&UR5eGripper::feedback_callback, this, std::placeholders::_1, std::placeholders::_2);
  send_goal_options_.result_callback =
      std::bind(&UR5eGripper::result_callback, this, std::placeholders::_1);

  tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
  RCLCPP_INFO(this->get_logger(), "Create Tf buffer and listener");
}

// Rest of the file remains unchanged
void UR5eGripper::init() {
  /* create move group interface */
  move_group_ = std::make_shared<moveit::planning_interface::MoveGroupInterface>(
      shared_from_this(), PLANNING_GROUP);
}

void UR5eGripper::goal_response_callback(const GoalHandleGripperCommand::SharedPtr &goal_handle) {
  if (!goal_handle) {
    RCLCPP_ERROR(this->get_logger(), "Goal was rejected by server");
  } else {
    RCLCPP_INFO(this->get_logger(), "Goal accepted by server, waiting for result");
  }
}

void UR5eGripper::feedback_callback(GoalHandleGripperCommand::SharedPtr,
                                    const std::shared_ptr<const GripperCommand::Feedback> feedback) {
  RCLCPP_INFO(this->get_logger(), "Got Feedback: Current position is %f", feedback->position);
}

void UR5eGripper::result_callback(const GoalHandleGripperCommand::WrappedResult &result) {
  switch (result.code) {
    case rclcpp_action::ResultCode::SUCCEEDED:
      break;
    case rclcpp_action::ResultCode::ABORTED:
      RCLCPP_ERROR(this->get_logger(), "Goal was aborted");
      return;
    case rclcpp_action::ResultCode::CANCELED:
      RCLCPP_ERROR(this->get_logger(), "Goal was canceled");
      return;
    default:
      RCLCPP_ERROR(this->get_logger(), "Unknown result code");
      return;
  }
  RCLCPP_INFO(this->get_logger(), "Goal is completed, current position is %f", result.result->position);
}

void UR5eGripper::get_target_pose_list(std::vector<std::vector<double>> &target_pose_list) {
  target_pose_list = target_pose_list_;
}

void UR5eGripper::str_list_2_double_list(const std::vector<std::string> &str_list,
                                         std::vector<std::vector<double>> &double_list) {
  double_list.clear();
  for (auto &pose_str : str_list) {
    std::vector<double> pose;
    std::stringstream ss(pose_str);
    std::string token;
    while (std::getline(ss, token, ',')) {
      pose.push_back(std::stod(token));
    }
    double_list.push_back(pose);
  }
}

void UR5eGripper::get_joint_target_positions(
    moveit::planning_interface::MoveGroupInterfacePtr move_group,
    const std::vector<double> &target_pose, const std::string &reference_frame,
    std::vector<double> &joint_target_positions) {
  assert(target_pose.size() == 6); // x, y, z, roll, pitch, yaw
  tf2::Quaternion quat;
  quat.setRPY(target_pose[3], target_pose[4], target_pose[5]);
  quat.normalize();
  geometry_msgs::msg::PoseStamped target_pose_stamped;
  target_pose_stamped.header.frame_id = reference_frame;
  target_pose_stamped.pose.position.x = target_pose[0];
  target_pose_stamped.pose.position.y = target_pose[1];
  target_pose_stamped.pose.position.z = target_pose[2];
  target_pose_stamped.pose.orientation.x = quat.x();
  target_pose_stamped.pose.orientation.y = quat.y();
  target_pose_stamped.pose.orientation.z = quat.z();
  target_pose_stamped.pose.orientation.w = quat.w();

  move_group->setJointValueTarget(target_pose_stamped);
  move_group->getJointValueTarget(joint_target_positions);
}

bool UR5eGripper::plan_and_execute(const std::vector<double> &target_pose) {
  std::vector<double> joint_target_positions;
  if (target_pose.size() != 6) {
    joint_target_positions = move_group_->getCurrentJointValues();
  } else {
    get_joint_target_positions(move_group_, target_pose, "base_link", joint_target_positions);
  }

  move_group_->setJointValueTarget(joint_target_positions);

  moveit::planning_interface::MoveGroupInterface::Plan plan;
  bool success_plan = (move_group_->plan(plan) == moveit::core::MoveItErrorCode::SUCCESS);
  if (success_plan) {
    move_group_->execute(plan);
  } else {
    RCLCPP_ERROR(this->get_logger(), "Failed to plan");
    return false;
  }
  return true;
}

bool UR5eGripper::grasp(double gripper_position) {
  auto gripper_goal_msg = GripperCommand::Goal();
  gripper_goal_msg.command.position = gripper_position;
  gripper_goal_msg.command.max_effort = -1.0; // do not limit the effort

  if (!gripper_action_client_->wait_for_action_server(std::chrono::seconds(10))) {
    RCLCPP_ERROR(this->get_logger(), "Action server not available after waiting");
    return false;
  }
  RCLCPP_INFO(this->get_logger(), "Sending gripper goal");
  gripper_action_client_->async_send_goal(gripper_goal_msg, send_goal_options_);
  return true;
}

void UR5eGripper::get_cube_pose(const std::string &from_frame, const std::string &to_frame,
                                std::vector<double> &cube_pose) {
  cube_pose.clear();
  geometry_msgs::msg::TransformStamped tf_msg;
  try {
    tf_msg = tf_buffer_->lookupTransform(from_frame, to_frame, tf2::TimePointZero);
  } catch (tf2::TransformException &ex) {
    RCLCPP_ERROR(this->get_logger(), "%s", ex.what());
    rclcpp::shutdown();
    return;
  }
  cube_pose.push_back(tf_msg.transform.translation.x);
  cube_pose.push_back(tf_msg.transform.translation.y);
  cube_pose.push_back(tf_msg.transform.translation.z);
  cube_pose.push_back(0);
  cube_pose.push_back(0);
  cube_pose.push_back(0);
}

void UR5eGripper::go_to_ready_position() {
  move_group_->setNamedTarget("ready");
  move_group_->move();
}
