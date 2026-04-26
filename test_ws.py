import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

file_path = "credentials.json"
credentials = Credentials.from_service_account_file(file_path, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open("BD_SAS_VENDAS")

# Check if worksheet "Canceladas" exists
try:
    ws_cancel = sheet.worksheet("Canceladas")
    print("Worksheet Canceladas já existe.")
except gspread.exceptions.WorksheetNotFound:
    ws_cancel = sheet.add_worksheet(title="Canceladas", rows="100", cols="20")
    print("Worksheet Canceladas criada com sucesso.")

