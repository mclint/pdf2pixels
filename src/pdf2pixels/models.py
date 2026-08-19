"""Public result models."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class PageImage:
    """One rendered PDF page."""

    page: int
    data: bytes
    format: Literal["png", "jpeg"]
    width: int
    height: int

