import cv2

import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from geometry_msgs.msg import Twist


class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')

        self.bridge = CvBridge()
        self.previous_yellow_line = None
        self.previous_white_line = None
        self.lane_width_ratio = 0.8
        # Piksel hatasını dönüş hızına çeviren oransal kontrol katsayısı.
        self.kp = 0.005
        self.max_angular_speed = 1.0
        self.linear_speed = 0.30
        self.previous_angular_z = 0.0
        self.steering_alpha = 0.25
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.camera_subscriber = self.create_subscription(
            Image,
            '/camera/front_camera/image_raw',
            self.image_callback,
            10
        )

        self.get_logger().info('Kamera düğümü başlatıldı.')

    def average_line(
        self,
        lines,
        image_width,
        image_height,
        expected_side=None
    ):
        if lines is None:
            return None

        x_points = []
        y_points = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            midpoint_x = (x1 + x2) / 2.0

            if expected_side == 'left' and midpoint_x > image_width * 0.55:
                continue
            if expected_side == 'right' and midpoint_x < image_width * 0.45:
                continue

            if abs(dy) > 0.1 * max(abs(dx), 1):
                x_points.extend([x1, x2])
                y_points.extend([y1, y2])

        if len(x_points) < 2 or max(y_points) - min(y_points) < 10:
            return None

        x_slope, x_intercept = np.polyfit(y_points, x_points, 1)

        y_bottom = image_height - 1
        y_top = image_height // 4
        x_bottom = int(x_slope * y_bottom + x_intercept)
        x_top = int(x_slope * y_top + x_intercept)

        # Görüntü dışındaki kesişimleri koru; kırpmak merkez hesabını bozar.

        return x_bottom, y_bottom, x_top, y_top

    def smooth_line(self, current_line, previous_line, alpha=0.25):
        if current_line is None:
            return None

        if previous_line is None:
            return current_line

        return tuple(
            int(alpha * current + (1.0 - alpha) * previous)
            for current, previous in zip(current_line, previous_line)
        )

    def lane_center(self, yellow_line, white_line, image_width, target_y):
        """Görünen sınırdan merkezi hesapla, iki sınır varsa genişliği öğren."""
        def x_at(line):
            x1, y1, x2, y2 = line
            return x1 + (x2 - x1) * (target_y - y1) / (y2 - y1)

        if yellow_line is None and white_line is None:
            return None, False

        if yellow_line is not None and white_line is not None:
            left_x = x_at(yellow_line)
            right_x = x_at(white_line)
            width = right_x - left_x
            if not 0.2 * image_width <= width <= 2.0 * image_width:
                return None, False
            self.lane_width_ratio = (
                0.25 * width / image_width + 0.75 * self.lane_width_ratio
            )
            return int((left_x + right_x) / 2), False

        # İlk karede tek sınır varsa başlangıç genişliğini kullan.
        # Her iki sınır görüldükçe bu tahmin ölçülen genişliğe yaklaşır.
        half_width = self.lane_width_ratio * image_width / 2
        if yellow_line is not None:
            return int(x_at(yellow_line) + half_width), True
        return int(x_at(white_line) - half_width), True

    def publish_command(self, linear_x, angular_z):
        command = Twist()
        command.linear.x = linear_x
        command.angular.z = angular_z
        self.cmd_vel_publisher.publish(command)

    def stop_robot(self):
        self.publish_command(0.0, 0.0)

    def detect_lane_lines(self, roi):
        """Yol bölgesinden renk maskelerini ve Hough çizgilerini çıkar."""
        hsv_image = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        lower_yellow = np.array([15, 80, 50])
        upper_yellow = np.array([40, 255, 255])

        yellow_mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)

        lower_white = np.array([0, 0, 80])
        upper_white = np.array([180, 100, 255])

        white_mask = cv2.inRange(
            hsv_image,
            lower_white,
            upper_white
        )

        # İnce gürültüleri temizle, şerit çizgisindeki küçük boşlukları kapat.
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
        yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)

        yellow_edges = cv2.Canny(yellow_mask, 50, 150)
        white_edges = cv2.Canny(white_mask, 50, 150)

        yellow_lines = cv2.HoughLinesP(
            yellow_edges,
            1,
            np.pi / 180,
            threshold=20,
            minLineLength=15,
            maxLineGap=30
        )

        white_lines = cv2.HoughLinesP(
            white_edges,
            1,
            np.pi / 180,
            threshold=20,
            minLineLength=15,
            maxLineGap=30
        )

        return yellow_mask, white_mask, yellow_lines, white_lines

    def calculate_steering(self, error):
        """P kontrolünü uygula, dönüş hızını sınırla ve yumuşat."""
        # Pozitif hata: şerit görüntüde sağda. ROS'ta negatif angular.z
        # robotu sağa döndürdüğü için işareti burada ters çeviriyoruz.
        target_angular_z = -self.kp * error
        target_angular_z = float(np.clip(
            target_angular_z,
            -self.max_angular_speed,
            self.max_angular_speed
        ))
        angular_z = (
            self.steering_alpha * target_angular_z
            + (1.0 - self.steering_alpha) * self.previous_angular_z
        )
        self.previous_angular_z = angular_z

        return angular_z

    def image_callback(self, message):
        cv_image = self.bridge.imgmsg_to_cv2(
            message,
            desired_encoding='bgr8'
        )

        height = cv_image.shape[0]
        roi = cv_image[height // 2:height, :]

        yellow_mask, white_mask, yellow_lines, white_lines = (
            self.detect_lane_lines(roi)
        )

        hough_image = roi.copy()

        yellow_line = self.average_line(
            yellow_lines,
            roi.shape[1],
            roi.shape[0],
            expected_side='left'
        )
        white_line = self.average_line(
            white_lines,
            roi.shape[1],
            roi.shape[0],
            expected_side='right'
        )

        yellow_line = self.smooth_line(
            yellow_line, self.previous_yellow_line
        )
        white_line = self.smooth_line(white_line, self.previous_white_line)
        self.previous_yellow_line = yellow_line
        self.previous_white_line = white_line

        if yellow_line is not None:
            x1, y1, x2, y2 = yellow_line
            cv2.line(hough_image, (x1, y1), (x2, y2), (0, 0, 255), 5)

        if white_line is not None:
            x1, y1, x2, y2 = white_line
            cv2.line(hough_image, (x1, y1), (x2, y2), (0, 255, 0), 5)

        # Virajı görebilmek için ROI'nin alt kenarı yerine ilerisine bak.
        center_y = int(roi.shape[0] * 0.6)
        center_x, estimated = self.lane_center(
            yellow_line, white_line, roi.shape[1], center_y
        )
        if center_x is not None:
            image_center_x = roi.shape[1] // 2
            error = center_x - image_center_x
            angular_z = self.calculate_steering(error)

            speed = self.linear_speed * (0.4 if estimated else 1.0)
            self.publish_command(speed, angular_z)

            cv2.circle(
                hough_image,
                (center_x, center_y),
                8,
                (0, 0, 255),
                -1
            )

            cv2.putText(
                hough_image,
                f'{"Tahmini merkez" if estimated else "Serit merkezi"}: {center_x}',
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

            cv2.line(
                hough_image,
                (center_x, 0),
                (center_x, roi.shape[0]),
                (255, 0, 0),
                2
            )

            cv2.line(
                hough_image,
                (image_center_x, 0),
                (image_center_x, hough_image.shape[0]),
                (0, 255, 0),
                2
            )

            cv2.putText(
                hough_image,
                f'Hata: {error}',
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            cv2.putText(
                hough_image,
                f'Donus komutu: {angular_z:.2f}',
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )
        else:
            self.previous_angular_z = 0.0
            self.stop_robot()

            cv2.putText(
                hough_image,
                'Serit bulunamadi',
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        cv2.imshow('Tam Kamera Goruntusu', cv_image)
        cv2.imshow('Yol Bolgesi ROI', roi)
        cv2.imshow('Sari Maske', yellow_mask)
        cv2.imshow('Beyaz Maske', white_mask)
        cv2.imshow('Hough Cizgileri', hough_image)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)

    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
