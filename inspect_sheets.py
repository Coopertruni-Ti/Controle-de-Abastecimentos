import gspread
from google.oauth2.service_account import Credentials
import json

# Conectar ao Google Sheets
GOOGLE_SHEETS_ID = "1w_Zkf5HbDBsStnvrHu_eifLjgWvGMaUyhC_CEE74GDA"
CREDS_FILE = "google_creds.json"

try:
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)

    print("=" * 60)
    print("📋 ESTRUTURA DO GOOGLE SHEETS")
    print("=" * 60)

    for sheet_name in ["PESSOAS", "VEICULOS", "ABASTECIMENTOS"]:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            records = worksheet.get_all_records()

            print(f"\n📄 Aba: {sheet_name}")
            print(f"   Total de linhas: {len(records)}")

            if records:
                colunas = list(records[0].keys())
                print(f"   Colunas: {colunas}")
                print(f"   Exemplo do primeiro registro:")
                for col in colunas:
                    print(f"      {col}: {records[0][col]}")
            else:
                print("   ⚠️ Nenhum dado")

        except Exception as e:
            print(f"   ❌ Erro ao ler {sheet_name}: {str(e)}")

    print("\n" + "=" * 60)

except Exception as e:
    print(f"❌ Erro: {str(e)}")
