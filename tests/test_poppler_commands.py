from __future__ import annotations

from pathlib import Path
from shutil import which

import pytest

from pdf2pixels.backends.poppler import PopplerRenderer

POPPLER_COMMANDS = [
    command
    for name in ("pdftocairo", "pdftoppm")
    if (command := which(name)) is not None
]


@pytest.mark.parametrize("command", POPPLER_COMMANDS)
def test_installed_poppler_commands_satisfy_basic_contract(
    command: str, multipage_pdf: Path
) -> None:
    renderer = PopplerRenderer(command)

    pages = list(
        renderer.convert(
            multipage_pdf,
            dpi=72,
            pages=[2, 1],
            format="jpeg",
        )
    )

    assert [page.page for page in pages] == [2, 1]
    assert [(page.width, page.height) for page in pages] == [
        (792, 612),
        (612, 792),
    ]
    assert all(page.data.startswith(b"\xff\xd8") for page in pages)
