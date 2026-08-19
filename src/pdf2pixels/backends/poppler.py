"""Poppler rendering backend."""

from __future__ import annotations

import os
import shutil
import struct
import subprocess
from collections.abc import Iterable, Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pdf2pixels.models import PageImage

_REQUIRED_OPTIONS = ("-f", "-l", "-singlefile", "-r", "-png", "-jpeg")
_JPEG_SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


class PopplerRenderer:
    """Render PDF pages through a Poppler command-line tool."""

    def __init__(self, command: str) -> None:
        self._command = command

    @classmethod
    def create(cls) -> PopplerRenderer | None:
        for command_name in ("pdftocairo", "pdftoppm"):
            command = shutil.which(command_name)
            if command is not None and _supports_required_options(command):
                return cls(command)
        return None

    def convert(
        self,
        source: str | Path | bytes,
        *,
        dpi: int,
        pages: Iterable[int] | None,
        format: Literal["png", "jpeg"],
    ) -> Iterator[PageImage]:
        with TemporaryDirectory(prefix="pdf2pixels-") as temporary_directory:
            work_directory = Path(temporary_directory)
            input_path = _prepare_input(source, work_directory)
            output_prefix = work_directory / "page"

            if pages is None:
                page_number = 1
                while True:
                    page = self._render_page(
                        input_path,
                        output_prefix,
                        page_number,
                        dpi,
                        format,
                        allow_end=True,
                    )
                    if page is None:
                        return
                    yield page
                    page_number += 1
            else:
                for page_number in pages:
                    page = self._render_page(
                        input_path,
                        output_prefix,
                        page_number,
                        dpi,
                        format,
                        allow_end=False,
                    )
                    if page is None:  # pragma: no cover - guarded by allow_end
                        raise AssertionError("explicit pages cannot end implicitly")
                    yield page

    def _render_page(
        self,
        input_path: Path,
        output_prefix: Path,
        page_number: int,
        dpi: int,
        format: Literal["png", "jpeg"],
        *,
        allow_end: bool,
    ) -> PageImage | None:
        extension = "jpg" if format == "jpeg" else "png"
        output_path = output_prefix.with_suffix(f".{extension}")
        output_path.unlink(missing_ok=True)

        arguments = [
            self._command,
            f"-{format}",
            "-singlefile",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-r",
            str(dpi),
        ]
        if format == "jpeg":
            arguments.extend(("-jpegopt", "quality=85"))
        arguments.extend((str(input_path), str(output_prefix)))

        environment = os.environ.copy()
        environment["LC_ALL"] = "C"
        try:
            completed = subprocess.run(
                arguments,
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
        except OSError as exc:
            raise RuntimeError("Poppler could not be started") from exc

        if completed.returncode != 0:
            if _is_end_of_document(completed):
                if allow_end:
                    return None
                raise ValueError(
                    f"page {page_number} is outside the document's page range"
                )
            _raise_poppler_error(completed)

        try:
            data = output_path.read_bytes()
        except OSError as exc:
            raise RuntimeError(
                f"Poppler did not produce page {page_number}"
            ) from exc
        finally:
            output_path.unlink(missing_ok=True)

        width, height = _image_dimensions(data, format)
        return PageImage(
            page=page_number,
            data=data,
            format=format,
            width=width,
            height=height,
        )


def _supports_required_options(command: str) -> bool:
    try:
        completed = subprocess.run(
            [command, "-h"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    help_text = completed.stdout + completed.stderr
    return all(option in help_text for option in _REQUIRED_OPTIONS)


def _prepare_input(source: str | Path | bytes, work_directory: Path) -> Path:
    if not isinstance(source, bytes):
        return Path(source).absolute()

    input_path = work_directory / "input.pdf"
    try:
        input_path.write_bytes(source)
    except OSError as exc:
        raise RuntimeError("could not prepare PDF bytes for Poppler") from exc
    return input_path


def _is_end_of_document(completed: subprocess.CompletedProcess[str]) -> bool:
    return (
        completed.returncode == 99
        and "Wrong page range given" in completed.stderr
        and "first page" in completed.stderr
    )


def _raise_poppler_error(completed: subprocess.CompletedProcess[str]) -> None:
    message = completed.stderr.strip()
    lowered_message = message.lower()
    if "password" in lowered_message or "encrypted" in lowered_message:
        raise ValueError("encrypted PDFs are not supported")
    if completed.returncode == 1 and "couldn't open file" not in lowered_message:
        raise ValueError("source does not contain valid PDF data")
    detail = message or "unknown error"
    raise RuntimeError(f"Poppler failed to render the PDF: {detail}")


def _image_dimensions(
    data: bytes, format: Literal["png", "jpeg"]
) -> tuple[int, int]:
    try:
        if format == "png":
            if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError
            width, height = struct.unpack(">II", data[16:24])
        else:
            width, height = _jpeg_dimensions(data)
    except (ValueError, struct.error) as exc:
        raise RuntimeError(f"Poppler produced an invalid {format} image") from exc

    if width <= 0 or height <= 0:
        raise RuntimeError(f"Poppler produced an invalid {format} image")
    return width, height


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError

    position = 2
    while position < len(data):
        while position < len(data) and data[position] != 0xFF:
            position += 1
        while position < len(data) and data[position] == 0xFF:
            position += 1
        if position >= len(data):
            break

        marker = data[position]
        position += 1
        if marker in {0x01, *range(0xD0, 0xDA)}:
            continue
        if position + 2 > len(data):
            break
        segment_length = struct.unpack(">H", data[position : position + 2])[0]
        if segment_length < 2 or position + segment_length > len(data):
            break
        if marker in _JPEG_SOF_MARKERS:
            if segment_length < 7:
                break
            height, width = struct.unpack(
                ">HH", data[position + 3 : position + 7]
            )
            return width, height
        position += segment_length

    raise ValueError
