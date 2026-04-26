import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
file_path = "credentials.json"
credentials = Credentials.from_service_account_file(file_path, scopes=SCOPES)
client = gspread.authorize(credentials)
ws = client.open("BD_SAS_VENDAS").get_worksheet(0)

headers = [
    "os_number", "date", "entrada_time", "autorizacao_time", 
    "fechamento_time", "saida_time", "customer", "email", 
    "vehicle", "vehicle_model", "vehicle_year", "plate", 
    "contact", "total_parts", "total_services", "total_tires", "tire_quantity",
    "total_michelin", "michelin_quantity"
]

try:
    data = ws.get_all_records(expected_headers=headers, numericise_ignore=["os_number", "contact", "plate", "vehicle_year", "entrada_time", "saida_time", "autorizacao_time", "fechamento_time"])
    print("Sucesso! Linhas resgatadas:", len(data))
except Exception as e:
    import traceback
    traceback.print_exc()
