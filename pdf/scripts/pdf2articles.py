import os
import PyPDF2


def extract_pages(input_pdf_path, output_pdf_path, start_page, end_page):
    """
    Extract pages from start_page to end_page (inclusive) from the input PDF and save to a new PDF.

    Parameters:
    - input_pdf_path: Path to the source PDF
    - output_pdf_path: Path to save the extracted pages
    - start_page: The first page to extract (0-indexed)
    - end_page: The last page to extract (0-indexed)
    """
    # Open the input PDF file
    with open(input_pdf_path, "rb") as infile:
        pdf_reader = PyPDF2.PdfReader(infile)

        # Create a PDF writer object
        pdf_writer = PyPDF2.PdfWriter()

        # Extract pages within the range
        for page_num in range(start_page, end_page + 1):
            if page_num < len(pdf_reader.pages):
                pdf_writer.add_page(pdf_reader.pages[page_num])

        # Write the extracted pages to a new PDF
        with open(output_pdf_path, "wb") as outfile:
            pdf_writer.write(outfile)


def extract_article_page_ranges_from_pdf(pdf_path):
    """
    Extrait les plages de pages des articles d'un fichier PDF, en commençant après la première page contenant 'DR Nord-Pas-de-Calais',
    et en utilisant la balise 'Parution' pour identifier les articles.

    Arguments :
    pdf_path (str) : Le chemin du fichier PDF à traiter.

    Retourne :
    List[Tuple[int, int]] : Une liste de tuples, chaque tuple représentant un range de pages (start_page, end_page) pour un article.
    """
    # Initialisation du lecteur de PDF
    reader = PyPDF2.PdfReader(pdf_path)

    # Liste pour stocker les numéros de pages des articles
    article_page_ranges = []

    # Variables de contrôle
    found_first_article = False
    current_article_start = None

    # Parcourir les pages et extraire les pages après "DR Nord-Pas-de-Calais"
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()

        if not found_first_article:
            # Si la page contient seulement 'DR Nord-Pas-de-Calais', l'ignorer
            if page_text.strip() == "DR Nord-Pas-de-Calais":
                found_first_article = True
                current_article_start = page_num + 1
                continue  # Passer à la page suivante sans ajouter cette page
        else:
            # Si la page contient la balise "Parution", cela marque la fin de l'article
            if "Parution" in page_text:
                if current_article_start is not None:
                    # Ajouter la plage de pages de l'article précédent
                    article_page_ranges.append((current_article_start, page_num))
                # Réinitialiser pour un nouvel article
                current_article_start = page_num + 1

    return article_page_ranges


def extract_articles_as_pdf(input_pdf_path, output_dir):

    # Extraire les plages de pages des articles
    article_page_ranges = extract_article_page_ranges_from_pdf(input_pdf_path)

    # Ouvrir le fichier PDF source
    for i, (start_page, end_page) in enumerate(article_page_ranges):
        output_pdf_path = os.path.join(output_dir, f"article_{i}.pdf")
        extract_pages(input_pdf_path, output_pdf_path, start_page, end_page)


if __name__ == "__main__":
    # Example usage
    input_pdf = "./pdf/data/Revue-Médias - DR Nord-Pas-de-Calais du 02012025.pdf"  # Path to the input PDF
    output_dir = "./pdf/data/articles"  # Directory to save the extracted articles

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    extract_articles_as_pdf(input_pdf, output_dir)
