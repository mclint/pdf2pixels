from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import pdf2pixels.backends.poppler as poppler_module
from pdf2pixels import PageImage
from pdf2pixels.backends.pdfium import PdfiumRenderer
from pdf2pixels.backends.poppler import PopplerRenderer


class FakeBitmap:
    def __init__(self) -> None:
        self.closed = False

    def to_pil(self) -> FakeImage:
        return FakeImage()

    def close(self) -> None:
        self.closed = True


class FakeImage:
    size = (10, 20)

    def convert(self, mode: str) -> FakeImage:
        del mode
        return self

    def save(self, output: Any, **options: object) -> None:
        del options
        output.write(b"image")

    def close(self) -> None:
        pass


class FakePage:
    def __init__(self) -> None:
        self.bitmap = FakeBitmap()
        self.closed = False

    def render(self, **options: object) -> FakeBitmap:
        del options
        return self.bitmap

    def close(self) -> None:
        self.closed = True


class FakeDocument:
    def __init__(self) -> None:
        self.pages: list[FakePage] = []
        self.closed = False

    def __len__(self) -> int:
        return 2

    def __getitem__(self, index: int) -> FakePage:
        del index
        page = FakePage()
        self.pages.append(page)
        return page

    def close(self) -> None:
        self.closed = True


def test_pdfium_closes_resources_when_iterator_is_closed_early() -> None:
    document = FakeDocument()
    module = SimpleNamespace(PdfDocument=lambda source: document)
    renderer = PdfiumRenderer(module)  # type: ignore[arg-type]

    iterator = renderer.convert(b"pdf", dpi=72, pages=None, format="png")
    next(iterator)
    iterator.close()

    assert document.closed
    assert document.pages[0].closed
    assert document.pages[0].bitmap.closed


def test_pdfium_closes_resources_when_iterator_is_exhausted() -> None:
    document = FakeDocument()
    module = SimpleNamespace(PdfDocument=lambda source: document)
    renderer = PdfiumRenderer(module)  # type: ignore[arg-type]

    pages = list(renderer.convert(b"pdf", dpi=72, pages=None, format="png"))

    assert [page.page for page in pages] == [1, 2]
    assert document.closed
    assert len(document.pages) == 2
    assert all(page.closed for page in document.pages)
    assert all(page.bitmap.closed for page in document.pages)


def test_poppler_cleans_temporary_input_when_closed_early(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temporary_path = tmp_path / "poppler-work"
    exited = False

    class RecordingTemporaryDirectory:
        def __init__(self, **options: object) -> None:
            del options

        def __enter__(self) -> str:
            temporary_path.mkdir()
            return str(temporary_path)

        def __exit__(self, *exception: Any) -> None:
            nonlocal exited
            del exception
            exited = True
            shutil.rmtree(temporary_path)

    renderer = PopplerRenderer("pdftocairo")

    def render_page(*arguments: object, **options: object) -> PageImage:
        del arguments, options
        return PageImage(1, b"image", "png", 10, 20)

    monkeypatch.setattr(
        poppler_module,
        "TemporaryDirectory",
        RecordingTemporaryDirectory,
    )
    monkeypatch.setattr(renderer, "_render_page", render_page)

    iterator = renderer.convert(b"pdf", dpi=72, pages=None, format="png")
    next(iterator)
    assert temporary_path.exists()
    iterator.close()

    assert exited
    assert not temporary_path.exists()


def test_poppler_cleans_temporary_input_when_iterator_is_exhausted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    temporary_path = tmp_path / "poppler-work"
    exited = False

    class RecordingTemporaryDirectory:
        def __init__(self, **options: object) -> None:
            del options

        def __enter__(self) -> str:
            temporary_path.mkdir()
            return str(temporary_path)

        def __exit__(self, *exception: Any) -> None:
            nonlocal exited
            del exception
            exited = True
            shutil.rmtree(temporary_path)

    renderer = PopplerRenderer("pdftocairo")

    def render_page(*arguments: object, **options: object) -> PageImage:
        del arguments, options
        assert temporary_path.exists()
        return PageImage(1, b"image", "png", 10, 20)

    monkeypatch.setattr(
        poppler_module,
        "TemporaryDirectory",
        RecordingTemporaryDirectory,
    )
    monkeypatch.setattr(renderer, "_render_page", render_page)

    pages = list(
        renderer.convert(b"pdf", dpi=72, pages=[1], format="png")
    )

    assert [page.page for page in pages] == [1]
    assert exited
    assert not temporary_path.exists()
