from __future__ import annotations


def parse_callback(data: str) -> tuple[str, ...]:
    """Split callback data into parts."""
    return tuple(data.split(":"))
