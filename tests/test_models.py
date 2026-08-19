from pdf2pixels import PageImage


def test_page_image_contains_rendered_page_metadata() -> None:
    page = PageImage(
        page=1,
        data=b"image",
        format="png",
        width=1275,
        height=1650,
    )

    assert page.page == 1
    assert page.data == b"image"
    assert page.format == "png"
    assert page.width == 1275
    assert page.height == 1650

