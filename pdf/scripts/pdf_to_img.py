import os
import fitz  # PyMuPDF
import PIL
from PIL.Image import Image
import pytesseract
import io


def extract_image_with_ref(pdf, xref) -> Image:
    # Extract the image data
    image = pdf.extract_image(xref)["image"]

    return PIL.Image.open(io.BytesIO(image))  # Convert image bytes to a PIL Image


def extract_images_from_page(pdf, page_num: int) -> list[Image]:

    # Get the page
    page = pdf.load_page(page_num - 1)
    image_info = page.get_image_info(
        xrefs=True
    )  # Get meta info for all displayed images

    images = []
    for info in image_info:
        if info.get("xref", None) is not None:  # Ensure xref is valid
            image_bytes = pdf.extract_image(info["xref"])["image"]
            img = PIL.Image.open(io.BytesIO(image_bytes))

            images.append(img)

    return images


def extract_text_from_images(page_num, src_filepath, dst_dir=os.path.dirname(__file__)):
    pdf_file = fitz.open(src_filepath)

    # create the images directory if it doesn't exist
    if not os.path.exists(os.path.join(dst_dir, "images")):
        os.makedirs(os.path.join(dst_dir, "images"))

    for i, img in enumerate(extract_images_from_page(pdf_file, page_num)):
        # save the image
        img.save(os.path.join(dst_dir, f"images/image{i}.png"))
        if text := pytesseract.image_to_string(img).strip():
            print(text)
