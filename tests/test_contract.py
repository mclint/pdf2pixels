from __future__ import annotations

from pathlib import Path

import pytest

from pdf2pixels import convert
from pdf2pixels.backends.pdfium import PdfiumRenderer
from pdf2pixels.backends.poppler import PopplerRenderer


def _available_backends() -> list[str]:
    available: list[str] = []
    if PdfiumRenderer.create() is not None:
        available.append("pdfium")
    if PopplerRenderer.create() is not None:
        available.append("poppler")
    return available


BACKENDS = _available_backends()


@pytest.mark.parametrize("backend", BACKENDS)
def test_default_conversion_streams_all_pages(
    backend: str, multipage_pdf: Path
) -> None:
    pages = list(convert(multipage_pdf, backend=backend))

    assert [page.page for page in pages] == [1, 2]
    _assert_dimensions_close(
        [(page.width, page.height) for page in pages],
        [(1275, 1650), (1650, 1275)],
    )
    assert all(page.format == "png" for page in pages)
    assert all(page.data.startswith(b"\x89PNG\r\n\x1a\n") for page in pages)


@pytest.mark.parametrize("backend", BACKENDS)
def test_explicit_page_order_and_duplicates_are_preserved(
    backend: str, multipage_pdf: Path
) -> None:
    pages = list(convert(multipage_pdf, backend=backend, pages=[2, 1, 2]))

    assert [page.page for page in pages] == [2, 1, 2]
    _assert_dimensions_close(
        [(page.width, page.height) for page in pages],
        [(1650, 1275), (1275, 1650), (1650, 1275)],
    )


@pytest.mark.parametrize("backend", BACKENDS)
def test_dpi_changes_dimensions_proportionally(
    backend: str, multipage_pdf: Path
) -> None:
    page_72 = next(convert(multipage_pdf, backend=backend, dpi=72, pages=[1]))
    page_144 = next(convert(multipage_pdf, backend=backend, dpi=144, pages=[1]))

    assert (page_72.width, page_72.height) == (612, 792)
    assert (page_144.width, page_144.height) == (1224, 1584)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize(
    ("format", "signature"),
    [("png", b"\x89PNG\r\n\x1a\n"), ("jpeg", b"\xff\xd8")],
)
def test_output_formats(
    backend: str, format: str, signature: bytes, multipage_pdf: Path
) -> None:
    page = next(
        convert(
            multipage_pdf,
            backend=backend,
            pages=[1],
            format=format,  # type: ignore[arg-type]
        )
    )

    assert page.format == format
    assert page.data.startswith(signature)
    _assert_dimensions_close([(page.width, page.height)], [(1275, 1650)])


@pytest.mark.parametrize("backend", BACKENDS)
def test_path_and_byte_sources_work(backend: str, multipage_pdf: Path) -> None:
    path_page = next(convert(multipage_pdf, backend=backend, pages=[1]))
    byte_page = next(
        convert(multipage_pdf.read_bytes(), backend=backend, pages=[1])
    )

    assert (byte_page.page, byte_page.width, byte_page.height) == (
        path_page.page,
        path_page.width,
        path_page.height,
    )


@pytest.mark.parametrize("backend", BACKENDS)
def test_malformed_pdf_raises_value_error(backend: str) -> None:
    with pytest.raises(ValueError, match="valid PDF"):
        next(convert(b"not a PDF", backend=backend))


@pytest.mark.parametrize("backend", BACKENDS)
def test_encrypted_pdf_raises_value_error(
    backend: str, encrypted_pdf: Path
) -> None:
    with pytest.raises(ValueError, match="encrypted"):
        next(convert(encrypted_pdf, backend=backend))


@pytest.mark.parametrize("backend", BACKENDS)
def test_out_of_range_page_raises_value_error(
    backend: str, multipage_pdf: Path
) -> None:
    with pytest.raises(ValueError, match="outside"):
        next(convert(multipage_pdf, backend=backend, pages=[3]))


def _assert_dimensions_close(
    actual: list[tuple[int, int]], expected: list[tuple[int, int]]
) -> None:
    assert len(actual) == len(expected)
    assert all(
        abs(actual_width - expected_width) <= 1
        and abs(actual_height - expected_height) <= 1
        for (actual_width, actual_height), (expected_width, expected_height) in zip(
            actual, expected, strict=True
        )
    )
