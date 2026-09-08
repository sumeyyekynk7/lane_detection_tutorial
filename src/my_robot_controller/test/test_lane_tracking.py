"""Lane loss and single-boundary regression tests without a running ROS graph."""
from unittest.mock import Mock

import cv2
import numpy as np
import pytest

from my_robot_controller.camera_node import CameraNode


def make_controller():
    node = CameraNode.__new__(CameraNode)
    node.lane_width_ratio = 0.8
    node.previous_yellow_line = None
    node.previous_white_line = None
    node.kp = 0.005
    node.max_angular_speed = 1.0
    node.linear_speed = 0.3
    node.previous_angular_z = 0.0
    node.steering_alpha = 0.25
    node.bridge = Mock()
    node.cmd_vel_publisher = Mock()
    return node


@pytest.mark.parametrize('yellow,white', [
    (True, True), (True, False), (False, True), (False, False),
])
def test_camera_command_for_visible_boundaries(monkeypatch, yellow, white):
    node = make_controller()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    if yellow:
        cv2.line(frame, (70, 479), (260, 260), (0, 100, 100), 8)
    if white:
        cv2.line(frame, (570, 479), (380, 260), (160, 160, 160), 8)
    node.bridge.imgmsg_to_cv2.return_value = frame
    monkeypatch.setattr(cv2, 'imshow', lambda *args: None)
    monkeypatch.setattr(cv2, 'waitKey', lambda *args: None)
    node.image_callback(Mock())
    command = node.cmd_vel_publisher.publish.call_args.args[0]
    expected_speed = 0.3 if yellow and white else 0.12 if yellow or white else 0
    assert command.linear.x == pytest.approx(expected_speed)
    assert abs(command.angular.z) <= node.max_angular_speed
    if not yellow and not white:
        assert command.angular.z == 0


def test_single_boundary_uses_learned_width():
    node = make_controller()
    left = (100, 239, 100, 60)
    right = (500, 239, 500, 60)
    for _ in range(40):
        assert node.lane_center(left, right, 640, 144) == (300, False)
    center, estimated = node.lane_center(None, right, 640, 144)
    assert abs(center - 300) <= 1
    assert estimated
    assert node.lane_center(None, None, 640, 144) == (None, False)
    assert node.lane_center(right, left, 640, 144) == (None, False)


def test_one_hough_segment_is_enough():
    node = make_controller()
    lines = np.array([[[400, 100, 600, 230]]])
    assert node.average_line(lines, 640, 240, 'right') is not None


@pytest.mark.parametrize('error,sign', [(100, -1), (-100, 1), (0, 0)])
def test_steering_direction_and_limit(error, sign):
    node = make_controller()
    result = node.calculate_steering(error)
    assert np.sign(result) == sign
    for _ in range(100):
        result = node.calculate_steering(error * 100)
        assert abs(result) <= node.max_angular_speed


def test_lane_loss_stops_after_moving(monkeypatch):
    node = make_controller()
    monkeypatch.setattr(cv2, 'imshow', lambda *args: None)
    monkeypatch.setattr(cv2, 'waitKey', lambda *args: None)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.line(frame, (570, 479), (380, 260), (160, 160, 160), 8)
    node.bridge.imgmsg_to_cv2.return_value = frame
    node.image_callback(Mock())
    assert node.cmd_vel_publisher.publish.call_args.args[0].linear.x > 0
    node.bridge.imgmsg_to_cv2.return_value = np.zeros_like(frame)
    node.image_callback(Mock())
    command = node.cmd_vel_publisher.publish.call_args.args[0]
    assert command.linear.x == 0
    assert command.angular.z == 0
    assert node.previous_angular_z == 0
    assert node.previous_white_line is None
