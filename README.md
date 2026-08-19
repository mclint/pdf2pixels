# pdf2pixels

`pdf2pixels` is a small Python library focused on streaming PDF pages as PNG or JPEG images through interchangeable rendering backends.

The project is currently being implemented. Its planned API is:

```python
from pdf2pixels import convert

for page in convert("document.pdf", dpi=150):
    with open(f"page-{page.page}.{page.format}", "wb") as output:
        output.write(page.data)
```

See [plan.md](plan.md) for the v0.1 design.

## License

Apache-2.0. Optional rendering engines and system dependencies retain their own licenses.

