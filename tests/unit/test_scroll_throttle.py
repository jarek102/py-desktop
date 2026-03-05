"""Unit tests for utils.scroll_throttle.ScrollThrottle."""

import pytest
from utils.scroll_throttle import ScrollThrottle


class TestDiscreteWheel:
    """Discrete mouse wheel: clean ±1.0 ticks must pass through as single steps."""

    def test_single_forward_tick(self):
        assert ScrollThrottle().feed(1.0) == 1

    def test_single_backward_tick(self):
        assert ScrollThrottle().feed(-1.0) == -1

    def test_multiple_forward_ticks(self):
        assert ScrollThrottle().feed(3.0) == 3

    def test_zero_returns_zero(self):
        assert ScrollThrottle().feed(0.0) == 0


class TestHighResAccumulation:
    """Hi-res input: many small deltas must not trigger until threshold crossed."""

    def test_nine_small_deltas_do_not_trigger(self):
        throttle = ScrollThrottle(threshold=1.0)
        for _ in range(9):
            assert throttle.feed(0.1) == 0

    def test_tenth_delta_triggers_exactly_once(self):
        throttle = ScrollThrottle(threshold=1.0)
        results = [throttle.feed(0.1) for _ in range(10)]
        assert sum(results) == 1
        assert results.count(0) == 9

    def test_remainder_carries_over(self):
        throttle = ScrollThrottle(threshold=1.0)
        assert throttle.feed(1.1) == 1
        # 0.1 carried — only needs 0.9 more for next step
        assert throttle.feed(0.9) == 1

    def test_negative_accumulates_correctly(self):
        throttle = ScrollThrottle(threshold=1.0)
        results = [throttle.feed(-0.1) for _ in range(10)]
        assert sum(results) == -1

    def test_direction_reversal_cancels_momentum(self):
        throttle = ScrollThrottle(threshold=1.0)
        throttle.feed(0.6)
        throttle.feed(-0.6)
        # Net delta is ~0, nothing should have fired
        assert throttle.feed(0.0) == 0


class TestCustomThreshold:
    """Lower threshold for sensitive controls like volume."""

    def test_half_threshold_each_half_tick_fires(self):
        throttle = ScrollThrottle(threshold=0.5)
        assert throttle.feed(0.5) == 1
        assert throttle.feed(0.5) == 1

    def test_discrete_tick_with_half_threshold_gives_two_steps(self):
        throttle = ScrollThrottle(threshold=0.5)
        assert throttle.feed(1.0) == 2


class TestReset:
    def test_reset_discards_partial_accumulation(self):
        throttle = ScrollThrottle(threshold=1.0)
        throttle.feed(0.7)
        throttle.reset()
        assert throttle.feed(0.7) == 0
        assert throttle.feed(0.3) == 1


class TestInvalidConstruction:
    def test_zero_threshold_raises(self):
        with pytest.raises(ValueError):
            ScrollThrottle(threshold=0.0)

    def test_negative_threshold_raises(self):
        with pytest.raises(ValueError):
            ScrollThrottle(threshold=-1.0)
