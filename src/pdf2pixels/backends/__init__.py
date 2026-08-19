"""Rendering backend selection."""

from .base import Renderer
from .pdfium import PdfiumRenderer
from .poppler import PopplerRenderer


def get_renderer(backend: str) -> Renderer:
    """Return the requested available renderer."""
    if backend in {"auto", "pdfium"}:
        pdfium_renderer = PdfiumRenderer.create()
        if pdfium_renderer is not None:
            return pdfium_renderer
        if backend == "pdfium":
            raise RuntimeError(
                "PDFium is unavailable. Install it with "
                "'pip install pdf2pixels[pdfium]'."
            )

    if backend in {"auto", "poppler"}:
        poppler_renderer = PopplerRenderer.create()
        if poppler_renderer is not None:
            return poppler_renderer
        if backend == "poppler":
            raise RuntimeError(
                "Poppler is unavailable. Install pdftocairo or pdftoppm "
                "using your system package manager."
            )

    raise RuntimeError(
        "No PDF rendering backend is available. Install the PDFium extra "
        "with 'pip install pdf2pixels[pdfium]' or install Poppler's "
        "pdftocairo/pdftoppm commands."
    )


__all__ = ["get_renderer"]
