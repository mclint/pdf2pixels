"""Internal rendering backend contract."""

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Literal, Protocol

from pdf2pixels.models import PageImage


class Renderer(Protocol):
    """Contract implemented by PDF rendering backends."""

    def convert(
        self,
        source: str | Path | bytes,
        *,
        dpi: int,
        pages: Iterable[int] | None,
        format: Literal["png", "jpeg"],
    ) -> Iterator[PageImage]:
        """Yield rendered pages and release resources when closed."""
        ...

