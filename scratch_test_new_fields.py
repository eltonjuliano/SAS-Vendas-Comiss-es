import re
from parser.pdf_parser import extract_pdf_data
from services.commission import process_sales_dataframe
import glob

def test_new_fields():
    # Let's read one of the pdfs raw text directly for finding patterns
    import pdfplumber
    pdf_path = "relatorio-administrativo-0007304_00-SIC9E82.pdf"
    
    text_content = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"
            
    # OS N
    os_match = re.search(r"Ordem de Servi[çc]o:\s*N[°º]?\s*0*(\d+)", text_content)
    print("OS:", os_match.group(1) if os_match else "None")
    
    # Times
    entrada_m = re.search(r"Entrada:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text_content)
    aut_m = re.search(r"Autoriza[çc][ãa]o:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text_content)
    fech_m = re.search(r"Fechamento:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text_content)
    saida_m = re.search(r"Sa[íi]da:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text_content)
    
    print("Times:")
    print("Entrada", entrada_m.group(1) if entrada_m else "None")
    print("Aut", aut_m.group(1) if aut_m else "None")
    print("Fech", fech_m.group(1) if fech_m else "None")
    print("Saida", saida_m.group(1) if saida_m else "None")
    
    # Email
    email_m = re.search(r"E-mail:\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text_content)
    # The firm email is cantele@cantele.com.br, customer email is lower down or maybe suprimentos@locfrotas.com.br
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text_content)
    # Exclude cantele
    customer_email = next((e for e in emails if "cantele" not in e.lower()), None)
    print("Customer Email:", customer_email)
    
    # Tires quantity
    for line in text_content.splitlines():
        if "PNEU" in line.upper():
            tokens = line.split()
            # Usually quant is a number around 4.00 or 2.00, let's find the token that looks like \d+,\d{2} before the price
            # Example: 40639 PNEU R16 215/65 102H CONT CROSSCONTACT LX2 4,00 719,90 0,00 719,90 2879,60
            # Let's count back. -1 is total (2879,60). -2 is liq (719,90). -3 is desc (0,00). -4 is unit (719,90). -5 is quant (4,00).
            if len(tokens) >= 5:
                print("Quant?", tokens[-5])

if __name__ == "__main__":
    test_new_fields()
