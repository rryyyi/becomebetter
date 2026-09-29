"""图像文件解析：直接对整个图像做 OCR"""
from typing import Dict

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

# 全局单例，避免每次调用都重新加载模型
_ocr_instance = None


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
    return _ocr_instance


def extract_image(file_path: str) -> Dict:
    """解析图像文件，返回与 PDF 一致的 Document IR 结构"""
    img = Image.open(file_path).convert("RGB")
    ocr = _get_ocr()
    result = ocr.ocr(np.array(img), cls=True)

    blocks = []
    full_text_lines = []

    if result and result[0]:
        for line in result[0]:
            text = line[1][0]
            bbox_points = line[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            xs = [p[0] for p in bbox_points]
            ys = [p[1] for p in bbox_points]
            blocks.append({
                "type": "text",
                "page": 1,
                "text": text,
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
            })
            full_text_lines.append(text)

    return {
        "blocks": blocks,
        "images": [{
            "type": "image",
            "page": 1,
            "bbox": [0, 0, img.width, img.height],
            "ocr_text": "\n".join(full_text_lines),
            "image_index": 0,
        }],
        "metadata": {
            "page_count": 1,
            "has_text_layer": False,
            "width": img.width,
            "height": img.height,
        },
    }