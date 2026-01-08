#!/usr/bin/env python3
"""
Script para inicializar as tabelas do Google Sheets com dados de exemplo EXPANDIDO.
Execute apenas UMA VEZ antes de usar o sistema.

Uso: python init_sheets.py
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import random

# Configuração
GOOGLE_SHEETS_ID = "1w_Zkf5HbDBsStnvrHu_eifLjgWvGMaUyhC_CEE74GDA"
CREDS_FILE = "google_creds.json"


def init_sheets():
    """Inicializa as 3 abas com estrutura e dados de exemplo expandidos."""

    # Autenticar
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)

    # Abrir planilha
    spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)

    print("📋 Inicializando tabelas do Google Sheets (VERSÃO EXPANDIDA)...\n")

    # ==================== TABELA: PESSOAS ====================
    print("1️⃣  Criando/atualizando aba PESSOAS...")
    try:
        sheet_pessoas = spreadsheet.worksheet("PESSOAS")
        sheet_pessoas.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet_pessoas = spreadsheet.add_worksheet("PESSOAS", rows=200, cols=12)

    # Headers expandidos
    headers_pessoas = ["ID", "NOME", "TIPO", "TELEFONE", "EMAIL", "CPF_CNPJ", "ENDERECO", "CEP", "CIDADE", "ESTADO", "EMPRESA", "ATIVO"]
    sheet_pessoas.append_row(headers_pessoas)

    # Dados de exemplo expandidos (20 pessoas)
    data_pessoas = [
        # Motoristas
        [
            1,
            "João Silva",
            "MOTORISTA",
            "11999999999",
            "joao@email.com",
            "12345678900",
            "Rua A, 123",
            "01234-567",
            "São Paulo",
            "SP",
            "Transportes XYZ",
            "Sim",
        ],
        [
            2,
            "Maria Santos",
            "MOTORISTA",
            "11988888888",
            "maria@email.com",
            "98765432100",
            "Rua B, 456",
            "01234-568",
            "São Paulo",
            "SP",
            "Transportes XYZ",
            "Sim",
        ],
        [
            3,
            "Pedro Oliveira",
            "MOTORISTA",
            "11977777777",
            "pedro@email.com",
            "11111111100",
            "Rua C, 789",
            "01234-569",
            "São Paulo",
            "SP",
            "Transportes XYZ",
            "Sim",
        ],
        [
            4,
            "Lucas Costa",
            "MOTORISTA",
            "11966666666",
            "lucas@email.com",
            "22222222200",
            "Av. Paulista, 1000",
            "01310-100",
            "São Paulo",
            "SP",
            "Transportes ABC",
            "Sim",
        ],
        [
            5,
            "Felipe Dias",
            "MOTORISTA",
            "11955555555",
            "felipe@email.com",
            "33333333300",
            "Rua das Flores, 500",
            "01234-570",
            "São Paulo",
            "SP",
            "Transportes ABC",
            "Sim",
        ],
        [
            6,
            "Ana Paula",
            "MOTORISTA",
            "11944444444",
            "ana@email.com",
            "44444444400",
            "Av. Brasil, 2000",
            "01234-571",
            "São Paulo",
            "SP",
            "Transportes DEF",
            "Sim",
        ],
        # Postos de combustível
        [
            7,
            "Shell Paulista",
            "POSTO",
            "1133333333",
            "shell@email.com",
            "12345678000100",
            "Avenida Paulista, 100",
            "01310-100",
            "São Paulo",
            "SP",
            "Shell Brasil",
            "Sim",
        ],
        [
            8,
            "Petrobras Centro",
            "POSTO",
            "1134444444",
            "petrobras@email.com",
            "",
            "Rua 15 de Novembro, 500",
            "01013-100",
            "São Paulo",
            "SP",
            "Petrobras",
            "Sim",
        ],
        [
            9,
            "Auto Posto ABC",
            "POSTO",
            "1135555555",
            "abc@email.com",
            "12345678000100",
            "Av. Principal, 1000",
            "01234-500",
            "São Paulo",
            "SP",
            "",
            "Sim",
        ],
        [
            10,
            "Posto Vila Maria",
            "POSTO",
            "1136666666",
            "vilaMaria@email.com",
            "",
            "Av. Paes de Barros, 300",
            "03104-010",
            "São Paulo",
            "SP",
            "",
            "Sim",
        ],
        [
            11,
            "Shell Zona Sul",
            "POSTO",
            "1137777777",
            "shell.zona.sul@email.com",
            "",
            "Avenida Santo Amaro, 2000",
            "04755-000",
            "São Paulo",
            "SP",
            "Shell Brasil",
            "Sim",
        ],
        [
            12,
            "Esso Imirim",
            "POSTO",
            "1138888888",
            "esso@email.com",
            "",
            "Avenida Imirim, 1500",
            "02463-100",
            "São Paulo",
            "SP",
            "Esso",
            "Sim",
        ],
        # Proprietários
        [
            13,
            "Coopertruni Transportes",
            "PROPRIETARIO",
            "1139999999",
            "contato@coopertruni.com",
            "12345678000200",
            "Rua Proprietário, 789",
            "01234-600",
            "São Paulo",
            "SP",
            "Coopertruni",
            "Sim",
        ],
        [
            14,
            "Empresa Transportes Silva",
            "PROPRIETARIO",
            "11988888800",
            "silva@transporte.com",
            "98765432000100",
            "Av. Empresarial, 500",
            "01234-700",
            "São Paulo",
            "SP",
            "Transportes Silva",
            "Sim",
        ],
        [
            15,
            "Transportes Regional ltda",
            "PROPRIETARIO",
            "11977777700",
            "regional@transport.com",
            "11111111000150",
            "Estrada Regional, 1000",
            "01234-800",
            "São Paulo",
            "SP",
            "",
            "Sim",
        ],
    ]

    sheet_pessoas.append_rows(data_pessoas)
    print(f"✅ {len(data_pessoas)} registros criados em PESSOAS\n")

    # ==================== TABELA: VEICULOS ====================
    print("2️⃣  Criando/atualizando aba VEICULOS...")
    try:
        sheet_veiculos = spreadsheet.worksheet("VEICULOS")
        sheet_veiculos.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet_veiculos = spreadsheet.add_worksheet("VEICULOS", rows=200, cols=18)

    # Headers expandidos
    headers_veiculos = [
        "ID",
        "PLACA",
        "TIPO_VEICULO",
        "MARCA",
        "MODELO",
        "ANO",
        "ID_PROPRIETARIO",
        "CHASSIS",
        "RENAVAM",
        "SEGURADORA",
        "NUMERO_APÓLICE",
        "COR",
        "COMBUSTIVEL_TIPO",
        "CAPACIDADE_TANQUE",
        "KM_INICIAL",
        "DATA_AQUISICAO",
        "ATIVO",
    ]
    sheet_veiculos.append_row(headers_veiculos)

    # Dados de exemplo expandidos (15 veículos)
    data_veiculos = [
        [
            1,
            "ABC1234",
            "Ônibus",
            "Marcopolo",
            "G7",
            2020,
            13,
            "ABC123DEF456",
            "12345678901234",
            "Bradesco",
            "APL123456",
            "Branco",
            "Diesel",
            200,
            0,
            "15/03/2020",
            "Sim",
        ],
        [
            2,
            "XYZ5678",
            "Micro",
            "Mercedes",
            "Sprinter",
            2021,
            13,
            "XYZ987GHI654",
            "98765432109876",
            "Porto Seguro",
            "APL654321",
            "Azul",
            "Diesel",
            150,
            0,
            "20/05/2021",
            "Sim",
        ],
        [
            3,
            "DEF9012",
            "Caminhão",
            "Volvo",
            "FH16",
            2019,
            13,
            "DEF456JKL789",
            "11111111111111",
            "Allianz",
            "APL111111",
            "Vermelho",
            "Diesel",
            350,
            5000,
            "10/02/2019",
            "Sim",
        ],
        [
            4,
            "GHI3456",
            "Van",
            "Hyundai",
            "H350",
            2022,
            13,
            "GHI789MNO123",
            "22222222222222",
            "HDI",
            "APL222222",
            "Prata",
            "Diesel",
            100,
            0,
            "01/01/2022",
            "Sim",
        ],
        [
            5,
            "JKL7890",
            "Ônibus",
            "Marcopolo",
            "Viaggio",
            2018,
            14,
            "JKL012PQR345",
            "33333333333333",
            "Bradesco",
            "APL333333",
            "Cinza",
            "Diesel",
            200,
            10000,
            "20/06/2018",
            "Sim",
        ],
        [
            6,
            "MNO1234",
            "Micro",
            "Ford",
            "Transit",
            2020,
            14,
            "MNO456STU789",
            "44444444444444",
            "Porto",
            "APL444444",
            "Branco",
            "Gasolina",
            80,
            5000,
            "10/08/2020",
            "Sim",
        ],
        [
            7,
            "PQR5678",
            "Caminhão",
            "Scania",
            "P230",
            2017,
            14,
            "PQR789VWX012",
            "55555555555555",
            "Allianz",
            "APL555555",
            "Azul",
            "Diesel",
            300,
            20000,
            "15/03/2017",
            "Sim",
        ],
        [
            8,
            "STU9012",
            "Carro",
            "Volkswagen",
            "Passat",
            2023,
            15,
            "STU234XYZ567",
            "66666666666666",
            "Zurich",
            "APL666666",
            "Preto",
            "Gasolina",
            60,
            0,
            "01/02/2023",
            "Sim",
        ],
        [
            9,
            "VWX3456",
            "Van",
            "Peugeot",
            "Boxer",
            2021,
            15,
            "VWX678ABC901",
            "77777777777777",
            "HDI",
            "APL777777",
            "Branco",
            "Diesel",
            120,
            0,
            "20/07/2021",
            "Sim",
        ],
        [
            10,
            "YZA7890",
            "Ônibus",
            "Comil",
            "Campione",
            2016,
            13,
            "YZA901DEF234",
            "88888888888888",
            "Bradesco",
            "APL888888",
            "Verde",
            "Diesel",
            250,
            30000,
            "10/10/2016",
            "Sim",
        ],
        [
            11,
            "BCD1234",
            "Micro",
            "Iveco",
            "Daily",
            2022,
            14,
            "BCD345GHI678",
            "99999999999999",
            "Porto",
            "APL999999",
            "Amarelo",
            "Diesel",
            100,
            0,
            "15/04/2022",
            "Sim",
        ],
        [
            12,
            "EFG5678",
            "Caminhão",
            "MAN",
            "TGX",
            2018,
            15,
            "EFG678JKL901",
            "11111111111112",
            "Allianz",
            "APL111112",
            "Laranja",
            "Diesel",
            400,
            15000,
            "20/05/2018",
            "Sim",
        ],
        [
            13,
            "HIJ9012",
            "Carro",
            "Chevrolet",
            "Cruze",
            2023,
            13,
            "HIJ012KLM345",
            "22222222222223",
            "Zurich",
            "APL222223",
            "Vermelho",
            "Gasolina",
            50,
            0,
            "01/01/2023",
            "Sim",
        ],
        [
            14,
            "KLM3456",
            "Van",
            "Renault",
            "Master",
            2020,
            14,
            "KLM345NOP678",
            "33333333333334",
            "HDI",
            "APL333334",
            "Prata",
            "Diesel",
            110,
            5000,
            "10/09/2020",
            "Sim",
        ],
        [
            15,
            "NOP7890",
            "Ônibus",
            "Neobus",
            "Thunder",
            2019,
            15,
            "NOP678QRS901",
            "44444444444445",
            "Bradesco",
            "APL444445",
            "Branco",
            "Diesel",
            210,
            12000,
            "20/11/2019",
            "Sim",
        ],
    ]

    sheet_veiculos.append_rows(data_veiculos)
    print(f"✅ {len(data_veiculos)} registros criados em VEICULOS\n")

    # ==================== TABELA: ABASTECIMENTOS ====================
    print("3️⃣  Criando/atualizando aba ABASTECIMENTOS...")
    try:
        sheet_abastecimentos = spreadsheet.worksheet("ABASTECIMENTOS")
        sheet_abastecimentos.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet_abastecimentos = spreadsheet.add_worksheet("ABASTECIMENTOS", rows=500, cols=13)

    # Headers expandidos
    headers_abastecimentos = [
        "ID",
        "DATA",
        "ID_VEICULO",
        "ID_MOTORISTA",
        "ID_POSTO",
        "LITROS",
        "KM_ODOMETRO",
        "VALOR_UNITARIO",
        "VALOR_TOTAL",
        "COMBUSTIVEL_TIPO",
        "NIVEL_TANQUE",
        "OBSERVACOES",
        "DATA_CADASTRO",
    ]
    sheet_abastecimentos.append_row(headers_abastecimentos)

    # Gerar 60 registros de exemplo com datas variadas
    data_abastecimentos = []
    motoristas = [1, 2, 3, 4, 5, 6]
    postos = [7, 8, 9, 10, 11, 12]
    veiculos = list(range(1, 16))

    combustivel_tipos = ["Diesel", "Gasolina", "Etanol"]
    niveis_tanque = ["Vazio", "1/4", "1/2", "3/4", "Cheio"]

    base_date = datetime(2025, 12, 1)
    km_base = 5000

    for i in range(1, 61):
        data = (base_date + timedelta(days=random.randint(0, 30))).strftime("%d/%m/%Y")
        id_veiculo = random.choice(veiculos)
        id_motorista = random.choice(motoristas)
        id_posto = random.choice(postos)
        litros = round(random.uniform(30, 120), 2)
        km = km_base + (i * random.randint(100, 500))
        valor_unitario = round(random.uniform(5.00, 6.50), 2)
        valor_total = round(litros * valor_unitario, 2)
        combustivel_tipo = random.choice(combustivel_tipos)
        nivel_tanque = random.choice(niveis_tanque)
        observacoes = ""
        data_cadastro = datetime.now().strftime("%d/%m/%Y")

        data_abastecimentos.append(
            [
                i,
                data,
                id_veiculo,
                id_motorista,
                id_posto,
                litros,
                km,
                valor_unitario,
                valor_total,
                combustivel_tipo,
                nivel_tanque,
                observacoes,
                data_cadastro,
            ]
        )

    sheet_abastecimentos.append_rows(data_abastecimentos)
    print(f"✅ {len(data_abastecimentos)} registros criados em ABASTECIMENTOS\n")

    # ==================== RESUMO FINAL ====================
    print("=" * 60)
    print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print(f"\n📊 Resumo de dados criados:")
    print(f"   • PESSOAS: {len(data_pessoas)} registros")
    print(f"   • VEICULOS: {len(data_veiculos)} registros")
    print(f"   • ABASTECIMENTOS: {len(data_abastecimentos)} registros")
    print(f"\n🚀 Próximo passo: execute 'streamlit run app.py'\n")


if __name__ == "__main__":
    try:
        init_sheets()
    except FileNotFoundError:
        print("❌ Erro: arquivo 'google_creds.json' não encontrado!")
        print("   Faça download das credenciais do Google Cloud Console.")
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
