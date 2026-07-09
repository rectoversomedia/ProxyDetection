"""Tests for behavioral simulation."""

import pytest
import asyncio
from src.antidetect.behavioral import (
    BehavioralSimulator,
    BezierCurve,
    LogNormalDistribution,
    Point,
)


class TestBezierCurve:
    """Tests for Bezier curve calculations."""

    def test_bezier_curve_basic(self):
        """Test basic bezier curve creation."""
        points = [Point(0, 0), Point(100, 100), Point(200, 0)]
        curve = BezierCurve(points)

        assert curve.control_points == points

    def test_bezier_curve_start_end(self):
        """Test bezier curve starts and ends at control points."""
        start = Point(0, 0)
        end = Point(100, 100)
        curve = BezierCurve([start, end])

        start_point = curve.point_at(0)
        end_point = curve.point_at(1)

        assert start_point.x == start.x
        assert start_point.y == start.y
        assert end_point.x == end.x
        assert end_point.y == end.y

    def test_bezier_curve_points_along(self):
        """Test getting points along curve."""
        points = [Point(0, 0), Point(50, 50), Point(100, 0)]
        curve = BezierCurve(points)

        curve_points = curve.points_along_curve(5)

        assert len(curve_points) == 5

    def test_bezier_curve_requires_two_points(self):
        """Test bezier curve requires at least 2 points."""
        with pytest.raises(ValueError):
            BezierCurve([Point(0, 0)])


class TestLogNormalDistribution:
    """Tests for log-normal distribution."""

    def test_log_normal_initialization(self):
        """Test log-normal distribution initialization."""
        dist = LogNormalDistribution(mu=0, sigma=0.5)
        assert dist.mu == 0
        assert dist.sigma == 0.5

    def test_log_normal_sample_positive(self):
        """Test log-normal samples are positive."""
        dist = LogNormalDistribution()
        samples = [dist.sample() for _ in range(100)]

        assert all(s > 0 for s in samples)

    def test_log_normal_sample_with_seed(self):
        """Test reproducible sampling with seed."""
        dist1 = LogNormalDistribution(seed=42)
        dist2 = LogNormalDistribution(seed=42)

        sample1 = [dist1.sample() for _ in range(10)]
        sample2 = [dist2.sample() for _ in range(10)]

        assert sample1 == sample2

    def test_log_normal_sample_range(self):
        """Test sampling within range."""
        dist = LogNormalDistribution()
        sample = dist.sample_range(0.1, 1.0)

        assert 0.1 <= sample <= 1.0


class TestBehavioralSimulator:
    """Tests for BehavioralSimulator."""

    def test_simulator_initialization(self):
        """Test simulator can be initialized."""
        sim = BehavioralSimulator()
        assert sim is not None

    def test_simulator_with_seed(self):
        """Test simulator with seed for reproducibility."""
        sim = BehavioralSimulator(seed=123)
        assert sim._random is not None

    def test_simulator_speed_presets(self):
        """Test different speed presets."""
        for speed in ["slow", "normal", "fast"]:
            sim = BehavioralSimulator(mouse_speed=speed)
            assert sim is not None

    def test_delay_range(self):
        """Test delay range is configured."""
        sim = BehavioralSimulator(mouse_speed="normal")
        assert sim._mouse_duration_range is not None
        assert sim._pause_range is not None


class TestPoint:
    """Tests for Point class."""

    def test_point_creation(self):
        """Test point creation."""
        p = Point(10, 20)
        assert p.x == 10
        assert p.y == 20

    def test_point_distance(self):
        """Test point distance calculation."""
        p1 = Point(0, 0)
        p2 = Point(3, 4)

        assert p1.distance_to(p2) == 5.0

    def test_point_addition(self):
        """Test point addition."""
        p1 = Point(1, 2)
        p2 = Point(3, 4)

        result = p1 + p2

        assert result.x == 4
        assert result.y == 6

    def test_point_subtraction(self):
        """Test point subtraction."""
        p1 = Point(5, 7)
        p2 = Point(2, 3)

        result = p1 - p2

        assert result.x == 3
        assert result.y == 4

    def test_point_multiplication(self):
        """Test point scalar multiplication."""
        p = Point(3, 4)

        result = p * 2

        assert result.x == 6
        assert result.y == 8
