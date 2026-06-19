from __future__ import annotations

import json
import mimetypes
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

from pdf_blur import (
    EncryptedPdfError,
    PdfBlurError,
    SUPPORTED_IMAGE_EXTENSIONS,
    blur_image_regions,
    blur_pdf_regions,
    render_image_preview,
    render_pdf_previews,
)


APP_HOST = "127.0.0.1"
APP_PORT = int(os.environ.get("PORT", "5000"))
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "100"))
UPLOAD_TTL_SECONDS = int(os.environ.get("UPLOAD_TTL_SECONDS", str(24 * 60 * 60)))
WORK_ROOT = Path(tempfile.gettempdir()) / "pdf-region-blur"
TOKEN_PATTERN = re.compile(r"^[0-9a-f]{32}$")
SUPPORTED_PDF_EXTENSION = ".pdf"
SUPPORTED_EXTENSIONS = {SUPPORTED_PDF_EXTENSION, *SUPPORTED_IMAGE_EXTENSIONS}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def _parse_blur_radius(raw_value: str | None) -> int:
    try:
        radius = int(raw_value or "8")
    except ValueError as exc:
        raise PdfBlurError("블러 강도는 숫자로 입력해 주세요.") from exc
    if radius < 1 or radius > 40:
        raise PdfBlurError("블러 강도는 1에서 40 사이여야 합니다.")
    return radius


def _parse_regions(raw_value: str | None) -> list[dict[str, float | int]]:
    if not raw_value:
        raise PdfBlurError("블러 처리할 영역을 하나 이상 지정해 주세요.")
    try:
        regions = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise PdfBlurError("영역 데이터 형식이 올바르지 않습니다.") from exc
    if not isinstance(regions, list) or not regions:
        raise PdfBlurError("블러 처리할 영역을 하나 이상 지정해 주세요.")

    parsed: list[dict[str, float | int]] = []
    for region in regions:
        if not isinstance(region, dict):
            raise PdfBlurError("영역 데이터 형식이 올바르지 않습니다.")
        try:
            parsed.append(
                {
                    "page": int(region["page"]),
                    "x": float(region["x"]),
                    "y": float(region["y"]),
                    "width": float(region["width"]),
                    "height": float(region["height"]),
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PdfBlurError("영역 데이터 형식이 올바르지 않습니다.") from exc
    return parsed


def _download_name(original_name: str, media_type: str, output_extension: str) -> str:
    stem = Path(original_name).stem or "document"
    safe_stem = secure_filename(stem) or "document"
    suffix = ".pdf" if media_type == "pdf" else output_extension
    return f"{safe_stem}-blurred{suffix}"


def _work_dir(token: str) -> Path:
    if not TOKEN_PATTERN.fullmatch(token):
        raise PdfBlurError("작업 토큰이 올바르지 않습니다.")
    return WORK_ROOT / token


def _cleanup_old_uploads() -> None:
    if not WORK_ROOT.exists():
        return
    now = time.time()
    for child in WORK_ROOT.iterdir():
        if not child.is_dir():
            continue
        try:
            if now - child.stat().st_mtime > UPLOAD_TTL_SECONDS:
                shutil.rmtree(child, ignore_errors=True)
        except OSError:
            continue


def _cleanup_work_dir(token: str) -> None:
    try:
        shutil.rmtree(_work_dir(token), ignore_errors=True)
    except PdfBlurError:
        return


def _media_type_for_extension(extension: str) -> str:
    if extension == SUPPORTED_PDF_EXTENSION:
        return "pdf"
    if extension in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    raise PdfBlurError("PDF, PNG, JPG, WEBP 파일만 업로드할 수 있습니다.")


def _input_path_for(work_dir: Path) -> Path:
    extension = (work_dir / "extension.txt").read_text(encoding="utf-8").strip()
    return work_dir / f"input{extension}"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/upload")
def upload_file():
    _cleanup_old_uploads()
    upload = request.files.get("file") or request.files.get("pdf")
    if upload is None or upload.filename == "":
        return render_template("index.html", error="PDF 또는 이미지 파일을 선택해 주세요."), 400

    original_name = secure_filename(upload.filename) or "document.pdf"
    extension = Path(original_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        return render_template("index.html", error="PDF, PNG, JPG, WEBP 파일만 업로드할 수 있습니다."), 400

    media_type = _media_type_for_extension(extension)
    token = uuid4().hex
    work_dir = _work_dir(token)
    work_dir.mkdir(parents=True, exist_ok=False)
    input_path = work_dir / f"input{extension}"

    try:
        upload.save(input_path)
        (work_dir / "original_name.txt").write_text(original_name, encoding="utf-8")
        (work_dir / "media_type.txt").write_text(media_type, encoding="utf-8")
        (work_dir / "extension.txt").write_text(extension, encoding="utf-8")
        previews = render_pdf_previews(input_path) if media_type == "pdf" else render_image_preview(input_path)
        return render_template(
            "index.html",
            token=token,
            filename=original_name,
            media_type=media_type,
            previews=previews,
            default_blur_radius=8,
        )
    except EncryptedPdfError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        return render_template("index.html", error=str(exc)), 400
    except PdfBlurError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        return render_template("index.html", error=str(exc)), 400
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        app.logger.exception("Failed to prepare editor")
        return render_template("index.html", error="미리보기를 만드는 중 오류가 발생했습니다."), 500


@app.post("/process/<token>")
def process_file(token: str):
    try:
        work_dir = _work_dir(token)
        original_name_path = work_dir / "original_name.txt"
        media_type_path = work_dir / "media_type.txt"
        if not original_name_path.exists() or not media_type_path.exists():
            raise PdfBlurError("업로드한 파일을 찾을 수 없습니다. 다시 업로드해 주세요.")

        input_path = _input_path_for(work_dir)
        if not input_path.exists():
            raise PdfBlurError("업로드한 파일을 찾을 수 없습니다. 다시 업로드해 주세요.")

        blur_radius = _parse_blur_radius(request.form.get("blur_radius"))
        regions = _parse_regions(request.form.get("regions"))
        original_name = original_name_path.read_text(encoding="utf-8").strip() or "document"
        media_type = media_type_path.read_text(encoding="utf-8").strip()

        if media_type == "pdf":
            output_extension = ".pdf"
            output_path = work_dir / "output.pdf"
            blur_pdf_regions(
                input_path=input_path,
                output_path=output_path,
                regions=regions,
                blur_radius=blur_radius,
            )
        elif media_type == "image":
            output_extension = input_path.suffix.lower()
            output_path = work_dir / f"output{output_extension}"
            blur_image_regions(
                input_path=input_path,
                output_path=output_path,
                regions=regions,
                blur_radius=blur_radius,
            )
        else:
            raise PdfBlurError("지원하지 않는 파일 형식입니다.")

        response = send_file(
            output_path,
            mimetype=mimetypes.guess_type(output_path.name)[0] or "application/octet-stream",
            as_attachment=True,
            download_name=_download_name(original_name, media_type, output_extension),
            max_age=0,
        )
        response.call_on_close(lambda: _cleanup_work_dir(token))
        return response
    except EncryptedPdfError as exc:
        _cleanup_work_dir(token)
        return render_template("index.html", error=str(exc)), 400
    except PdfBlurError as exc:
        return render_template("index.html", error=str(exc)), 400
    except Exception:
        app.logger.exception("Failed to process file")
        return render_template("index.html", error="파일 처리 중 오류가 발생했습니다."), 500


@app.post("/cancel/<token>")
def cancel_upload(token: str):
    _cleanup_work_dir(token)
    return render_template("index.html", notice="업로드한 파일을 정리했습니다.")


if __name__ == "__main__":
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    _cleanup_old_uploads()
    app.run(host=APP_HOST, port=APP_PORT, debug=False)
