# pdf2pixels

`pdf2pixels` streams PDF pages as PNG or JPEG images through interchangeable
PDFium and Poppler rendering backends.

## Installation

The base package has no Python rendering-engine dependency:

```shell
python -m pip install pdf2pixels
```

For the preferred PDFium backend, install the optional extra:

```shell
python -m pip install "pdf2pixels[pdfium]"
```

Alternatively, install Poppler with your operating system's package manager.
`pdf2pixels` uses `pdftocairo` when available and otherwise uses `pdftoppm`;
it does not download or distribute Poppler binaries.

## Usage

Omitting `pages` renders every page in document order:

```python
from pdf2pixels import convert

for page in convert("document.pdf"):
    with open(f"page-{page.page}.{page.format}", "wb") as output:
        output.write(page.data)
```

Each `PageImage` contains the 1-based page number, encoded image bytes, output
format, width, and height. Conversion is lazy: the document is opened and the
first page is rendered when the iterator is consumed. Resources are released
when the iterator is exhausted or closed.

Paths and in-memory PDF bytes are supported:

```python
first_page = next(convert(pdf_bytes, pages=[1], format="jpeg", dpi=300))
selected = list(convert("document.pdf", pages=[3, 1, 3]))
```

For an interactive walkthrough, open the
[quickstart notebook](https://github.com/mclint/pdf2pixels/blob/main/examples/quickstart.ipynb),
which renders and displays the included
[sample PDF](https://github.com/mclint/pdf2pixels/blob/main/examples/sample.pdf).
Install its dependencies with
`python -m pip install -e ".[pdfium,examples]"`.

The options are:

- `backend`: `"auto"` (PDFium, then Poppler), `"pdfium"`, or `"poppler"`.
- `dpi`: a positive integer; the default is 150.
- `pages`: positive, 1-based page numbers. `None` renders all pages, and an
  empty iterable renders no pages. Explicit order and duplicates are preserved.
- `format`: `"png"` or `"jpeg"`. JPEG output uses quality 85.

Invalid arguments, malformed data, encrypted PDFs, and invalid page selections
raise `ValueError`. Missing paths raise `FileNotFoundError`. Missing renderers
and environmental rendering failures raise `RuntimeError`. Opening and render
errors can occur while iterating.

### Renderer versions

PDFium support is tested from `pypdfium2` 5.0 through the latest compatible
release, without an upper bound. Poppler support is based on command capability
rather than a version number and uses the installation provided by your system.
An informed user can try an older, unsupported PDFium release with
`python -m pip install Pillow pypdfium2==VERSION` followed by
`python -m pip install --no-deps pdf2pixels`. Older combinations are outside
the tested support range and may contain unpatched security issues; selecting
and maintaining renderer versions is the user's responsibility.

## Project boundary

Version 0.1 is a rendering library only: it does not fetch URLs, accept PDF
passwords, provide a CLI or renderer plugin API, or perform downstream PDF
processing.

## Development

Create the development environment from the repository root:

```shell
conda env create --file environment.yml
conda activate pdf2pixels-dev
```

The environment installs the project editable with the PDFium, development,
and example extras. Build distributions with `python -m build`, or clean
generated build artifacts with `python -m hatchling build --clean-only`.

## License

`pdf2pixels` is licensed under Apache-2.0. PDFium, `pypdfium2`, Pillow, Poppler,
and their dependencies retain their own licenses and are not relicensed by this
project.
