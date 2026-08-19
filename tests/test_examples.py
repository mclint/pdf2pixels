from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdf2pixels import convert
from pdf2pixels.backends.pdfium import PdfiumRenderer
from pdf2pixels.backends.poppler import PopplerRenderer

EXAMPLES = Path("examples")


def test_sample_pdf_renders_both_distinct_pages() -> None:
    if PdfiumRenderer.create() is None and PopplerRenderer.create() is None:
        pytest.skip("no rendering backend is installed")

    pages = list(convert(EXAMPLES / "sample.pdf", dpi=72))

    assert [page.page for page in pages] == [1, 2]
    assert [(page.width, page.height) for page in pages] == [
        (612, 792),
        (792, 612),
    ]
    assert all(page.data for page in pages)


def test_quickstart_notebook_is_valid_and_has_no_stored_outputs() -> None:
    notebook = json.loads((EXAMPLES / "quickstart.ipynb").read_text())
    code_cells = [
        cell for cell in notebook["cells"] if cell["cell_type"] == "code"
    ]

    assert notebook["nbformat"] == 4
    assert code_cells
    assert all(cell["execution_count"] is None for cell in code_cells)
    assert all(cell["outputs"] == [] for cell in code_cells)
