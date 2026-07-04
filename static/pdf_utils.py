
import fitz
from PIL import Image
import io

def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)

    pages = []

    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        pages.append(img)

    return pages