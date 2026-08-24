import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ListenerNode(Node):

    def __init__(self):
        super().__init__('listener_node')

        self.subscriber = self.create_subscription(
            String,
            '/robot_message',
            self.message_callback,
            10
        )

        self.get_logger().info('Listener node başlatıldı! Mesaj bekleniyor...')

    def message_callback(self, message):
        self.get_logger().info(f'Alındı: "{message.data}"')


def main(args=None):
    rclpy.init(args=args)

    node = ListenerNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()