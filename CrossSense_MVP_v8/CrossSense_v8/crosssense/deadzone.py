from __future__ import annotations

from dataclasses import dataclass


def clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


@dataclass
class CrossDeadzoneProfile:
    inner_deadzone_percent: float = 6.0
    outer_saturation_percent: float = 83.0
    forward_boost_percent: float = 0.0

    @property
    def inner(self) -> float:
        return clamp(self.inner_deadzone_percent / 100.0, 0.0, 0.95)

    @property
    def outer(self) -> float:
        return clamp(self.outer_saturation_percent / 100.0, 0.01, 1.0)

    def map_axis(self, value: float) -> float:
        value = clamp(value)
        sign = -1.0 if value < 0 else 1.0
        amount = abs(value)
        if amount <= self.inner:
            return 0.0
        denom = max(0.0001, self.outer - self.inner)
        mapped = (amount - self.inner) / denom
        return clamp(mapped * sign)

    def map_left_stick(self, x: float, y: float) -> tuple[float, float]:
        # Cross / axial deadzone: each axis is treated independently.
        mapped_x = self.map_axis(x)
        mapped_y = self.map_axis(y)
        # Optional tiny forward/up boost. DualSense up is negative Y through SDL on Windows.
        boost = clamp(self.forward_boost_percent / 100.0, 0.0, 0.15)
        if mapped_y < 0.0 and boost > 0.0:
            mapped_y = clamp(mapped_y * (1.0 + boost))
        return mapped_x, mapped_y
