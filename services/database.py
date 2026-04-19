import gspread
import os
import json
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Configure the name of your spreadsheet here:
SPREADSHEET_NAME = "BD_SAS_VENDAS"

def get_google_client():
    """Authenticate and return the gspread client."""
    # Try to get credentials from Streamlit Secrets safely (for production)
    try:
        if "gcp_service_account" in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=SCOPES
            )
            return gspread.authorize(credentials)
    except Exception:
        pass # Ignora erro e tenta o arquivo local abaixo

    # Local approach
    file_path = "credentials.json"
    if not os.path.exists(file_path):
        st.error("⚠️ Arquivo credentials.json não encontrado. Certifique-se de que ele está na mesma pasta do painel.")
        return None
        
    credentials = Credentials.from_service_account_file(file_path, scopes=SCOPES)
    client = gspread.authorize(credentials)
    return client

def get_or_create_worksheet():
    """Finds the spreadsheet and returns the first sheet. Creates headers if empty."""
    client = get_google_client()
    if not client: return None
    
    try:
        sheet = client.open(SPREADSHEET_NAME)
        worksheet = sheet.get_worksheet(0)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"⚠️ Planilha '{SPREADSHEET_NAME}' não encontrada. Verifique se você compartilhou com o e-mail do robô.")
        return None
        
    # Check if empty or malformed to inject headers
    data = worksheet.get_all_values()
    headers = [
        "os_number", "date", "entrada_time", "autorizacao_time", 
        "fechamento_time", "saida_time", "customer", "email", 
        "vehicle", "vehicle_model", "vehicle_year", "plate", 
        "contact", "total_parts", "total_services", "total_tires", "tire_quantity",
        "total_michelin", "michelin_quantity"
    ]
    
    if not data or len(data[0]) < 2 or "date" not in data[0]:
        # Clear sheet and inject standard headers mirroring pdf_parser logic
        worksheet.clear()
        worksheet.insert_row(headers, 1)
        
    return worksheet

def load_all_sales():
    """Loads all records from Google Sheets natively as a list of dicts."""
    ws = get_or_create_worksheet()
    if not ws: return []
    
    records = ws.get_all_records(numericise_ignore=["os_number", "contact", "plate", "vehicle_year", "entrada_time", "saida_time", "autorizacao_time", "fechamento_time"])
    
    # Failsafe in case records returned is weird or empty after clearing
    if not records:
        return []
        
    # Cast float values
    for r in records:
        for key in ["total_parts", "total_services", "total_tires", "tire_quantity", "total_michelin", "michelin_quantity"]:
            val = r.get(key)
            if val == "" or val is None:
                r[key] = 0.0
            elif isinstance(val, (int, float)):
                # Se já for tipo numérico, apenas converte
                r[key] = float(val) if "quantity" not in key else int(val)
            else:
                # Se for string
                try:
                    val_str = str(val).replace("R$", "").replace(" ", "")
                    # Só remove ponto milhar se for padrão BR (com vírgula)
                    if "," in val_str:
                        val_str = val_str.replace(".", "").replace(",", ".")
                    r[key] = float(val_str) if "quantity" not in key else int(float(val_str))
                except:
                    r[key] = 0.0
                    
    return records

def save_new_sales(parsed_data_list):
    """
    Receives a list of parsed dictionaries from PDF.
    Inserts ONLY the ones that are not already present in the database.
    Returns the number of rows inserted.
    """
    if not parsed_data_list: return 0
    
    ws = get_or_create_worksheet()
    if not ws: return 0
    
    try:
        existing_records = ws.get_all_records()
        existing_os = set(str(row.get("os_number")) for row in existing_records)
    except:
        existing_os = set()
        
    rows_to_insert = []
    keys = [
        "os_number", "date", "entrada_time", "autorizacao_time", 
        "fechamento_time", "saida_time", "customer", "email", 
        "vehicle", "vehicle_model", "vehicle_year", "plate", 
        "contact", "total_parts", "total_services", "total_tires", "tire_quantity",
        "total_michelin", "michelin_quantity"
    ]
    
    for item in parsed_data_list:
        os_num = str(item.get('os_number'))
        if os_num not in existing_os and os_num.strip() != "":
            # Prepare row matching keys order
            row = []
            for k in keys:
                val = item.get(k, "")
                # Type safe for google sheets avoiding dates crashes
                if val is None: val = ""
                else: val = str(val)
                row.append(val)
            rows_to_insert.append(row)
            existing_os.add(os_num) # Previne duplicata no mesmo lote
            
    if rows_to_insert:
        # Append rows in batch
        ws.append_rows(rows_to_insert, value_input_option='USER_ENTERED')
        
    return len(rows_to_insert)
