from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Mapping

import fitz
from PIL import Image, ImageFilter, ImageOps


PREVIEW_DPI = 120
OUTPUT_DPI = 200
MAX_IMAGE_PREVIEW_SIDE = 1800
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class PdfBlurError(Exception):
    """Base exception for user-facing blur failures."""


class EncryptedPdfError(PdfBlurError):
    """Raised when a PDF needs a password."""


@dataclass(frozen=True)
class PreviewPage:
    page: int
    label: str
    width: int
    height: int
    image_data: str


@dataclass(frozen=True)
class RegionBlurStats:
    pages: int
    regions: int


NormalizedRegion = Mapping[str, float | int]
Box = tuple[int, int, int, int]


def render_pdf_previews(input_path: str | Path, *, dpi: int = PREVIEW_DPI) -> list[PreviewPage]:
    """Render PDF pages to inline PNG previews for the browser editor."""
    _validate_dpi(dpi)
    document = _open_pdf(input_path)
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    previews: list[PreviewPage] = []

    try:
        for page_index, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_data = base64.b64encode(pixmap.tobytes("png")).decode("ascii")
            previews.append(
                PreviewPage(
                    page=page_index,
                    label=f"{page_index + 1}페이지",
                    width=pixmap.width,
                    height=pixmap.height,
                    image_data=f"data:image/png;base64,{image_data}",
                )
            )
        if not previews:
            raise PdfBlurError("PDF에 페이지가 없습니다.")
        return previews
    finally:
        document.close()


def render_image_preview(input_path: str | Path) -> list[PreviewPage]:
    """Create a browser preview for a raster image upload."""
    image = _open_image(input_path)
    try:
        preview = image.copy()
        preview.thumbnail((MAX_IMAGE_PREVIEW_SIDE, MAX_IMAGE_PREVIEW_SIDE), Image.Resampling.LANCZOS)
        image_data = base64.b64encode(_encode_png(preview.convert("RGBA"))).decode("ascii")
        return [
            PreviewPage(
                page=0,
                label="이미지",
                width=preview.width,
                height=preview.height,
                image_data=f"data:image/png;base64,{image_data}",
            )
        ]
    finally:
        image.close()


def blur_pdf_regions(
    input_path: str | Path,
    output_path: str | Path,
    *,
    regions: Iterable[NormalizedRegion],
    dpi: int = OUTPUT_DPI,
    blur_radius: int = 8,
) -> RegionBlurStats:
    """Blur user-selected normalized regions and rebuild the PDF as page images."""
    _validate_dpi(dpi)
    _validate_blur_radius(blur_radius)

    grouped_regions = _group_regions(regions)
    if not grouped_regions:
        raise PdfBlurError("블러 처리할 영역을 하나 이상 지정해 주세요.")

    input_path = Path(input_path)
    output_path = Path(output_path)
    source = _open_pdf(input_path)
    output = fitz.open()
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    applied_regions = 0

    try:
        page_count = source.page_count
        invalid_pages = [page for page in grouped_regions if page < 0 or page >= page_count]
        if invalid_pages:
            raise PdfBlurError("선택 영역에 존재하지 않는 페이지가 포함되어 있습니다.")

        for page_index, page in enumerate(source):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

            for region in grouped_regions.get(page_index, []):
                box = _normalized_region_to_box(region, image.size)
                if box is None:
                    continue
                _blur_box(image, box, blur_radius)
                applied_regions += 1

            pdf_page = output.new_page(width=page.rect.width, height=page.rect.height)
            pdf_page.insert_image(pdf_page.rect, stream=_encode_png(image))

        if applied_regions == 0:
            raise PdfBlurError("유효한 블러 영역이 없습니다. 영역을 다시 지정해 주세요.")

        _clear_metadata(output)
        output.save(output_path, garbage=4, deflate=True, clean=True)
        return RegionBlurStats(pages=source.page_count, regions=applied_regions)
    finally:
        output.close()
        source.close()


def blur_image_regions(
    input_path: str | Path,
    output_path: str | Path,
    *,
    regions: Iterable[NormalizedRegion],
    blur_radius: int = 8,
) -> RegionBlurStats:
    """Blur user-selected normalized regions in a raster image."""
    _validate_blur_radius(blur_radius)
    grouped_regions = _group_regions(regions)
    image_regions = grouped_regions.get(0, [])
    if not image_regions:
        raise PdfBlurError("블러 처리할 영역을 하나 이상 지정해 주세요.")

    image = _open_image(input_path)
    applied_regions = 0
    try:
        editable = image.convert("RGBA")
        for region in image_regions:
            box = _normalized_region_to_box(region, editable.size)
            if box is None:
                continue
            _blur_box(editable, box, blur_radius)
            applied_regions += 1

        if applied_regions == 0:
            raise PdfBlurError("유효한 블러 영역이 없습니다. 영역을 다시 지정해 주세요.")

        _save_image(editable, output_path, Path(input_path).suffix.lower())
        return RegionBlurStats(pages=1, regions=applied_regions)
    finally:
        image.close()


def _open_pdf(input_path: str | Path) -> fitz.Document:
    try:
        document = fitz.open(Path(input_path))
    except Exception as exc:
        raise PdfBlurError("PDF 파일을 열 수 없습니다.") from exc
    if document.is_encrypted or document.needs_pass:
        document.close()
        raise EncryptedPdfError("암호화된 PDF는 처리할 수 없습니다.")
    return document


def _open_image(input_path: str | Path) -> Image.Image:
    path = Path(input_path)
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise PdfBlurError("지원하지 않는 이미지 형식입니다.")
    try:
        image = Image.open(path)
        image.load()
        return ImageOps.exif_transpose(image)
    except Exception as exc:
        raise PdfBlurError("이미지 파일을 열 수 없습니다.") from exc


def _save_image(image: Image.Image, output_path: str | Path, source_suffix: str) -> None:
    suffix = source_suffix.lower()
    output = Path(output_path)
    if suffix in {".jpg", ".jpeg"}:
        image.convert("RGB").save(output, format="JPEG", quality=95, optimize=True)
        return
    if suffix == ".webp":
        image.save(output, format="WEBP", quality=95, method=6)
        return
    image.save(output, format="PNG", optimize=True)


def _validate_dpi(dpi: int) -> None:
    if dpi < 72 or dpi > 600:
        raise PdfBlurError("DPI 값은 72에서 600 사이여야 합니다.")


def _validate_blur_radius(blur_radius: int) -> None:
    if blur_radius < 1 or blur_radius > 40:
        raise PdfBlurError("블러 강도는 1에서 40 사이여야 합니다.")


def _group_regions(regions: Iterable[NormalizedRegion]) -> dict[int, list[NormalizedRegion]]:
    grouped: dict[int, list[NormalizedRegion]] = {}
    for region in regions:
        try:
            page = int(region["page"])
            x = float(region["x"])
            y = float(region["y"])
            width = float(region["width"])
            height = float(region["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PdfBlurError("영역 데이터 형식이 올바르지 않습니다.") from exc
        grouped.setdefault(page, []).append(
            {
                "page": page,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }
        )
    return grouped


def _normalized_region_to_box(region: NormalizedRegion, image_size: tuple[int, int]) -> Box | None:
    image_width, image_height = image_size
    x = float(region["x"])
    y = float(region["y"])
    width = float(region["width"])
    height = float(region["height"])

    x1 = max(0.0, min(1.0, x))
    y1 = max(0.0, min(1.0, y))
    x2 = max(0.0, min(1.0, x + width))
    y2 = max(0.0, min(1.0, y + height))

    left = round(min(x1, x2) * image_width)
    top = round(min(y1, y2) * image_height)
    right = round(max(x1, x2) * image_width)
    bottom = round(max(y1, y2) * image_height)

    if right - left < 3 or bottom - top < 3:
        return None
    return left, top, right, bottom


def _blur_box(image: Image.Image, box: Box, blur_radius: int) -> None:
    crop = image.crop(box)
    blurred = crop.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    image.paste(blurred, box)


def _encode_png(image: Image.Image) -> bytes:
    stream = BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def _clear_metadata(document: fitz.Document) -> None:
    document.set_metadata(
        {
            "format": "PDF 1.7",
            "title": "",
            "author": "",
            "subject": "",
            "keywords": "",
            "creator": "",
            "producer": "",
            "creationDate": "",
            "modDate": "",
            "trapped": "",
            "encryption": "",
        }
    )
