import pytesseract
from PIL import Image, ImageFilter, ImageOps


def extract_label_text(image_path: str) -> str:
    """
    Perform OCR on the given image with simple preprocessing.
    Returns uppercase text.
    """
    try:
        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)
        img = img.convert("L")
        img = img.filter(ImageFilter.SHARPEN)

        text = pytesseract.image_to_string(img, config="--psm 6")
        return text.upper().strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""