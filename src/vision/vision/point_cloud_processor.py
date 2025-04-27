import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2

class PointCloudProcessor(Node):
    def __init__(self):
        super().__init__('point_cloud_processor')
        self.declare_parameter('proportion', 0.3)
        self.declare_parameter('start_from_top', True)
        self.subscription = self.create_subscription(
            PointCloud2,
            '/depth/points',
            self.listener_callback,
            10)
        self.publisher_ = self.create_publisher(PointCloud2, '/depth/points_filtered', 10)

    def listener_callback(self, msg):
        proportion = self.get_parameter('proportion').value
        start_from_top = self.get_parameter('start_from_top').value

        if msg.height > 1:  # 有组织的点云
            max_height = msg.height
            new_height = int(proportion * max_height)
            if new_height < 1:
                self.get_logger().info('New height too small, not publishing')
                return
            if start_from_top:
                start = 0
            else:
                start = (msg.height - new_height) * msg.row_step
            data_size = new_height * msg.row_step
            new_data = msg.data[start : start + data_size]
            
            # 创建新的 PointCloud2 消息
            new_msg = PointCloud2()
            new_msg.header = msg.header
            new_msg.height = new_height
            new_msg.width = msg.width
            new_msg.fields = msg.fields
            new_msg.is_bigendian = msg.is_bigendian
            new_msg.point_step = msg.point_step
            new_msg.row_step = msg.row_step
            new_msg.data = new_data
            new_msg.is_dense = msg.is_dense
            
            # 发布过滤后的点云
            self.publisher_.publish(new_msg)
        
        elif msg.height == 1:  # 无组织的点云
            max_width = msg.width
            new_width = int(proportion * max_width)
            if new_width < 1:
                self.get_logger().info('New width too small, not publishing')
                return
            if start_from_top:
                start = 0
            else:
                start = (msg.width - new_width) * msg.point_step
            data_size = new_width * msg.point_step
            new_data = msg.data[start : start + data_size]
            
            # 创建新的 PointCloud2 消息
            new_msg = PointCloud2()
            new_msg.header = msg.header
            new_msg.height = 1
            new_msg.width = new_width
            new_msg.fields = msg.fields
            new_msg.is_bigendian = msg.is_bigendian
            new_msg.point_step = msg.point_step
            new_msg.row_step = new_width * msg.point_step
            new_msg.data = new_data
            new_msg.is_dense = msg.is_dense
            
            # 发布过滤后的点云
            self.publisher_.publish(new_msg)
        
        else:
            self.get_logger().warn('Point cloud has height <1, cannot process')

def main(args=None):
    rclpy.init(args=args)
    point_cloud_processor = PointCloudProcessor()
    rclpy.spin(point_cloud_processor)
    point_cloud_processor.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()