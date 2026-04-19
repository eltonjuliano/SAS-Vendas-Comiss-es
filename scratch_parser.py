import pdfplumber
import sys

def parse_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        print(text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse_pdf(sys.argv[1])
