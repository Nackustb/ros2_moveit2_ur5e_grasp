#include <gazebo/transport/transport.hh>

#include "../msg/grasp_event.pb.h"
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_msgs/msg/bool.hpp>
#include <boost/bind.hpp>

using GraspEventPtr = std::shared_ptr<const gazebo::msgs::GraspEvent>;

rclcpp::Publisher<std_msgs::msg::String>::SharedPtr graspEventPublisher;
rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr attachedPublisher;

/**
 * Callback to receive gazebo grasp event messages
 */
void ReceiveGraspMsg(const boost::shared_ptr<const gazebo::msgs::GraspEvent>& gzMsg)
{
  RCLCPP_INFO_STREAM(rclcpp::get_logger("gazebo_grasp_plugin_event_republisher"), 
                     "Re-publishing grasp event: " << gzMsg->DebugString());

  auto rosMsg = std::make_unique<std_msgs::msg::String>();
  rosMsg->data = gzMsg->arm() + "," + gzMsg->object();
  graspEventPublisher->publish(std::move(rosMsg));

  auto attachedMsg = std::make_unique<std_msgs::msg::Bool>();
  attachedMsg->data = gzMsg->attached();
  attachedPublisher->publish(std::move(attachedMsg));
}

int main(int argc, char** argv)
{
  // Initialize ROS and Gazebo transport
  rclcpp::init(argc, argv);
  if (!gazebo::transport::init())
  {
    RCLCPP_ERROR(rclcpp::get_logger("gazebo_grasp_plugin_event_republisher"), 
                 "Unable to initialize gazebo transport - is gazebo running?");
    return 1;
  }
  gazebo::transport::run();

  // Subscribe to Gazebo grasp event message
  gazebo::transport::NodePtr gzNode(new gazebo::transport::Node());
  gzNode->Init();
  gazebo::transport::SubscriberPtr subscriber;
  try
  {
    subscriber = gzNode->Subscribe("~/grasp_events", &ReceiveGraspMsg);
  }
  catch (std::exception& e)
  {
    RCLCPP_ERROR_STREAM(rclcpp::get_logger("gazebo_grasp_plugin_event_republisher"), 
                        "Error subscribing to topic: " << e.what());
    return 1;
  }


  // Initialize ROS publisher
  auto rosNode = rclcpp::Node::make_shared("gazebo_grasp_plugin_event_republisher");
  const std::string pubTopic = "grasp_events";
  const std::string attachedTopic = "attached_status";
  
  graspEventPublisher = rosNode->create_publisher<std_msgs::msg::String>(pubTopic, 10);
  attachedPublisher = rosNode->create_publisher<std_msgs::msg::Bool>(attachedTopic, 10);

  rclcpp::spin(rosNode);
  rclcpp::shutdown();
  gazebo::transport::fini();
  return 0;
}
