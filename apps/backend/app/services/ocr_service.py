"""OCR Service — extracts text from PDFs and images using PaddleOCR/DocTR."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PageResult:
    page_num: int
    raw_text: str
    confidence_score: float = 0.0


@dataclass
class OCRResult:
    pages: list[PageResult] = field(default_factory=list)

    @property
    def raw_text(self) -> str:
        return "\n".join([f"--- PAGE {p.page_num} ---\n{p.raw_text}" for p in self.pages])


class OCRService:
    """Extract text from lab report documents.
    
    Supports: PDF (text-based), PDF (scanned), JPEG, PNG, TIFF, WEBP.
    Uses PaddleOCR as primary engine with DocTR fallback.
    """

    def extract(self, file_path: str) -> OCRResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self._extract_pdf(file_path)
        elif suffix in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"):
            return self._extract_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _extract_pdf(self, file_path: str) -> OCRResult:
        # Try text-based PDF first via pdfminer
        text = self._extract_text_pdf(file_path)
        if text and len(text.strip()) > 50:
            return OCRResult(pages=[PageResult(page_num=1, raw_text=text)])

        # Scanned PDF — rasterize + OCR
        return self._extract_scanned_pdf(file_path)

    def _extract_text_pdf(self, file_path: str) -> str:
        try:
            from pdfminer.high_level import extract_text
            return extract_text(file_path)
        except ImportError:
            return ""

    def _extract_scanned_pdf(self, file_path: str) -> OCRResult:
        pages = []
        images = self._pdf_to_images(file_path)
        for i, img_path in enumerate(images, 1):
            ocr = self._ocr_image(img_path)
            pages.append(PageResult(page_num=i, raw_text=ocr))
        return OCRResult(pages=pages)

    def _pdf_to_images(self, file_path: str) -> list[str]:
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, dpi=300)
            paths = []
            for i, img in enumerate(images):
                tmp = f"/tmp/medi-vault/page_{i}.png"
                img.save(tmp, "PNG")
                paths.append(tmp)
            return paths
        except ImportError:
            return []

    def _extract_image(self, file_path: str) -> OCRResult:
        text = self._ocr_image(file_path)
        return OCRResult(pages=[PageResult(page_num=1, raw_text=text)])

    def _ocr_image(self, image_path: str) -> str:
        # Preprocessing: deskew, contrast, binarize
        processed = self._preprocess(image_path)

        # Try PaddleOCR first
        text = self._paddle_ocr(processed or image_path)
        if text.strip():
            return text

        # Fallback to DocTR
        return self._doctr_ocr(processed or image_path)

    def _preprocess(self, image_path: str) -> Optional[str]:
        try:
            from PIL import Image, ImageEnhance
            img = Image.open(image_path).convert("L")
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            processed = f"/tmp/medi-vault/preprocessed_{Path(image_path).name}"
            img.save(processed)
            return processed
        except ImportError:
            return None

    def _paddle_ocr(self, image_path: str) -> str:
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            result = ocr.ocr(image_path, cls=True)
            if not result or not result[0]:
                return ""
            lines = []
            for line in result[0]:
                if line and len(line) > 1 and line[1][0]:
                    lines.append(line[1][0])
            return "\n".join(lines)
        except ImportError:
            return ""

    def _doctr_ocr(self, image_path: str) -> str:
        try:
            from doctr.io import DocumentFile
            from doctr.models import ocr_predictor
            model = ocr_predictor(pretrained=True)
            doc = DocumentFile.from_images(image_path)
            result = model(doc)
            return result.render()
        except ImportError:
            return f"[OCR unavailable for: {image_path}]"
