import pdf2pixels


def test_public_api_exports_convert_and_page_image() -> None:
    assert pdf2pixels.__all__ == ["PageImage", "convert"]

