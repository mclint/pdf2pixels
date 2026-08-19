"""Public conversion API."""

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Literal

from .models import PageImage

OutputFormat = Literal["png", "jpeg"]
PDFSource = str | Path | bytes


def convert(
    source: PDFSource,
    *,
    backend: str = "auto",
    dpi: int = 150,
    pages: Iterable[int] | None = None,
    format: OutputFormat = "png",
) -> Iterator[PageImage]:
    """Stream rendered pages from a PDF.

    Rendering backend implementations will be added in the next stage.
    """
    del source, backend, dpi, pages, format
    raise NotImplementedError("PDF rendering backends are not implemented yet")

