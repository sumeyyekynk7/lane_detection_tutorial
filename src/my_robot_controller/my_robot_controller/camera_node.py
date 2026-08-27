import cv2

import numpy as np 

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')

        self.bridge = CvBridge()
        self.previous_yellow_line = None
        self.previous_white_line = None
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
        minimum_midpoint_x=None
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

            if (
                minimum_midpoint_x is not None
                and midpoint_x < minimum_midpoint_x
            ):
                continue

            if abs(dy) > 0.1 * max(abs(dx), 1):
                x_points.extend([x1, x2])
                y_points.extend([y1, y2])

        if len(x_points) < 4 or max(y_points) - min(y_points) < 10:
            return None

        x_slope, x_intercept = np.polyfit(y_points, x_points, 1)

        y_bottom = image_height - 1
        y_top = image_height // 4
        x_bottom = int(x_slope * y_bottom + x_intercept)
        x_top = int(x_slope * y_top + x_intercept)

        x_bottom = int(np.clip(x_bottom, 0, image_width - 1))
        x_top = int(np.clip(x_top, 0, image_width - 1))

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

    def image_callback(self, message):
        cv_image = self.bridge.imgmsg_to_cv2(
            message,
            desired_encoding='bgr8'
        )

        height = cv_image.shape[0]
        roi = cv_image[height // 2:height, :]

        hsv_image = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2HSV
        )

        lower_yellow = np.array([15, 80, 80])
        upper_yellow = np.array([40, 255, 255])

        yellow_mask = cv2.inRange(hsv_image, lower_yellow, upper_yellow)

        lower_white = np.array([0, 0, 80])
        upper_white = np.array([180, 100, 255])

        white_mask = cv2.inRange(
            hsv_image,
            lower_white,
            upper_white
        )

        lane_mask = cv2.bitwise_or(yellow_mask, white_mask)
        edges = cv2.Canny(lane_mask, 50, 150)

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

        hough_image = roi.copy()

        yellow_line = self.average_line(
            yellow_lines,
            roi.shape[1],
            roi.shape[0]
        )
        white_line = self.average_line(
            white_lines,
            roi.shape[1],
            roi.shape[0],
            minimum_midpoint_x=roi.shape[1] // 2
        )

        yellow_line = self.smooth_line(
            yellow_line,
            self.previous_yellow_line
        )
        white_line = self.smooth_line(
            white_line,
            self.previous_white_line
        )

        if yellow_line is not None:
            self.previous_yellow_line = yellow_line

        if white_line is not None:
            self.previous_white_line = white_line

        if yellow_line is not None:
            x1, y1, x2, y2 = yellow_line
            cv2.line(hough_image, (x1, y1), (x2, y2), (0, 0, 255), 5)

        if white_line is not None:
            x1, y1, x2, y2 = white_line
            cv2.line(hough_image, (x1, y1), (x2, y2), (0, 255, 0), 5)


        moments = cv2.moments(yellow_mask)

        if moments['m00'] > 0:
            center_x = int(moments['m10'] / moments['m00'])
            center_y = int(moments['m01'] / moments['m00'])
            image_center_x = roi.shape[1] // 2
            error = center_x - image_center_x

            cv2.circle(
                roi,
                (center_x, center_y),
                8,
                (0, 0, 255),
                -1
            )

            cv2.putText(
                roi,
                f'Serit merkezi: {center_x}',
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

            cv2.line(
                roi,
                (image_center_x, 0),
                (image_center_x, roi.shape[0]),
                (0, 255, 0),
                2
            )

            cv2.putText(
                roi,
                f'Hata: {error}',
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # cv2.imshow('Tam Kamera Goruntusu', cv_image)
        # cv2.imshow('Yol Bolgesi ROI', roi)
        # cv2.imshow('Sari Maske', yellow_mask)
        # cv2.imshow('Beyaz Maske', white_mask)
        # cv2.imshow('Canny Kenarlari', edges)
        cv2.imshow('Hough Cizgileri', hough_image)
        cv2.waitKey(1)



def main(args=None):
    rclpy.init(args=args)

    node = CameraNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
