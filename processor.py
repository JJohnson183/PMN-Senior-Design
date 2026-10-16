import requests
import pypdfium2 as pdfium # Used for reading the text out of PDF files


# Extract the text from a PDF file
def extract_info_from_pdf(pdf_url):
    try:
        # 1) Download the PDF into memory
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()

        # 2) Read the text from every page and join it into one string
        with pdfium.PdfDocument(response.content) as pdf:
            text = "\n".join(page.get_textpage().get_text_bounded() for page in pdf)

        # 3) Use "\n" line endings, and remove the "\x02" PDFium puts where a word was hyphenated across two lines
        text = text.replace("\r\n", "\n").replace("\x02", "")

        # 4) Warn if no text was found since the PDF is likely a scanned image
        if not text.strip():
            print(f"No text found in {pdf_url}, it may be a scanned image")

        return text
    except Exception as e:
        print(f"Error extracting PDF {pdf_url}: {e}")
        return None
