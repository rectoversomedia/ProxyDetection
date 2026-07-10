"""Behavioral simulation for human-like interactions.

This module simulates realistic human behavior patterns including:
- Bezier curve mouse movements
- Log-normal typing patterns
- Natural scroll behavior
- Random pauses and delays
- ML-resistant behavioral patterns
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Union

from ..utils.logger import get_logger

logger = get_logger(__name__)


# Lazy import for ML-resistant system to avoid circular imports
def _get_ml_system():
    """Lazy import of ML-resistant behavioral system."""
    from .behavioral_ml import MLResistantBehavioralSystem
    return MLResistantBehavioralSystem


@dataclass
class Point:
    """Represents a 2D point."""
    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        """Calculate distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Point:
        return Point(self.x * scalar, self.y * scalar)


@dataclass
class KeyPress:
    """Represents a keyboard key press."""
    key: str
    press_time: float
    release_time: float
    timestamp: float


@dataclass
class MouseEvent:
    """Represents a mouse movement event."""
    point: Point
    timestamp: float
    button: Optional[int] = None


class BezierCurve:
    """Bezier curve for smooth mouse movements."""

    def __init__(self, control_points: List[Point]):
        """
        Initialize Bezier curve with control points.

        Args:
            control_points: List of control points (at least 2)
        """
        if len(control_points) < 2:
            raise ValueError("At least 2 control points required")
        self.control_points = control_points

    def point_at(self, t: float) -> Point:
        """
        Calculate point on Bezier curve at parameter t.

        Args:
            t: Parameter from 0 to 1

        Returns:
            Point on the curve
        """
        n = len(self.control_points) - 1
        result = Point(0, 0)

        for i, point in enumerate(self.control_points):
            # Bernstein polynomial
            coefficient = self._binomial_coefficient(n, i) * (t ** i) * ((1 - t) ** (n - i))
            result = result + point * coefficient

        return result

    def points_along_curve(self, num_points: int) -> List[Point]:
        """
        Get evenly spaced points along the curve.

        Args:
            num_points: Number of points to generate

        Returns:
            List of points along the curve
        """
        return [self.point_at(i / (num_points - 1)) for i in range(num_points)]

    @staticmethod
    def _binomial_coefficient(n: int, k: int) -> float:
        """Calculate binomial coefficient n choose k."""
        if k < 0 or k > n:
            return 0
        result = 1
        for i in range(min(k, n - k)):
            result = result * (n - i) // (i + 1)
        return result


class LogNormalDistribution:
    """
    Log-normal distribution for realistic timing.

    Human behavior often follows log-normal distributions due to
    multiplicative processes in neural processing.
    """

    def __init__(self, mu: float = 0, sigma: float = 0.5, seed: Optional[int] = None):
        """
        Initialize log-normal distribution.

        Args:
            mu: Mean of the underlying normal distribution
            sigma: Standard deviation of the underlying normal distribution
            seed: Random seed for reproducibility
        """
        self.mu = mu
        self.sigma = sigma
        self._random = random.Random(seed)

    def sample(self) -> float:
        """Sample from the log-normal distribution."""
        # Box-Muller transform for normal distribution
        u1 = self._random.random()
        u2 = self._random.random()

        while u1 == 0:
            u1 = self._random.random()

        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

        # Transform to log-normal
        return math.exp(self.mu + self.sigma * z0)

    def sample_range(self, min_val: float, max_val: float) -> float:
        """Sample within a range, resampling if out of bounds."""
        while True:
            value = self.sample()
            if min_val <= value <= max_val:
                return value


class BehavioralSimulator:
    """
    Simulate human-like behavior for browser automation.

    This class provides methods for:
    - Mouse movements with Bezier curves
    - Keyboard typing with realistic timing
    - Scroll patterns
    - Random human-like delays
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        mouse_speed: str = "normal",
        typing_speed: str = "normal",
    ):
        """
        Initialize behavioral simulator.

        Args:
            seed: Random seed for reproducibility
            mouse_speed: Mouse speed preset ('slow', 'normal', 'fast')
            typing_speed: Typing speed preset ('slow', 'normal', 'fast')
        """
        self._random = random.Random(seed)

        # Speed presets
        speed_configs = {
            "slow": {
                "mouse_duration_range": (0.8, 1.5),
                "pause_range": (0.3, 0.8),
                "typing_wpm": 30,
            },
            "normal": {
                "mouse_duration_range": (0.3, 0.8),
                "pause_range": (0.1, 0.3),
                "typing_wpm": 50,
            },
            "fast": {
                "mouse_duration_range": (0.15, 0.4),
                "pause_range": (0.05, 0.15),
                "typing_wpm": 80,
            },
        }

        config = speed_configs.get(mouse_speed, speed_configs["normal"])
        self._mouse_duration_range = config["mouse_duration_range"]
        self._pause_range = config["pause_range"]
        self._typing_wpm = config["typing_wpm"] if typing_speed == "normal" else (
            30 if typing_speed == "slow" else 80
        )

    async def move_mouse(
        self,
        page,
        start: Tuple[float, float],
        end: Tuple[float, float],
        bezier_points: int = 5,
        include_micro_movements: bool = True,
    ) -> None:
        """
        Move mouse with human-like Bezier curve movement.

        Args:
            page: Browser page object
            start: Starting coordinates (x, y)
            end: Ending coordinates (x, y)
            bezier_points: Number of points in the Bezier curve
            include_micro_movements: Add micro-movements at destination
        """
        start_point = Point(start[0], start[1])
        end_point = Point(end[0], end[1])

        # Generate control points for Bezier curve
        control_points = self._generate_bezier_control_points(
            start_point,
            end_point,
            bezier_points,
        )

        # Create Bezier curve
        curve = BezierCurve(control_points)

        # Generate points along curve
        num_mouse_events = self._random.randint(20, 40)
        points = curve.points_along_curve(num_mouse_events)

        # Add variable speed (accelerate/decelerate)
        points = self._apply_speed_variation(points)

        # Add micro-movements at destination if enabled
        if include_micro_movements:
            points = self._add_micro_movements(points, end_point)

        # Calculate total duration
        duration_range = self._mouse_duration_range
        distance = start_point.distance_to(end_point)
        base_duration = distance / 500  # pixels per second
        total_duration = self._random.uniform(
            max(duration_range[0], base_duration * 0.8),
            max(duration_range[1], base_duration * 1.2),
        )

        # Move mouse with easing
        await self._execute_mouse_movement(page, points, total_duration)

    def _generate_bezier_control_points(
        self,
        start: Point,
        end: Point,
        num_points: int,
    ) -> List[Point]:
        """Generate control points for a natural-looking curve."""
        points = [start]

        # Add intermediate control points
        for _ in range(num_points - 2):
            # Random offset from direct line
            mid_x = (start.x + end.x) / 2
            mid_y = (start.y + end.y) / 2

            # Perpendicular offset
            dx = end.x - start.x
            dy = end.y - start.y
            length = math.sqrt(dx * dx + dy * dy)

            if length > 0:
                perp_x = -dy / length
                perp_y = dx / length
            else:
                perp_x, perp_y = 1, 0

            # Random offset
            offset = self._random.uniform(-50, 50)
            control_x = mid_x + perp_x * offset + self._random.uniform(-30, 30)
            control_y = mid_y + perp_y * offset + self._random.uniform(-30, 30)

            points.append(Point(control_x, control_y))

        points.append(end)
        return points

    def _apply_speed_variation(self, points: List[Point]) -> List[Point]:
        """Apply variable speed to mouse movement."""
        if len(points) < 3:
            return points

        # Create varied speed distribution
        speed_factors = []
        for i in range(len(points)):
            # Slower at start and end, faster in middle
            t = i / (len(points) - 1)
            if t < 0.1:
                factor = 0.5 + self._random.uniform(0, 0.3)
            elif t > 0.9:
                factor = 0.5 + self._random.uniform(0, 0.3)
            else:
                factor = 0.8 + self._random.uniform(0, 0.4)
            speed_factors.append(factor)

        # Return original points (speed variation handled in timing)
        return points

    def _add_micro_movements(self, points: List[Point], target: Point) -> List[Point]:
        """Add micro-movements near destination."""
        if len(points) < 5:
            return points

        # Add small jitter at the end
        for i in range(len(points) - 5, len(points)):
            if self._random.random() < 0.5:
                jitter = Point(
                    self._random.uniform(-2, 2),
                    self._random.uniform(-2, 2),
                )
                points[i] = points[i] + jitter

        return points

    async def _execute_mouse_movement(
        self,
        page,
        points: List[Point],
        total_duration: float,
    ) -> None:
        """Execute mouse movement with proper timing."""
        if not points:
            return

        num_points = len(points)
        base_interval = total_duration / num_points

        for i, point in enumerate(points):
            # Variable timing
            interval = base_interval * self._random.uniform(0.8, 1.2)
            await asyncio.sleep(interval)

            # Move to point
            try:
                await page.mouse.move(point.x, point.y)
            except Exception as e:
                logger.debug(f"Mouse move: {e}")

    async def click(
        self,
        page,
        x: float,
        y: float,
        button: str = "left",
        human_like: bool = True,
    ) -> None:
        """
        Click at coordinates with human-like timing.

        Args:
            page: Browser page object
            x: X coordinate
            y: Y coordinate
            button: Mouse button ('left', 'right', 'middle')
            human_like: Apply human-like timing and movement
        """
        if human_like:
            # Small random offset
            offset_x = self._random.uniform(-2, 2)
            offset_y = self._random.uniform(-2, 2)

            # Move to click position
            await self.move_mouse(
                page,
                (x + offset_x - 10, y + offset_y - 10),
                (x + offset_x, y + offset_y),
            )

            # Random delay before click
            await asyncio.sleep(self._random.uniform(0.05, 0.15))

        # Perform click
        try:
            await page.mouse.click(x, y, button=button)
        except Exception as e:
            logger.debug(f"Click: {e}")

        if human_like:
            # Small delay after click
            await asyncio.sleep(self._random.uniform(0.05, 0.15))

    async def double_click(
        self,
        page,
        x: float,
        y: float,
        human_like: bool = True,
    ) -> None:
        """Double click at coordinates."""
        if human_like:
            await self.click(page, x, y, human_like=True)
            await asyncio.sleep(self._random.uniform(0.05, 0.1))

        await self.click(page, x, y, human_like=False)

    async def hover(
        self,
        page,
        x: float,
        y: float,
    ) -> None:
        """Hover over coordinates."""
        await self.move_mouse(page, (x, y), (x, y))

    async def type_text(
        self,
        page,
        text: str,
        delay_range: Tuple[float, float] = (0.05, 0.2),
        include_errors: bool = True,
        error_rate: float = 0.02,
    ) -> None:
        """
        Type text with human-like timing.

        Args:
            page: Browser page object
            text: Text to type
            delay_range: Range for delay between keystrokes (min, max) seconds
            include_errors: Include occasional typos
            error_rate: Probability of making a typo
        """
        for char in text:
            # Random delay before key press
            await asyncio.sleep(self._random.uniform(*delay_range))

            # Handle special characters
            if char in ["\n", "\t"]:
                key = "Enter" if char == "\n" else "Tab"
                try:
                    await page.keyboard.press(key)
                except Exception as e:
                    logger.debug(f"Keyboard press: {e}")

                if char == "\n":
                    await asyncio.sleep(self._random.uniform(0.1, 0.3))
                continue

            # Regular character typing
            try:
                # Maybe make a typo
                if include_errors and self._random.random() < error_rate:
                    # Type wrong character
                    wrong_char = self._random.choice("qweryuiopasdfghjklzxcvbnm")
                    await page.keyboard.type(wrong_char)
                    await asyncio.sleep(self._random.uniform(0.05, 0.1))

                    # Backspace
                    await page.keyboard.press("Backspace")
                    await asyncio.sleep(self._random.uniform(0.05, 0.1))

                await page.keyboard.type(char)
            except Exception as e:
                logger.debug(f"Type text: {e}")

        # Random pause after typing
        await asyncio.sleep(self._random.uniform(0.1, 0.3))

    async def type_with_log_normal(
        self,
        page,
        text: str,
    ) -> None:
        """
        Type text with log-normal timing distribution.

        This is more realistic as human typing intervals follow log-normal distribution.

        Args:
            page: Browser page object
            text: Text to type
        """
        # Calculate average delay from WPM
        avg_delay = 60 / self._typing_wpm

        # Log-normal distribution for delays
        log_normal = LogNormalDistribution(
            mu=math.log(avg_delay) - 0.1,  # Adjust for realistic timing
            sigma=0.5,
            seed=self._random.randint(0, 2**31 - 1),
        )

        for char in text:
            # Sample delay from log-normal
            delay = log_normal.sample_range(0.02, 0.5)
            await asyncio.sleep(delay)

            # Type character
            try:
                if char == "\n":
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(log_normal.sample_range(0.1, 0.5))
                else:
                    await page.keyboard.type(char)
            except Exception as e:
                logger.debug(f"Type with log-normal: {e}")

    async def scroll(
        self,
        page,
        amount: int,
        direction: str = "down",
        smooth: bool = True,
    ) -> None:
        """
        Scroll with natural movement.

        Args:
            page: Browser page object
            amount: Amount to scroll in pixels
            direction: Scroll direction ('up', 'down', 'left', 'right')
            smooth: Use smooth scrolling
        """
        if direction == "down":
            delta_y = -amount
        elif direction == "up":
            delta_y = amount
        elif direction == "left":
            delta_y = amount
        else:
            delta_y = -amount

        if smooth:
            # Smooth scrolling with multiple smaller scrolls
            scroll_amount = 100
            num_scrolls = abs(amount) // scroll_amount

            for _ in range(num_scrolls):
                # Variable scroll amount
                actual_scroll = scroll_amount * self._random.uniform(0.8, 1.2)
                try:
                    await page.mouse.wheel(
                        delta_x=0 if direction in ["up", "down"] else actual_scroll,
                        delta_y=-actual_scroll if direction == "down" else actual_scroll,
                    )
                except Exception as e:
                    logger.debug(f"Scroll: {e}")

                # Random pause between scrolls
                await asyncio.sleep(self._random.uniform(0.02, 0.08))
        else:
            # Instant scroll
            try:
                await page.evaluate(f"window.scrollBy(0, {delta_y})")
            except Exception as e:
                logger.debug(f"Instant scroll: {e}")

    async def scroll_to_element(
        self,
        page,
        selector: str,
    ) -> None:
        """
        Scroll to bring an element into view.

        Args:
            page: Browser page object
            selector: CSS selector for the element
        """
        try:
            await page.evaluate(f"""
                document.querySelector('{selector}').scrollIntoView({{
                    behavior: 'smooth',
                    block: 'center'
                }})
            """)
            # Wait for scroll animation
            await asyncio.sleep(self._random.uniform(0.3, 0.6))
        except Exception as e:
            logger.debug(f"Scroll to element: {e}")

    async def human_delay(self, min_seconds: float = 0.1, max_seconds: float = 0.5) -> None:
        """
        Add a human-like random delay.

        Args:
            min_seconds: Minimum delay
            max_seconds: Maximum delay
        """
        delay = self._random.uniform(min_seconds, max_seconds)

        # Add occasional longer pauses (like thinking)
        if self._random.random() < 0.1:
            delay += self._random.uniform(0.5, 2.0)

        await asyncio.sleep(delay)

    async def random_action_sequence(
        self,
        page,
        num_actions: int = 3,
    ) -> None:
        """
        Perform a random sequence of human-like actions.

        Args:
            page: Browser page object
            num_actions: Number of actions to perform
        """
        actions = [
            lambda: self.human_delay(0.5, 2.0),
            lambda: self.scroll(page, self._random.randint(100, 300)),
            lambda: page.mouse.move(
                self._random.randint(100, 500),
                self._random.randint(100, 500),
            ),
        ]

        for _ in range(num_actions):
            action = self._random.choice(actions)
            await action()


# =============================================================================
# ML-RESISTANT BEHAVIORAL METHODS
# =============================================================================

def _add_ml_resistant_methods():
    """Add ML-resistant methods to BehavioralSimulator class."""

    async def move_mouse_ml_resistant(
        self,
        page,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> None:
        """
        Move mouse with ML-resistant patterns.

        This method uses cognitive simulation, natural errors,
        and variable timing to evade ML-based detection.

        Args:
            page: Browser page object
            start: Starting coordinates (x, y)
            end: Ending coordinates (x, y)
        """
        from .behavioral_ml import get_ml_behavior_system

        ml_system = get_ml_behavior_system()

        # Generate natural path
        path = ml_system.mouse.generate_path(start, end, num_points=30)

        # Simulate occasional "look away"
        if ml_system.should_spoof_human():
            look_away_time = ml_system.get_look_away_time()
            # Move cursor away briefly
            await page.mouse.move(start[0] + 50, start[1] + 50)
            await asyncio.sleep(look_away_time)
            await page.mouse.move(start[0], start[0])

        # Execute path with variable timing
        for x, y, duration_ms in path:
            await asyncio.sleep(duration_ms / 1000)
            try:
                await page.mouse.move(x, y)
            except Exception as e:
                logger.debug(f"Mouse move: {e}")

    async def type_text_ml_resistant(
        self,
        page,
        text: str,
    ) -> None:
        """
        Type text with ML-resistant patterns.

        This includes natural typing errors, correction patterns,
        and variable timing.

        Args:
            page: Browser page object
            text: Text to type
        """
        from .behavioral_ml import get_ml_behavior_system

        ml_system = get_ml_behavior_system()
        error_gen = ml_system.errors

        for char in text:
            # Occasional thinking pause
            think_delay = ml_system.timing.get_inter_action_delay("typing")
            if self._random.random() < 0.1:
                await asyncio.sleep(think_delay * 2)

            # Check for typo
            if error_gen.should_make_typo():
                typo_char = error_gen.get_typo_char(char)
                try:
                    await page.keyboard.type(typo_char)
                except Exception as e:
                    logger.debug(f"Type error: {e}")

                # Correction delay
                await asyncio.sleep(error_gen.get_correction_delay())

                # Backspace
                try:
                    await page.keyboard.press("Backspace")
                except Exception as e:
                    logger.debug(f"Backspace: {e}")

                await asyncio.sleep(error_gen.get_correction_delay())

            # Check for double tap
            if error_gen.should_double_tap():
                char_to_type = char + char
            else:
                char_to_type = char

            # Type the character(s)
            try:
                if char == "\n":
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(ml_system.timing.get_typing_delay("special"))
                elif char == "\t":
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(ml_system.timing.get_typing_delay("special"))
                elif char == " ":
                    await page.keyboard.press("Space")
                    await asyncio.sleep(ml_system.timing.get_typing_delay("space"))
                else:
                    await page.keyboard.type(char_to_type)
                    await asyncio.sleep(ml_system.timing.get_typing_delay())

            except Exception as e:
                logger.debug(f"Type error: {e}")

        # Random pause after typing
        await asyncio.sleep(self._random.uniform(0.1, 0.5))

    async def click_ml_resistant(
        self,
        page,
        x: float,
        y: float,
    ) -> None:
        """
        Click with ML-resistant patterns.

        Args:
            page: Browser page object
            x: X coordinate
            y: Y coordinate
        """
        from .behavioral_ml import get_ml_behavior_system

        ml_system = get_ml_behavior_system()

        # Hover before click (like checking target)
        if ml_system.mouse.should_hover():
            hover_duration = ml_system.mouse.get_hover_duration()
            try:
                await page.mouse.move(x, y)
            except Exception as e:
                logger.debug(f"Hover move: {e}")
            await asyncio.sleep(hover_duration)

        # Small offset
        offset_x = self._random.uniform(-3, 3)
        offset_y = self._random.uniform(-3, 3)

        # Move to position
        await self.move_mouse_ml_resistant(
            page,
            (x + offset_x - 20, y + offset_y - 20),
            (x + offset_x, y + offset_y),
        )

        # Random delay before click
        await asyncio.sleep(self._random.uniform(0.05, 0.2))

        # Click
        try:
            await page.mouse.click(x + offset_x, y + offset_y)
        except Exception as e:
            logger.debug(f"Click: {e}")

        # Delay after click
        await asyncio.sleep(self._random.uniform(0.05, 0.15))

    async def scroll_ml_resistant(
        self,
        page,
        amount: int,
        direction: str = "down",
    ) -> None:
        """
        Scroll with ML-resistant patterns.

        Args:
            page: Browser page object
            amount: Amount to scroll
            direction: Scroll direction
        """
        from .behavioral_ml import get_ml_behavior_system

        ml_system = get_ml_behavior_system()

        # Generate scroll sequence
        scrolls = ml_system.scroll.generate_scroll_sequence(amount, direction)

        for delta, delay in scrolls:
            await asyncio.sleep(delay)
            try:
                if direction in ["up", "down"]:
                    await page.mouse.wheel(delta_y=-delta if direction == "down" else delta)
                else:
                    await page.mouse.wheel(delta_x=delta if direction == "right" else -delta)
            except Exception as e:
                logger.debug(f"Scroll: {e}")

    async def human_think(self) -> float:
        """
        Simulate human thinking/hesitation.

        Returns:
            Duration of thinking in seconds
        """
        from .behavioral_ml import get_ml_behavior_system

        ml_system = get_ml_behavior_system()
        think_time = ml_system.cognitive.simulate_think_time()

        await asyncio.sleep(think_time)
        return think_time

    async def simulate_fatigue(self, session_duration_minutes: float) -> float:
        """
        Simulate session fatigue - gradually slows down behavior.

        Args:
            session_duration_minutes: How long the session has been running

        Returns:
            Fatigue multiplier (0.5-1.0)
        """
        from .behavioral_ml import get_ml_behavior_system

        ml_system = get_ml_behavior_system()
        cognitive_state = ml_system.cognitive.get_state()

        # Calculate fatigue
        fatigue = min(1.0, session_duration_minutes / 30)
        cognitive_state.fatigue_level = fatigue

        return 1.0 - (fatigue * 0.5)


# ML-resistant methods are now integrated into MLResistantBehavioralSimulator
# See src/antidetect/behavioral_ml.py for full ML-resistant implementation
