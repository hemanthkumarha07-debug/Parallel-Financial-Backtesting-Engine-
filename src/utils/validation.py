"""
General-purpose validation utilities.
"""
from typing import Any, List


def validate_positive(value: float, name: str) -> None:
    """Raise ValueError if value is not positive."""
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_range(value: float, low: float, high: float, name: str) -> None:
    """Raise ValueError if value is outside [low, high]."""
    if not (low <= value <= high):
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")


def validate_less_than(a: float, b: float, name_a: str, name_b: str) -> None:
    """Raise ValueError if a >= b."""
    if a >= b:
        raise ValueError(f"{name_a} ({a}) must be less than {name_b} ({b})")


def validate_integer_positive(value: int, name: str) -> None:
    """Raise ValueError if value is not a positive integer."""
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value}")


def validate_in_list(value: Any, allowed: List[Any], name: str) -> None:
    """Raise ValueError if value is not in the allowed list."""
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}, got {value}")
