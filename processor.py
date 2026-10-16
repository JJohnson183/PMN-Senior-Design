import io
import requests
import pdfplumber # Used for reading the text out of PDF files


# Extract the text from a PDF file (scanned PDFs are only images, so they have no text to read)
def extract_info_from_pdf(pdf_url):
    try:
        # 1) Download the PDF into memory
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()

        # 2) Read the text from every page and join it into one string
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        # 3) Warn if no text was found, since the PDF is likely a scanned image
        if not text.strip():
            print(f"No text found in {pdf_url}, it may be a scanned image")

        return text
    except Exception as e:
        print(f"Error extracting PDF {pdf_url}: {e}")
        return None
