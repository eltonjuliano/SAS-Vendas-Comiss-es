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

print("Apagando a planilha inteira...")
ws.clear()
print("Recriando cabeçalhos oficiais limpos...")
ws.append_row(headers)
print("Pronto!")
