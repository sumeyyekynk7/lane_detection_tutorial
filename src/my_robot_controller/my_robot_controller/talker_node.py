import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TalkerNode(Node):

    def __init__(self):
        super().__init__('talker_node')

        self.publisher = self.create_publisher(
            String,
            '/robot_message',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.send_message
        )

        self.counter = 0

        self.get_logger().info('Talker node başlatıldı!')

    def send_message(self):
        message = String()

        message.data = f'Merhaba! Mesaj numarası: {self.counter}'

        self.publisher.publish(message)

        self.get_logger().info(f'Gönderildi: "{message.data}"')

        self.counter += 1


def main(args=None):
    rclpy.init(args=args)

    node = TalkerNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
