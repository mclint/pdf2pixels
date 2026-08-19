from __future__ import annotations

import base64
from pathlib import Path

import pytest


@pytest.fixture
def multipage_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "multipage.pdf"
    path.write_bytes(_make_multipage_pdf())
    return path


@pytest.fixture
def encrypted_pdf(tmp_path: Path) -> Path:
    encoded = Path("tests/fixtures/encrypted.pdf.b64").read_text().strip()
    path = tmp_path / "encrypted.pdf"
    path.write_bytes(base64.b64decode(encoded))
    return path


def _make_multipage_pdf() -> bytes:
    page_one = b"q 0.85 0.15 0.15 rg 0 0 612 792 re f Q\n"
    page_two = b"q 0.15 0.25 0.85 rg 0 0 792 612 re f Q\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 5 0 R] /Count 2 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << >> /Contents 4 0 R >>"
        ),
        _stream(page_one),
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 792 612] "
            b"/Resources << >> /Contents 6 0 R >>"
        ),
        _stream(page_two),
    ]

    document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode())
        document.extend(body)
        document.extend(b"\nendobj\n")

    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode())
    document.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(document)


def _stream(data: bytes) -> bytes:
    return (
        f"<< /Length {len(data)} >>\nstream\n".encode()
        + data
        + b"endstream"
    )
