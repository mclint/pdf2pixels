"""Public conversion API."""

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Literal, cast

from .backends import get_renderer
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

    Arguments are validated immediately. Opening and rendering the PDF is
    deferred until the returned iterator is consumed.
    """
    validated_source = _validate_source(source)
    validated_backend = _validate_backend(backend)
    validated_dpi = _validate_dpi(dpi)
    validated_pages = _validate_pages(pages)
    validated_format = _validate_format(format)

    return _convert(
        validated_source,
        backend=validated_backend,
        dpi=validated_dpi,
        pages=validated_pages,
        format=validated_format,
    )


def _convert(
    source: PDFSource,
    *,
    backend: str,
    dpi: int,
    pages: tuple[int, ...] | None,
    format: OutputFormat,
) -> Iterator[PageImage]:
    if pages == ():
        return

    renderer = get_renderer(backend)
    yield from renderer.convert(
        source,
        dpi=dpi,
        pages=pages,
        format=format,
    )


def _validate_source(source: PDFSource) -> PDFSource:
    if isinstance(source, bytes):
        return source
    if not isinstance(source, str | Path):
        raise ValueError("source must be a filesystem path or PDF bytes")

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError("source path must identify a file")
    return path


def _validate_backend(backend: str) -> str:
    if not isinstance(backend, str) or backend not in {
        "auto",
        "pdfium",
        "poppler",
    }:
        raise ValueError("backend must be 'auto', 'pdfium', or 'poppler'")
    return backend


def _validate_dpi(dpi: int) -> int:
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi <= 0:
        raise ValueError("dpi must be a positive integer")
    return dpi


def _validate_pages(pages: Iterable[int] | None) -> tuple[int, ...] | None:
    if pages is None:
        return None
    if isinstance(pages, str | bytes):
        raise ValueError("pages must be an iterable of positive integers")

    try:
        selected_pages = tuple(pages)
    except TypeError as exc:
        raise ValueError("pages must be an iterable of positive integers") from exc

    if any(
        isinstance(page, bool) or not isinstance(page, int) or page <= 0
        for page in selected_pages
    ):
        raise ValueError("page numbers must be positive integers")
    return selected_pages


def _validate_format(format: str) -> OutputFormat:
    if not isinstance(format, str) or format not in {"png", "jpeg"}:
        raise ValueError("format must be 'png' or 'jpeg'")
    return cast(OutputFormat, format)
