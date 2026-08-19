from __future__ import annotations

import pytest

import pdf2pixels.backends as backends


class RendererSentinel:
    pass


def test_auto_prefers_pdfium(monkeypatch: pytest.MonkeyPatch) -> None:
    pdfium = RendererSentinel()
    monkeypatch.setattr(backends.PdfiumRenderer, "create", lambda: pdfium)
    monkeypatch.setattr(
        backends.PopplerRenderer,
        "create",
        lambda: (_ for _ in ()).throw(AssertionError("Poppler was probed")),
    )

    assert backends.get_renderer("auto") is pdfium


def test_auto_falls_back_to_poppler(monkeypatch: pytest.MonkeyPatch) -> None:
    poppler = RendererSentinel()
    monkeypatch.setattr(backends.PdfiumRenderer, "create", lambda: None)
    monkeypatch.setattr(backends.PopplerRenderer, "create", lambda: poppler)

    assert backends.get_renderer("auto") is poppler


@pytest.mark.parametrize("backend", ["auto", "pdfium", "poppler"])
def test_unavailable_backend_has_installation_guidance(
    backend: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(backends.PdfiumRenderer, "create", lambda: None)
    monkeypatch.setattr(backends.PopplerRenderer, "create", lambda: None)

    with pytest.raises(RuntimeError, match="Install|install"):
        backends.get_renderer(backend)
