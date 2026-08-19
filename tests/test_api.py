from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Literal

import pytest

import pdf2pixels.api as api
from pdf2pixels import PageImage, convert


class StubRenderer:
    def convert(
        self,
        source: str | Path | bytes,
        *,
        dpi: int,
        pages: Iterable[int] | None,
        format: Literal["png", "jpeg"],
    ) -> Iterator[PageImage]:
        del source, dpi
        selected_pages = (1, 2) if pages is None else pages
        for page in selected_pages:
            yield PageImage(page, b"image", format, 10, 20)


@pytest.mark.parametrize(
    "keyword_arguments",
    [
        {"backend": "PDFium"},
        {"backend": "unknown"},
        {"backend": None},
        {"backend": []},
        {"dpi": 0},
        {"dpi": -1},
        {"dpi": True},
        {"dpi": 72.5},
        {"pages": [0]},
        {"pages": [-1]},
        {"pages": [True]},
        {"pages": ["1"]},
        {"pages": "1"},
        {"format": "jpg"},
        {"format": "PNG"},
        {"format": None},
        {"format": []},
    ],
)
def test_invalid_arguments_raise_at_call_time(
    multipage_pdf: Path, keyword_arguments: dict[str, object]
) -> None:
    with pytest.raises(ValueError):
        convert(multipage_pdf, **keyword_arguments)  # type: ignore[arg-type]


def test_invalid_source_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="filesystem path or PDF bytes"):
        convert(123)  # type: ignore[arg-type]


def test_missing_source_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        convert(tmp_path / "missing.pdf")


def test_page_iterable_is_validated_and_preserved_at_call_time(
    multipage_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    consumed = False

    def selected_pages() -> Iterator[int]:
        nonlocal consumed
        consumed = True
        yield 2
        yield 1
        yield 2

    monkeypatch.setattr(api, "get_renderer", lambda backend: StubRenderer())
    iterator = convert(multipage_pdf, pages=selected_pages())

    assert consumed
    assert [page.page for page in iterator] == [2, 1, 2]


def test_backend_discovery_and_rendering_are_lazy(
    multipage_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    discoveries: list[str] = []

    def discover(backend: str) -> StubRenderer:
        discoveries.append(backend)
        return StubRenderer()

    monkeypatch.setattr(api, "get_renderer", discover)
    iterator = convert(multipage_pdf)

    assert discoveries == []
    assert next(iterator).page == 1
    assert discoveries == ["auto"]
    iterator.close()  # type: ignore[attr-defined]


def test_empty_page_selection_does_not_discover_a_backend(
    multipage_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_discovery(backend: str) -> StubRenderer:
        raise AssertionError(f"unexpected backend discovery: {backend}")

    monkeypatch.setattr(api, "get_renderer", fail_discovery)

    assert list(convert(multipage_pdf, pages=[])) == []
