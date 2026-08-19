"""PDFium rendering backend."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from importlib import import_module
from io import BytesIO
from pathlib import Path
from threading import RLock
from types import ModuleType
from typing import Any, Literal

from pdf2pixels.models import PageImage

_PDFIUM_LOCK = RLock()
_FORMAT_ERROR = 3
_PASSWORD_ERROR = 4
_SECURITY_ERROR = 5


class PdfiumRenderer:
    """Render PDF pages through pypdfium2."""

    def __init__(self, pdfium: ModuleType) -> None:
        self._pdfium = pdfium

    @classmethod
    def create(cls) -> PdfiumRenderer | None:
        try:
            pdfium = import_module("pypdfium2")
            import_module("PIL.Image")
        except Exception:
            return None
        return cls(pdfium)

    def convert(
        self,
        source: str | Path | bytes,
        *,
        dpi: int,
        pages: Iterable[int] | None,
        format: Literal["png", "jpeg"],
    ) -> Iterator[PageImage]:
        document = self._open_document(source)
        try:
            with _PDFIUM_LOCK:
                page_count = len(document)
            selected_pages = range(1, page_count + 1) if pages is None else pages

            for page_number in selected_pages:
                if page_number > page_count:
                    raise ValueError(
                        f"page {page_number} is outside the document's "
                        f"1-{page_count} page range"
                    )
                yield self._render_page(document, page_number, dpi, format)
        finally:
            with _PDFIUM_LOCK:
                document.close()

    def _open_document(self, source: str | Path | bytes) -> Any:
        try:
            with _PDFIUM_LOCK:
                return self._pdfium.PdfDocument(source)
        except FileNotFoundError:
            raise
        except Exception as exc:
            _raise_load_error(exc)

    def _render_page(
        self,
        document: Any,
        page_number: int,
        dpi: int,
        format: Literal["png", "jpeg"],
    ) -> PageImage:
        page: Any | None = None
        bitmap: Any | None = None
        image: Any | None = None
        encoded_image: Any | None = None
        try:
            with _PDFIUM_LOCK:
                page = document[page_number - 1]
                bitmap = page.render(
                    scale=dpi / 72,
                    fill_color=(255, 255, 255, 255),
                )
                image = bitmap.to_pil()
                encoded_image = image.convert("RGB") if format == "jpeg" else image
                output = BytesIO()
                save_format = "JPEG" if format == "jpeg" else "PNG"
                save_options = {"quality": 85} if format == "jpeg" else {}
                encoded_image.save(output, format=save_format, **save_options)
                width, height = encoded_image.size
                data = output.getvalue()
        except Exception as exc:
            raise RuntimeError(
                f"PDFium failed to render page {page_number}"
            ) from exc
        finally:
            with _PDFIUM_LOCK:
                if encoded_image is not None and encoded_image is not image:
                    encoded_image.close()
                if image is not None:
                    image.close()
                if bitmap is not None:
                    bitmap.close()
                if page is not None:
                    page.close()

        return PageImage(
            page=page_number,
            data=data,
            format=format,
            width=width,
            height=height,
        )


def _raise_load_error(exc: Exception) -> None:
    error_code = getattr(exc, "err_code", None)
    if error_code in {_PASSWORD_ERROR, _SECURITY_ERROR}:
        raise ValueError("encrypted PDFs are not supported") from exc
    if error_code == _FORMAT_ERROR:
        raise ValueError("source does not contain valid PDF data") from exc
    raise RuntimeError("PDFium failed to open the PDF") from exc
