"""OCR Service — extracts text from PDFs and images using PaddleOCR/DocTR."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class PageResult:
    page_num: int
    raw_text: str
    confidence_score: float = 0.0
    bounding_boxes: list = field(default_factory=list)


@dataclass
class OCRResult:
    pages: list[PageResult] = field(default_factory=list)
    status: str = "ok"  # ok | low_confidence | failed

    @property
    def raw_text(self) -> str:
        return "\n".join([f"--- PAGE {p.page_num} ---\n{p.raw_text}" for p in self.pages])

    @property
    def average_confidence(self) -> float:
        scores = [p.confidence_score for p in self.pages if p.confidence_score > 0]
        return sum(scores) / len(scores) if scores else 0.0


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
            result = self._extract_pdf(file_path)
        elif suffix in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"):
            result = self._extract_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        # Confidence threshold check
        if result.average_confidence < 0.75 and result.average_confidence > 0:
            result.status = "low_confidence"
        if result.average_confidence == 0 and not result.raw_text.strip():
            result.status = "failed"

        return result

    def _extract_pdf(self, file_path: str) -> OCRResult:
        # Try text-based PDF first via pdfminer
        text = self._extract_text_pdf(file_path)
        if text and len(text.strip()) > 50:
            return OCRResult(
                pages=[PageResult(page_num=1, raw_text=text, confidence_score=1.0)]
            )

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
            ocr_text, conf, boxes = self._ocr_image(img_path)
            pages.append(PageResult(
                page_num=i,
                raw_text=ocr_text,
                confidence_score=conf,
                bounding_boxes=boxes,
            ))
        return OCRResult(pages=pages)

    def _pdf_to_images(self, file_path: str) -> list[str]:
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, dpi=300)
            paths = []
            import os
            os.makedirs("/tmp/medi-vault", exist_ok=True)
            for i, img in enumerate(images):
                tmp = f"/tmp/medi-vault/page_{i}.png"
                img.save(tmp, "PNG")
                paths.append(tmp)
            return paths
        except ImportError:
            return []

    def _extract_image(self, file_path: str) -> OCRResult:
        text, conf, boxes = self._ocr_image(file_path)
        return OCRResult(
            pages=[PageResult(page_num=1, raw_text=text, confidence_score=conf, bounding_boxes=boxes)]
        )

    def _ocr_image(self, image_path: str) -> tuple[str, float, list]:
        """Returns (text, avg_confidence, bounding_boxes)."""
        # Preprocessing: deskew, contrast, binarize
        processed = self._preprocess(image_path)

        # Try PaddleOCR first
        text, conf, boxes = self._paddle_ocr(processed or image_path)
        if text.strip():
            # Detect tables
            table_text = self._detect_tables(boxes, text)
            if table_text:
                text = text + "\n\n" + table_text
            return text, conf, boxes

        # Fallback to DocTR
        return self._doctr_ocr(processed or image_path)

    def _preprocess(self, image_path: str) -> Optional[str]:
        """Apply deskew, contrast enhancement, and binarization."""
        try:
            from PIL import Image, ImageEnhance
            import cv2

            # Load as grayscale
            pil_img = Image.open(image_path).convert("L")
            cv_img = np.array(pil_img)

            # Deskew correction
            cv_img = self._deskew(cv_img)

            # Contrast enhancement
            pil_img = Image.fromarray(cv_img)
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(2.0)

            # Binarization (Otsu thresholding)
            cv_img = np.array(pil_img)
            cv_img = self._binarize(cv_img)

            import os
            os.makedirs("/tmp/medi-vault", exist_ok=True)
            processed = f"/tmp/medi-vault/preprocessed_{Path(image_path).name}"
            Image.fromarray(cv_img).save(processed)
            return processed

        except ImportError:
            try:
                from PIL import Image, ImageEnhance
                img = Image.open(image_path).convert("L")
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.0)
                import os
                os.makedirs("/tmp/medi-vault", exist_ok=True)
                processed = f"/tmp/medi-vault/preprocessed_{Path(image_path).name}"
                img.save(processed)
                return processed
            except ImportError:
                return None

    def _deskew(self, cv_img: np.ndarray) -> np.ndarray:
        """Detect and correct skew angle using Hough transform."""
        try:
            import cv2
            # Invert for line detection
            _, binary = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            coords = np.column_stack(np.where(binary > 0))
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) < 0.5:
                return cv_img

            (h, w) = cv_img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(cv_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
        except Exception:
            return cv_img

    def _binarize(self, cv_img: np.ndarray) -> np.ndarray:
        """Apply Otsu thresholding for binarization."""
        try:
            import cv2
            # Apply Gaussian blur to reduce noise, then Otsu
            blurred = cv2.GaussianBlur(cv_img, (5, 5), 0)
            _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        except Exception:
            return cv_img

    def _detect_tables(self, boxes: list, text: str) -> str:
        """Detect table structures from bounding box Y-coordinate clustering."""
        if not boxes or len(boxes) < 4:
            return ""

        try:
            # Cluster bounding boxes by Y-coordinate to find table rows
            y_coords = []
            for box in boxes:
                if len(box) >= 4:
                    # box format: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    y_coords.append((box[0][1] + box[2][1]) / 2)

            if len(y_coords) < 3:
                return ""

            # Sort Y coords and find clusters (rows)
            y_coords_sorted = sorted(y_coords)
            clusters = []
            current_cluster = [y_coords_sorted[0]]
            for y in y_coords_sorted[1:]:
                if y - current_cluster[-1] < 20:  # within 20px = same row
                    current_cluster.append(y)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [y]
            clusters.append(current_cluster)

            # More than 3 rows likely indicates a table
            if len(clusters) >= 3:
                return "[TABLE DETECTED — " + str(len(clusters)) + " rows]"
        except Exception:
            pass

        return ""

    def _paddle_ocr(self, image_path: str) -> tuple[str, float, list]:
        """Returns (text, avg_confidence, bounding_boxes)."""
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            result = ocr.ocr(image_path, cls=True)
            if not result or not result[0]:
                return "", 0.0, []

            lines = []
            confidences = []
            boxes = []
            for line in result[0]:
                if line and len(line) > 1:
                    text_part = line[1][0] if line[1][0] else ""
                    conf_part = line[1][1] if len(line[1]) > 1 and isinstance(line[1][1], (int, float)) else 0.0
                    if text_part:
                        lines.append(text_part)
                        confidences.append(conf_part)
                    if len(line) > 0 and isinstance(line[0], list):
                        boxes.append(line[0])

            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            return "\n".join(lines), avg_conf, boxes
        except ImportError:
            return "", 0.0, []

    def _doctr_ocr(self, image_path: str) -> tuple[str, float, list]:
        """Returns (text, confidence, boxes)."""
        try:
            from doctr.io import DocumentFile
            from doctr.models import ocr_predictor
            model = ocr_predictor(pretrained=True)
            doc = DocumentFile.from_images(image_path)
            result = model(doc)

            # Extract text and confidence
            text_parts = []
            confidences = []
            boxes = []
            for page in result.pages:
                for block in page.blocks:
                    for line in block.lines:
                        for word in line.words:
                            text_parts.append(word.value)
                            confidences.append(word.confidence)
                            # Convert geometry to box format
                            # word.geometry = ((x1, y1), (x2, y2))
                            boxes.append([
                                [word.geometry[0][0], word.geometry[0][1]],
                                [word.geometry[1][0], word.geometry[0][1]],
                                [word.geometry[1][0], word.geometry[1][1]],
                                [word.geometry[0][0], word.geometry[1][1]],
                            ])

            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            return " ".join(text_parts), avg_conf, boxes
        except ImportError:
            return f"[OCR unavailable for: {image_path}]", 0.0, []
