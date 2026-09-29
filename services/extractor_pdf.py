"""
PDF 解析器：用 PyMuPDF 提取文本块、图像，对扫描页做 OCR。
输出统一 Document IR 结构。
"""
import io
from typing import Dict, List

import fitz  # PyMuPDF
import numpy as np
from PIL import Image


def extract_pdf(file_path: str, enable_ocr: bool = True) -> Dict:
    """
    解析 PDF，返回：
    {
      "blocks": [{"type": "text", "page": N, "text": "...", "bbox": [...]}],
      "images": [{"type": "image", "page": N, "ocr_text": "...", "bbox": [...]}],
      "metadata": {"page_count": N, "has_text_layer": bool, "total_text_chars": N}
    }
    """
    doc = fitz.open(file_path)
    blocks: List[dict] = []
    images: List[dict] = []
    total_text_chars = 0

    for page_num, page in enumerate(doc):
        page_dict = page.get_text("dict")

        for block in page_dict["blocks"]:
            bbox = list(block["bbox"])

            # ── 文本块 ──
            if block["type"] == 0:
                text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text += span["text"]
                    text += "\n"
                text = text.strip()
                if text:
                    total_text_chars += len(text)
                    blocks.append({
                        "type": "text",
                        "page": page_num + 1,
                        "text": text,
                        "bbox": bbox,
                    })

            # ── 图像块 ──
            elif block["type"] == 1:
                ocr_text = ""
                # 判断是否扫描件：整页文本很少时，对图像做 OCR
                if enable_ocr and total_text_chars < 50 * (page_num + 1):
                    try:
                        ocr_text = _ocr_image_bytes(block.get("image"))
                    except Exception as e:
                        ocr_text = f"[OCR 失败: {e}]"

                images.append({
                    "type": "image",
                    "page": page_num + 1,
                    "bbox": bbox,
                    "ocr_text": ocr_text,
                    "image_index": len(images),
                })

    metadata = {
        "page_count": len(doc),
        "has_text_layer": total_text_chars > 100,
        "total_text_chars": total_text_chars,
    }
    doc.close()
    return {"blocks": blocks, "images": images, "metadata": metadata}


def _ocr_image_bytes(image_bytes: bytes) -> str:
    """对图像字节做 OCR。延迟导入 PaddleOCR，避免拖慢启动。"""
    if not image_bytes:
        return ""
    from paddleocr import PaddleOCR

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    result = ocr.ocr(np.array(img), cls=True)

    lines = []
    if result and result[0]:
        for line in result[0]:
            lines.append(line[1][0])
    return "\n".join(lines)