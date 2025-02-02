import os
import PyPDF2


def extract_pages(input_pdf_path, output_pdf_path, start_page, end_page):
    """
    Extracts pages from start_page to end_page (inclusive) from the input PDF and saves them to a new PDF.

    Parameters:
    - input_pdf_path (str): Path to the source PDF.
    - output_pdf_path (str): Path to save the extracted pages.
    - start_page (int): The first page to extract (0-indexed).
    - end_page (int): The last page to extract (0-indexed).
    """
    with open(input_pdf_path, "rb") as infile:
        pdf_reader = PyPDF2.PdfReader(infile)
        pdf_writer = PyPDF2.PdfWriter()

        for page_num in range(start_page, end_page + 1):
            if page_num < len(pdf_reader.pages):
                pdf_writer.add_page(pdf_reader.pages[page_num])

        with open(output_pdf_path, "wb") as outfile:
            pdf_writer.write(outfile)


def extract_article_page_ranges_from_pdf(pdf_path):
    """
    Extracts the page ranges of articles from a PDF file.
    It starts after the first page containing 'DR Nord-Pas-de-Calais'
    and uses the 'Parution' marker to identify articles.

    Parameters:
    - pdf_path (str): Path to the PDF file.

    Returns:
    - List[Tuple[int, int]]: A list of tuples, each representing a page range (start_page, end_page) for an article.
    """
    reader = PyPDF2.PdfReader(pdf_path)
    article_page_ranges = []
    found_first_article = False
    current_article_start = None

    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()

        if not found_first_article:
            if page_text.strip() == "DR Nord-Pas-de-Calais":
                found_first_article = True
                current_article_start = page_num + 1
                continue
        else:
            if "Parution" in page_text:
                if current_article_start is not None:
                    article_page_ranges.append((current_article_start, page_num))
                current_article_start = page_num + 1

    return article_page_ranges


def extract_articles_as_pdf(input_pdf_path, output_dir):
    """
    Extracts articles from a PDF and saves them as separate PDF files.

    Parameters:
    - input_pdf_path (str): Path to the input PDF file.
    - output_dir (str): Directory to save the extracted articles.
    """
    article_page_ranges = extract_article_page_ranges_from_pdf(input_pdf_path)

    for i, (start_page, end_page) in enumerate(article_page_ranges):
        output_pdf_path = os.path.join(output_dir, f"article{i}.pdf")
        extract_pages(input_pdf_path, output_pdf_path, start_page, end_page)


if __name__ == "__main__":
    # Example usage
    src_dir = "./pdf/data/"  # Path to the input PDF

    for i, file in enumerate(os.listdir(src_dir)):
        # Create the output directory if it doesn't exist
        filepath = os.path.join(src_dir, file)
        output_dir = f"./pdf/pdf{i}"  # Directory to save the extracted articles
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Processing file: {filepath}")
        extract_articles_as_pdf(filepath, output_dir)
