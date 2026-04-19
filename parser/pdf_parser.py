import pdfplumber
import re
from datetime import datetime

def parse_float(val_str):
    """Parses a Brazilian formatted float string '1.200,50' into float(1200.50)"""
    if not val_str:
        return 0.0
    return float(val_str.replace('.', '').replace(',', '.'))

def extract_pdf_data(file_obj):
    """
    Extracts relevant business fields from a given PDF file object.
    Requires pdfplumber.
    """
    text_content = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text_content += page.extract_text() + "\n"
            
    return extract_data_from_text(text_content)

def extract_data_from_text(text):
    """
    Regex based extraction from the PDF text payload.
    """
    data = {
        'os_number': '',
        'date': None,
        'entrada_time': None,
        'autorizacao_time': None,
        'fechamento_time': None,
        'saida_time': None,
        'customer': '',
        'email': '',
        'vehicle': '',
        'vehicle_model': '',
        'vehicle_year': '',
        'plate': '',
        'contact': '',
        'total_parts': 0.0,
        'total_services': 0.0,
        'total_tires': 0.0,
        'tire_quantity': 0,
        'total_michelin': 0.0,
        'michelin_quantity': 0
    }
    
    # Extract Date (Fechamento)
    date_match = re.search(r"Fechamento:\s*(\d{2}/\d{2}/\d{4})", text)
    if date_match:
        data['date'] = datetime.strptime(date_match.group(1), "%d/%m/%Y").date()
        
    # Extract OS Number
    os_match = re.search(r"Ordem de Servi[çc]o:\s*N[°º]?\s*0*(\d+)", text)
    if os_match:
        data['os_number'] = os_match.group(1)
        
    # Extract Times
    entrada_m = re.search(r"Entrada:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text)
    if entrada_m: data['entrada_time'] = entrada_m.group(1)
    
    aut_m = re.search(r"Autoriza[çc][ãa]o:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text)
    if aut_m: data['autorizacao_time'] = aut_m.group(1)
    
    fech_m = re.search(r"Fechamento:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text)
    if fech_m: data['fechamento_time'] = fech_m.group(1)
    
    saida_m = re.search(r"Sa[íi]da:\s*\d{2}/\d{2}/\d{4}\s+(\d{2}:\d{2})", text)
    if saida_m: data['saida_time'] = saida_m.group(1)
    
    # Extract Email
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    customer_email = next((e for e in emails if "cantele" not in e.lower()), "")
    data['email'] = customer_email
    
    # Extract Customer and Plate
    cliente_match = re.search(r"Cliente:\s*(.*?)\s+Placa:\s*(\S+)", text)
    if cliente_match:
        data['customer'] = cliente_match.group(1).strip()
        data['plate'] = cliente_match.group(2).strip()
        
    # Extract Vehicle
    veiculo_match = re.search(r"Ve[íi]culo:\s*(.*?)\n", text, re.IGNORECASE)
    if veiculo_match:
        # Stop at "Chassi:" if it appears on the same line or next word
        v_str = veiculo_match.group(1).split("Chassi:")[0].strip()
        data['vehicle'] = v_str
        # Extract model and year: RENAULT OROCH PRO | 2023/2024 - Flex
        parts = v_str.split("|")
        if len(parts) > 1:
            data['vehicle_model'] = parts[0].strip()
            data['vehicle_year'] = parts[1].split("-")[0].strip()
        else:
            data['vehicle_model'] = v_str
        
    # Extract Contact
    phones = re.findall(r"Telefone:\s*([\d]+)", text)
    # The shop's phone is usually 4130131666. Discard it.
    phones = [p for p in phones if p != "4130131666"]
    if phones:
        data['contact'] = phones[0]
    else:
        # Fallback to 'Outros contatos'
        outros_match = re.search(r"Outros Contatos:\s*([\d]+)", text)
        if outros_match:
            data['contact'] = outros_match.group(1)
    
    # Extract totals from summary section
    parts_match = re.search(r"Valor total em pe[çc]as:\s*([\d.]*,\d{2})", text, re.IGNORECASE)
    if parts_match:
        data['total_parts'] = parse_float(parts_match.group(1))
    else:
        # Fallback
        parts_match = re.search(r"Total pe[çc]as:\s*([\d.]*,\d{2})", text, re.IGNORECASE)
        if parts_match:
            data['total_parts'] = parse_float(parts_match.group(1))
            
    services_match = re.search(r"Valor total em servi[çc]os:\s*([\d.]*,\d{2})", text, re.IGNORECASE)
    if services_match:
        data['total_services'] = parse_float(services_match.group(1))
    else:
        services_match = re.search(r"Total servi[çc]os:\s*([\d.]*,\d{2})", text, re.IGNORECASE)
        if services_match:
            data['total_services'] = parse_float(services_match.group(1))
            
    # Extract Tire Sales
    # Scan line by line. Any item line containing 'PNEU' adds to tire total.
    # The last token of such a line is usually the 'Total' column for that item.
    total_tires = 0.0
    tire_quantity = 0
    total_michelin = 0.0
    michelin_quantity = 0
    
    for line in text.splitlines():
        if "PNEU" in line.upper():
            tokens = line.split()
            # The quantity is typically the 5th token from the end in Cantele layout
            # Format: ... PNEU ... 4,00 719,90 0,00 719,90 2879,60
            if len(tokens) >= 5:
                # Find the last token (total)
                last_token = tokens[-1]
                if re.match(r"[\d.]*,\d{2}", last_token):
                    line_val = parse_float(last_token)
                    quant_val = parse_float(tokens[-5])
                    line_qty = int(quant_val) if quant_val < 50 else 0
                    
                    total_tires += line_val
                    tire_quantity += line_qty
                    
                    # Track Michelin separately
                    if "MICHELIN" in line.upper():
                        total_michelin += line_val
                        michelin_quantity += line_qty
    
    data['total_tires'] = total_tires
    data['tire_quantity'] = tire_quantity
    data['total_michelin'] = total_michelin
    data['michelin_quantity'] = michelin_quantity
    
    return data
