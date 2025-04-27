#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"

int main(int argc, char * argv[]){

    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("test_gripper_in_gazebo");

    auto publisher = node->create_publisher<std_msgs::msg::Float64MultiArray>("/robotiq_gripper_controller/commands", 10);

    RCLCPP_INFO(node->get_logger(), "node created");

    std_msgs::msg::Float64MultiArray msg;

    using namespace std::chrono_literals;

    msg.data.push_back(0);
    publisher->publish(msg);
    std::this_thread::sleep_for(2s);

    msg.data[0] = 0.4;
    publisher->publish(msg);
    std::this_thread::sleep_for(2s);

    msg.data[0] = 0.2;
    publisher->publish(msg);
    std::this_thread::sleep_for(2s);

    msg.data[0] = 0.7;
    publisher->publish(msg);
    std::this_thread::sleep_for(2s);

    return 0;
}