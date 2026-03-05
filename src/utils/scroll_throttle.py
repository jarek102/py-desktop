"""
Utility for handling high-resolution continuous scroll input.

GTK's EventControllerScroll delivers fractional dy/dx values from hi-res
devices. A single deliberate gesture produces many callbacks with small values
(e.g. 0.08, 0.1) before the finger lifts. ScrollThrottle accumulates these and
only reports a step when the total crosses a whole-unit threshold. Discrete
wheel mice produce clean ±1.0 ticks which pass straight through as one step.
"""


class ScrollThrottle:
    """
    Accumulates fractional scroll deltas and fires only on whole-unit crossings.

    Args:
        threshold: Accumulated delta required to trigger one step. Default 1.0
                   matches a standard mouse wheel click. Use a lower value
                   (e.g. 0.5) for finer controls like volume.
    """

    def __init__(self, threshold: float = 1.0) -> None:
        if threshold <= 0:
            raise ValueError(f"threshold must be positive, got {threshold}")
        self._threshold = threshold
        self._accumulator: float = 0.0

    def feed(self, delta: float) -> int:
        """
        Feed one raw scroll delta value.

        Returns the number of whole steps crossed (positive = down/forward,
        negative = up/backward). Returns 0 if threshold not yet reached.
        May return values with |result| > 1 for fast discrete wheels.
        The fractional remainder is retained across calls.
        """
        self._accumulator += delta
        epsilon = 1e-9
        if self._accumulator >= 0:
            steps = int((self._accumulator + epsilon) / self._threshold)
        else:
            steps = -int(((-self._accumulator) + epsilon) / self._threshold)
        if steps != 0:
            self._accumulator -= steps * self._threshold
        return steps

    def reset(self) -> None:
        """
        Discard accumulated partial delta. Call when scroll context changes
        (e.g. workspace list rebuilds) to avoid phantom steps.
        """
        self._accumulator = 0.0
