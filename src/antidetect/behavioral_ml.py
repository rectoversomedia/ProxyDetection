"""ML-resistant behavioral patterns module.

This module provides behavioral patterns that evade ML-based bot detection systems
by simulating human cognitive patterns, fatigue, attention variation, and natural errors.

ML-based detection systems analyze:
- Mouse movement patterns (velocity, acceleration, curvature)
- Typing patterns (speed variation, error correction)
- Scroll behavior
- Timing patterns between actions
- Session-level patterns (fatigue, attention)
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# COGNITIVE LOAD SIMULATION
# =============================================================================

@dataclass
class CognitiveState:
    """Represents current cognitive state of the simulated human."""

    # Cognitive load factors
    attention_level: float = 1.0  # 0-1, 1 = fully focused
    cognitive_load: float = 0.0  # 0-1, higher = more distracted
    fatigue_level: float = 0.0  # 0-1, higher = more tired

    # Task complexity affects behavior
    current_task_complexity: float = 0.0  # 0-1

    # Time tracking
    session_start: float = field(default_factory=time.time)
    last_action_time: float = field(default_factory=time.time)

    def update_after_action(self, action_type: str) -> None:
        """Update cognitive state after an action."""
        current_time = time.time()
        time_since_last = current_time - self.last_action_time

        # Update fatigue (slowly increases over time)
        session_duration = current_time - self.session_start
        self.fatigue_level = min(1.0, session_duration / (30 * 60))  # Max after 30 min

        # Attention recovers during pauses
        if time_since_last > 5:
            self.attention_level = min(1.0, self.attention_level + 0.1)

        # Reset after action
        self.last_action_time = current_time

        # Update based on action type
        if action_type == "typing":
            self.cognitive_load = min(1.0, self.cognitive_load + 0.1)
            self.attention_level = max(0.3, self.attention_level - 0.05)
        elif action_type == "complex_form":
            self.cognitive_load = min(1.0, self.cognitive_load + 0.2)
        elif action_type == "reading":
            self.attention_level = max(0.5, self.attention_level - 0.1)
        elif action_type == "pause":
            # Rest recovers attention
            self.cognitive_load = max(0, self.cognitive_load - 0.1)

    def get_speed_multiplier(self) -> float:
        """Get speed multiplier based on cognitive state."""
        # Fatigue slows down
        fatigue_penalty = self.fatigue_level * 0.3

        # Low attention slows down
        attention_penalty = (1 - self.attention_level) * 0.2

        # Cognitive load slows down
        load_penalty = self.cognitive_load * 0.15

        return max(0.5, 1.0 - fatigue_penalty - attention_penalty - load_penalty)

    def get_error_probability(self) -> float:
        """Get probability of making an error."""
        base_error_rate = 0.02  # 2% base error rate

        # Fatigue increases errors
        fatigue_multiplier = 1 + self.fatigue_level * 2

        # Low attention increases errors
        attention_multiplier = 1 + (1 - self.attention_level) * 1.5

        # High cognitive load increases errors
        load_multiplier = 1 + self.cognitive_load * 2

        return min(0.3, base_error_rate * fatigue_multiplier * attention_multiplier * load_multiplier)


class CognitiveSimulator:
    """
    Simulate human cognitive patterns.

    This class models:
    - Attention fluctuation
    - Cognitive load accumulation
    - Fatigue buildup
    - Task complexity effects
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize cognitive simulator.

        Args:
            seed: Random seed
        """
        self._random = random.Random(seed)
        self._state = CognitiveState()

        # Configuration
        self._config = {
            "fatigue_rate": 0.0003,  # Fatigue increase per second
            "attention_recovery_rate": 0.1,  # Attention recovery per pause
            "cognitive_load_rate": 0.05,  # Load increase per complex action
            "max_pause_for_recovery": 10,  # Seconds for full attention recovery
        }

    def get_state(self) -> CognitiveState:
        """Get current cognitive state."""
        return self._state

    def reset(self) -> None:
        """Reset cognitive state."""
        self._state = CognitiveState()

    def simulate_think_time(self) -> float:
        """
        Simulate "thinking time" before an action.

        Returns:
            Seconds to wait
        """
        # Base think time
        base_time = self._random.uniform(0.5, 2.0)

        # Factor in cognitive load
        load_factor = 1 + self._state.cognitive_load * 2

        # Factor in fatigue (slower thinking when tired)
        fatigue_factor = 1 + self._state.fatigue_level * 0.5

        # Factor in attention (slower when distracted)
        attention_factor = 1 + (1 - self._state.attention_level)

        # Random variation
        variation = self._random.uniform(0.8, 1.5)

        think_time = base_time * load_factor * fatigue_factor * attention_factor * variation

        # Occasional longer pauses (like reconsidering)
        if self._random.random() < 0.1:
            think_time += self._random.uniform(2.0, 5.0)

        return think_time

    def should_look_away(self) -> bool:
        """
        Determine if the simulated human would "look away".

        This simulates humans getting distracted.

        Returns:
            True if looking away
        """
        # Higher fatigue = more likely to look away
        look_away_prob = 0.05 + self._state.fatigue_level * 0.15

        # Lower attention = more likely to look away
        look_away_prob += (1 - self._state.attention_level) * 0.1

        return self._random.random() < look_away_prob

    def get_look_away_duration(self) -> float:
        """Get duration of looking away."""
        # Usually short, sometimes longer
        if self._random.random() < 0.8:
            return self._random.uniform(1, 3)  # Short glance
        else:
            return self._random.uniform(5, 15)  # Longer distraction


# =============================================================================
# ML-RESISTANT TIMING PATTERNS
# =============================================================================

class MLResistantTiming:
    """
    Timing patterns that evade ML-based behavioral analysis.

    ML classifiers can detect bots by:
    - Perfectly regular intervals
    - Lack of natural variation
    - Unrealistic response times
    - No "thinking" pauses

    This class provides timing that:
    - Uses heavy-tailed distributions
    - Includes occasional "thinking" pauses
    - Varies based on cognitive state
    - Includes occasional "mistakes" in timing
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize ML-resistant timing.

        Args:
            seed: Random seed
        """
        self._random = random.Random(seed)
        self._cognitive = CognitiveSimulator(seed)

    @property
    def cognitive_simulator(self) -> CognitiveSimulator:
        """Get cognitive simulator."""
        return self._cognitive

    def get_inter_action_delay(self, context: str = "default") -> float:
        """
        Get delay between actions.

        Args:
            context: Context of the action

        Returns:
            Delay in seconds
        """
        # Base delays by context
        base_delays = {
            "default": (0.1, 0.5),
            "typing": (0.05, 0.2),
            "click": (0.1, 0.3),
            "scroll": (0.2, 1.0),
            "page_load": (1.0, 3.0),
            "form_field": (0.2, 0.8),
            "submit": (0.5, 2.0),
        }

        min_delay, max_delay = base_delays.get(context, (0.1, 0.5))

        # Apply cognitive state
        speed_mult = self._cognitive.get_state().get_speed_multiplier()
        min_delay *= speed_mult
        max_delay *= speed_mult

        # Use heavy-tailed distribution (more realistic)
        # 80% quick, 20% slower
        if self._random.random() < 0.8:
            delay = self._random.uniform(min_delay, max_delay)
        else:
            delay = self._random.uniform(max_delay, max_delay * 5)

        # Occasional "thinking" pause
        think_time = self._cognitive.simulate_think_time()
        if self._random.random() < 0.15:
            delay += think_time

        return delay

    def get_mouse_move_duration(
        self,
        distance: float,
        base_speed: float = 500,
    ) -> float:
        """
        Get duration for mouse movement.

        Args:
            distance: Distance in pixels
            base_speed: Base pixels per second

        Returns:
            Duration in seconds
        """
        # Base duration from distance
        base_duration = distance / base_speed

        # Cognitive effects
        speed_mult = self._cognitive.get_state().get_speed_multiplier()

        # Add natural variation (40-200% of base)
        variation = self._random.uniform(0.4, 2.0)

        # Occasional pauses mid-movement (like hesitating)
        hesitation = 0
        if self._random.random() < self._cognitive.get_state().fatigue_level * 0.3:
            hesitation = self._random.uniform(0.1, 0.5)

        duration = base_duration * speed_mult * variation + hesitation

        # Clamp to reasonable range
        return max(0.1, min(3.0, duration))

    def get_typing_delay(self, char_type: str = "normal") -> float:
        """
        Get delay between keystrokes.

        Args:
            char_type: Type of character (normal, special, punctuation)

        Returns:
            Delay in seconds
        """
        # Different delays for different key types
        if char_type == "special":
            base = self._random.uniform(0.2, 0.5)
        elif char_type == "punctuation":
            base = self._random.uniform(0.15, 0.4)
        elif char_type == "space":
            base = self._random.uniform(0.1, 0.3)
        else:
            base = self._random.uniform(0.05, 0.2)

        # Apply cognitive state
        speed_mult = self._cognitive.get_state().get_speed_multiplier()

        # Error rate affects pause (pausing to correct)
        error_prob = self._cognitive.get_state().get_error_probability()
        if self._random.random() < error_prob:
            base += self._random.uniform(0.1, 0.3)  # Pause for potential correction

        return base * speed_mult

    def get_random_pause_duration(self) -> float:
        """
        Get duration of random pause (simulating looking away/distracted).

        Returns:
            Duration in seconds
        """
        # Mostly short pauses, occasionally long
        if self._random.random() < 0.9:
            return self._random.uniform(1, 5)
        else:
            return self._random.uniform(10, 30)


# =============================================================================
# NATURAL ERROR PATTERNS
# =============================================================================

class NaturalErrorGenerator:
    """
    Generate natural human-like errors.

    Humans make errors that:
    - Are contextually appropriate
    - Include realistic correction patterns
    - Vary in frequency based on fatigue/attention
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize error generator.

        Args:
            seed: Random seed
        """
        self._random = random.Random(seed)
        self._cognitive = CognitiveSimulator(seed)

    def should_make_typo(self) -> bool:
        """Determine if should make a typo."""
        error_rate = self._cognitive.get_state().get_error_probability()
        return self._random.random() < error_rate

    def get_typo_char(self, original: str) -> str:
        """
        Get a realistic typo based on keyboard proximity.

        Args:
            original: Original character

        Returns:
            Typo character
        """
        # Keyboard proximity map (simplified)
        proximity_map = {
            "a": "sqzw",
            "b": "vghn",
            "c": "xdfv",
            "d": "serfcx",
            "e": "wsdr",
            "f": "drtgvc",
            "g": "ftyhbv",
            "h": "gyujnb",
            "i": "ujko",
            "j": "huikmn",
            "k": "jiolm",
            "l": "kop",
            "m": "njk",
            "n": "bhjm",
            "o": "iklp",
            "p": "ol",
            "q": "wa",
            "r": "edft",
            "s": "awedxz",
            "t": "rfgy",
            "u": "yhji",
            "v": "cfgb",
            "w": "qase",
            "x": "zsdc",
            "y": "tghu",
            "z": "asx",
            "1": "2q",
            "2": "1qw3",
            "3": "2we4",
            "4": "3er5",
            "5": "4rt6",
            "6": "5ty7",
            "7": "6yu8",
            "8": "7ui9",
            "9": "8io0",
            "0": "9op-",
        }

        original_lower = original.lower()
        if original_lower in proximity_map:
            nearby = proximity_map[original_lower]
            return self._random.choice(nearby)
        else:
            # Random letter/number for unknown
            return self._random.choice("qwertyuiopasdfghjklzxcvbnm1234567890")

    def should_double_tap(self) -> bool:
        """Determine if should double-tap a key."""
        # Slightly more likely when tired
        prob = 0.02 + self._cognitive.get_state().fatigue_level * 0.03
        return self._random.random() < prob

    def should_skip_char(self) -> bool:
        """Determine if should skip a character."""
        # Rare, but more likely when distracted
        prob = 0.01 + self._cognitive.get_state().cognitive_load * 0.02
        return self._random.random() < prob

    def get_correction_delay(self) -> float:
        """Get delay for correction action."""
        # Delay before correcting depends on when error is noticed
        if self._random.random() < 0.5:
            # Notice quickly
            return self._random.uniform(0.1, 0.3)
        else:
            # Notice after typing more
            return self._random.uniform(0.3, 0.8)


# =============================================================================
# MOUSE MOVEMENT PATTERNS
# =============================================================================

class MLResistantMouseMovement:
    """
    Mouse movement patterns that evade ML classifiers.

    ML classifiers detect bots by:
    - Perfectly straight lines
    - Constant velocity
    - No micro-corrections
    - Perfect Bezier curves
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize mouse movement generator.

        Args:
            seed: Random seed
        """
        self._random = random.Random(seed)
        self._cognitive = CognitiveSimulator(seed)
        self._timing = MLResistantTiming(seed)

    def generate_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        num_points: int = 30,
    ) -> List[Tuple[float, float, float]]:
        """
        Generate natural mouse path.

        Args:
            start: Start coordinates
            end: End coordinates
            num_points: Number of path points

        Returns:
            List of (x, y, duration_ms) tuples
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx * dx + dy * dy)

        # Calculate duration
        duration = self._timing.get_mouse_move_duration(distance)
        duration_ms = int(duration * 1000)

        # Generate base path
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)

            # Add multiple layers of natural variation

            # 1. Bezier-like curve (not perfect)
            control_offset_x = self._random.uniform(-50, 50)
            control_offset_y = self._random.uniform(-50, 50)
            mid_x = start[0] + dx * 0.5 + control_offset_x
            mid_y = start[1] + dy * 0.5 + control_offset_y

            # Quadratic bezier with noise
            x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * mid_x + t ** 2 * end[0]
            y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * mid_y + t ** 2 * end[1]

            # 2. Add micro-jitter (hand tremor)
            jitter_x = self._random.uniform(-1.5, 1.5)
            jitter_y = self._random.uniform(-1.5, 1.5)

            # 3. Add waypoint deviation (eyes following cursor)
            waypoint_deviation = self._random.uniform(-10, 10)
            perp_x = -dy / distance if distance > 0 else 0
            perp_y = dx / distance if distance > 0 else 0

            x += jitter_x + waypoint_deviation * perp_x
            y += jitter_y + waypoint_deviation * perp_y

            # Variable timing per segment
            segment_duration = duration_ms // num_points
            timing_noise = self._random.uniform(0.7, 1.5)
            segment_duration = int(segment_duration * timing_noise)

            points.append((x, y, segment_duration))

        # Add overshoot and correct (common human behavior)
        if self._random.random() < 0.3:
            # Find last 3 points
            overshoot_idx = len(points) - 3
            overshoot_amount = self._random.uniform(3, 8)
            overshoot_dir = self._random.choice([-1, 1])

            for i in range(overshoot_idx, len(points)):
                px, py, d = points[i]
                points[i] = (px, py + overshoot_amount * overshoot_dir, d)
                overshoot_amount *= 0.7  # Recovering

        return points

    def should_hover(self) -> bool:
        """Determine if should hover before clicking."""
        # More likely to hover when tired
        hover_prob = 0.1 + self._cognitive.get_state().fatigue_level * 0.2
        return self._random.random() < hover_prob

    def get_hover_duration(self) -> float:
        """Get hover duration."""
        return self._random.uniform(0.1, 0.5)


# =============================================================================
# SCROLL PATTERNS
# =============================================================================

class MLResistantScroll:
    """
    Scroll patterns that evade ML classifiers.

    ML classifiers detect bots by:
    - Perfectly smooth scrolls
    - Constant scroll amount
    - No direction changes
    - Perfect timing
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize scroll pattern generator.

        Args:
            seed: Random seed
        """
        self._random = random.Random(seed)
        self._cognitive = CognitiveSimulator(seed)

    def generate_scroll_sequence(
        self,
        total_distance: int,
        direction: str = "down",
    ) -> List[Tuple[int, float]]:
        """
        Generate natural scroll sequence.

        Args:
            total_distance: Total pixels to scroll
            direction: Scroll direction

        Returns:
            List of (delta, delay) tuples
        """
        scrolls = []

        # Base scroll amount
        base_scroll = self._random.randint(80, 150)

        # Number of scrolls
        num_scrolls = max(1, total_distance // base_scroll)

        remaining = total_distance
        for _ in range(num_scrolls):
            # Vary scroll amount
            scroll_variation = self._random.uniform(0.6, 1.4)
            scroll_amount = int(base_scroll * scroll_variation)
            scroll_amount = min(scroll_amount, remaining)

            if direction == "up":
                scroll_amount = -abs(scroll_amount)
            else:
                scroll_amount = abs(scroll_amount)

            # Delay between scrolls
            # Longer when tired, shorter when engaged
            fatigue = self._cognitive.get_state().fatigue_level
            base_delay = self._random.uniform(0.05, 0.2)
            delay = base_delay * (1 + fatigue * 0.5)

            # Occasional longer pause (reading)
            if self._random.random() < 0.2:
                delay += self._random.uniform(0.5, 2.0)

            # Occasional small scroll back
            if self._random.random() < 0.1:
                back_scroll = -self._random.randint(10, 30)
                scrolls.append((back_scroll, delay * 0.5))
                delay += 0.1

            scrolls.append((scroll_amount, delay))
            remaining -= abs(scroll_amount)

        return scrolls


# =============================================================================
# SESSION PATTERNS
# =============================================================================

class SessionPatternSimulator:
    """
    Simulate session-level human patterns.

    This includes:
    - Initial hesitation
    - Learning/adaptation
    - Fatigue over time
    - Natural breaks
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize session simulator.

        Args:
            seed: Random seed
        """
        self._random = random.Random(seed)
        self._start_time = time.time()
        self._action_count = 0
        self._total_breaks = 0

    def get_initial_delay(self) -> float:
        """
        Get initial delay when starting session.

        Returns:
            Seconds to wait
        """
        # Humans often hesitate before starting
        return self._random.uniform(1.0, 4.0)

    def should_take_break(self) -> bool:
        """
        Determine if should take a break.

        Returns:
            True if taking break
        """
        session_duration = time.time() - self._start_time
        minutes_elapsed = session_duration / 60

        # More likely to break as time goes on
        break_prob = 0.01 * minutes_elapsed

        # Max one break per 5 minutes
        if self._total_breaks > 0 and minutes_elapsed < self._total_breaks * 5:
            break_prob = 0

        return self._random.random() < break_prob

    def get_break_duration(self) -> float:
        """Get break duration."""
        # Usually short breaks, occasionally longer
        if self._random.random() < 0.7:
            return self._random.uniform(30, 120)  # 30s - 2min
        else:
            return self._random.uniform(180, 600)  # 3-10 min (bathroom, etc.)

    def get_speed_adjustment(self) -> float:
        """
        Get speed adjustment based on session progress.

        Returns:
            Multiplier (0.5-1.5)
        """
        session_duration = time.time() - self._start_time
        minutes_elapsed = session_duration / 60

        # Speed up initially (getting comfortable)
        if minutes_elapsed < 5:
            return self._random.uniform(0.8, 1.2)

        # Slow down over time (fatigue)
        fatigue_factor = min(0.5, minutes_elapsed * 0.02)
        base_speed = self._random.uniform(0.6, 0.9)

        return base_speed * (1 - fatigue_factor)


# =============================================================================
# COMPLETE ML-RESISTANT BEHAVIORAL SYSTEM
# =============================================================================

class MLResistantBehavioralSystem:
    """
    Complete ML-resistant behavioral simulation system.

    This integrates all ML-resistance components:
    - Cognitive simulation
    - Natural timing
    - Error patterns
    - Mouse movements
    - Scroll patterns
    - Session patterns
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize ML-resistant behavioral system.

        Args:
            seed: Random seed for reproducibility
        """
        self._random = random.Random(seed)
        self._cognitive = CognitiveSimulator(seed)
        self._timing = MLResistantTiming(seed)
        self._errors = NaturalErrorGenerator(seed)
        self._mouse = MLResistantMouseMovement(seed)
        self._scroll = MLResistantScroll(seed)
        self._session = SessionPatternSimulator(seed)

        # Share cognitive state across components
        self._errors._cognitive = self._cognitive
        self._mouse._cognitive = self._cognitive
        self._mouse._timing = self._timing

    # Expose sub-components
    @property
    def cognitive(self) -> CognitiveSimulator:
        """Get cognitive simulator."""
        return self._cognitive

    @property
    def timing(self) -> MLResistantTiming:
        """Get timing generator."""
        return self._timing

    @property
    def errors(self) -> NaturalErrorGenerator:
        """Get error generator."""
        return self._errors

    @property
    def mouse(self) -> MLResistantMouseMovement:
        """Get mouse movement generator."""
        return self._mouse

    @property
    def scroll(self) -> MLResistantScroll:
        """Get scroll generator."""
        return self._scroll

    @property
    def session(self) -> SessionPatternSimulator:
        """Get session simulator."""
        return self._session

    # Convenience methods
    async def think_before_action(self) -> float:
        """
        Simulate thinking before an action.

        Returns:
            Delay in seconds
        """
        think_time = self._cognitive.simulate_think_time()
        await asyncio.sleep(think_time)
        return think_time

    def should_spoof_human(self) -> bool:
        """Determine if should simulate looking away."""
        return self._cognitive.should_look_away()

    def get_look_away_time(self) -> float:
        """Get time looking away."""
        return self._cognitive.get_look_away_duration()


# Global instance
_ml_behavior_system: Optional[MLResistantBehavioralSystem] = None


def get_ml_behavior_system(seed: Optional[int] = None) -> MLResistantBehavioralSystem:
    """
    Get or create global ML-resistant behavioral system.

    Args:
        seed: Random seed

    Returns:
        MLResistantBehavioralSystem instance
    """
    global _ml_behavior_system
    if _ml_behavior_system is None:
        _ml_behavior_system = MLResistantBehavioralSystem(seed)
    return _ml_behavior_system
