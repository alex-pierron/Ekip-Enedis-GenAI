import os
import io
import fitz  # PyMuPDF
import PIL.Image
import pytesseract


def extract_image_with_ref(pdf, xref) -> PIL.Image.Image:
    """
    Extracts an image from a PDF file using its reference (xref).

    Arguments:
    ----------
    pdf (fitz.Document): The opened PDF document.
    xref (int): The reference ID of the image in the PDF.

    Returns:
    --------
    PIL.Image: The extracted image as a PIL Image object.

    Description:
    ------------
    Uses the xref identifier to extract the image data from the PDF.
    Converts the extracted image bytes into a Pillow (PIL) Image object.
    """
    image_bytes = pdf.extract_image(xref)["image"]
    return PIL.Image.open(io.BytesIO(image_bytes))


def extract_images_from_page(pdf, page_num: int) -> list[PIL.Image.Image]:
    """
    Extracts all images from a specific page of a PDF.

    Arguments:
    ----------
    pdf (fitz.Document): The opened PDF document.
    page_num (int): The page number (1-based index) from which to extract images.

    Returns:
    --------
    list[PIL.Image]: A list of extracted images as Pillow (PIL) Image objects.

    Description:
    ------------
    - Loads the specified page from the PDF.
    - Retrieves metadata of all images displayed on the page.
    - Extracts and converts each image into a Pillow (PIL) Image object.
    - Returns a list of images found on the page.
    """
    page = pdf.load_page(page_num - 1)  # Convert to 0-based index
    image_info = page.get_image_info(xrefs=True)  # Get metadata of all displayed images

    images = []
    for info in image_info:
        if "xref" in info:  # Ensure xref exists
            images.append(extract_image_with_ref(pdf, info["xref"]))

    return images


def extract_text_from_images(page_num, src_filepath, dst_dir=os.path.dirname(__file__)):
    """
    Extracts text from images found on a specified page of a PDF.

    Arguments:
    ----------
    page_num (int): The page number (1-based index) to analyze.
    src_filepath (str): The file path of the source PDF.
    dst_dir (str, optional): The destination directory for saving extracted images.
                             Default is the script's directory.

    Returns:
    --------
    None: Prints the extracted text from images found on the specified page.

    Description:
    ------------
    - Opens the given PDF file.
    - Extracts all images from the specified page.
    - Saves each extracted image as a PNG file in the `images/` subdirectory.
    - Uses Tesseract OCR (`pytesseract`) to extract text from each image.
    - Prints the extracted text if any is found.
    """
    pdf_file = fitz.open(src_filepath)

    # Create the "images" directory if it doesn't exist
    image_dir = os.path.join(dst_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    for i, img in enumerate(extract_images_from_page(pdf_file, page_num)):
        img_path = os.path.join(image_dir, f"image{i}.png")
        img.save(img_path)  # Save the extracted image

        # Extract text from the image
        text = pytesseract.image_to_string(img).strip()
        if text:
            print(f"Text extracted from image {i}:\n{text}\n")
