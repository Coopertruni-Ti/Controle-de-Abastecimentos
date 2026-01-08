import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_ultimo_km_veiculo

# Configuração
st.set_page_config(page_title="Cadastros", page_icon="📝", layout="wide")

# ============= CONFIGURAÇÃO GOOGLE SHEETS =============
GOOGLE_SHEETS_ID = "1w_Zkf5HbDBsStnvrHu_eifLjgWvGMaUyhC_CEE74GDA"
CREDS_FILE = "google_creds.json"


def get_sheets_client():
    """Retorna cliente autenticado do Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)
        return client.open_by_key(GOOGLE_SHEETS_ID)
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Google Sheets: {str(e)}")
        return None


def get_next_id(worksheet):
    """Obtém o próximo ID disponível"""
    try:
        data = worksheet.get_all_records()
        if not data:
            return 1
        return max([row.get("ID", 0) for row in data]) + 1
    except:
        return 1


# ============= HEADER =============
st.title("📝 Cadastros e Lançamentos")
st.markdown("---")

# ============= TABS =============
tab1, tab2, tab3 = st.tabs(["👥 Pessoas", "🚗 Veículos", "⛽ Abastecimentos"])

# ============= TAB 1: CADASTRO DE PESSOAS =============
with tab1:
    st.subheader("👥 Cadastro de Pessoas")
    st.caption("Adicione motoristas, postos ou proprietários")

    with st.form("form_pessoa", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            tipo_pessoa = st.selectbox("Tipo", ["MOTORISTA", "POSTO", "PROPRIETARIO"], key="tipo_pessoa")
            nome_pessoa = st.text_input("Nome Completo", key="nome_pessoa")

        with col2:
            cpf_cnpj = st.text_input("CPF/CNPJ", key="cpf_cnpj")
            contato = st.text_input("Telefone/Email (Opcional)", key="contato")

        submitted_pessoa = st.form_submit_button("➕ Adicionar Pessoa", type="primary", width="stretch")

        if submitted_pessoa:
            if not nome_pessoa:
                st.error("❌ Nome é obrigatório!")
            else:
                with st.spinner("Salvando..."):
                    spreadsheet = get_sheets_client()
                    if spreadsheet:
                        try:
                            worksheet = spreadsheet.worksheet("PESSOAS")
                            next_id = get_next_id(worksheet)

                            # Preparar dados (colunas: ID, NOME, TIPO, TELEFONE, EMAIL, CPF_CNPJ, ENDERECO, CEP, CIDADE, ESTADO, EMPRESA, ATIVO)
                            nova_pessoa = [next_id, nome_pessoa, tipo_pessoa, contato or "", "", cpf_cnpj or "", "", "", "", "", "", "Sim"]

                            # Adicionar linha
                            worksheet.append_row(nova_pessoa)

                            st.success(f"✅ {tipo_pessoa} cadastrado(a) com sucesso! ID: {next_id}")
                            st.balloons()

                            # Limpar cache para atualizar dados
                            st.cache_resource.clear()
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {str(e)}")

    # Mostrar pessoas cadastradas
    st.markdown("---")
    st.markdown("#### 📋 Pessoas Cadastradas")

    if "df_pessoas" in st.session_state and not st.session_state["df_pessoas"].empty:
        df_pessoas = st.session_state["df_pessoas"]

        # Filtro por tipo
        tipo_filtro = st.radio("Filtrar por:", ["TODOS", "MOTORISTA", "POSTO"], horizontal=True)

        if tipo_filtro != "TODOS":
            df_filtrado = df_pessoas[df_pessoas["TIPO"] == tipo_filtro]
        else:
            df_filtrado = df_pessoas

        # Mostrar colunas disponíveis
        colunas_disponiveis = ["ID", "NOME", "TIPO"]
        for col in ["CPF_CNPJ", "CONTATO"]:
            if col in df_filtrado.columns:
                colunas_disponiveis.append(col)

        # Garantir que CPF_CNPJ seja tratado como texto para evitar erros do Arrow
        if "CPF_CNPJ" in df_filtrado.columns:
            df_filtrado["CPF_CNPJ"] = df_filtrado["CPF_CNPJ"].astype(str)

        st.dataframe(
            df_filtrado[colunas_disponiveis],
            width="stretch",
            hide_index=True,
            height=300,
        )
    else:
        st.info("ℹ️ Nenhuma pessoa cadastrada ainda.")

# ============= TAB 2: CADASTRO DE VEÍCULOS =============
with tab2:
    st.subheader("🚗 Cadastro de Veículos")
    st.caption("Adicione veículos à frota")

    # Verificar se há pessoas cadastradas
    if "df_pessoas" not in st.session_state or st.session_state["df_pessoas"].empty:
        st.warning("⚠️ Cadastre ao menos uma pessoa antes de adicionar veículos!")
        st.info("💡 Acesse a aba '👥 Pessoas' para cadastrar motoristas e postos.")
        st.stop()

    df_pessoas = st.session_state["df_pessoas"]

    with st.form("form_veiculo", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            placa = st.text_input("Placa", placeholder="ABC-1234", key="placa_veiculo")
            modelo = st.text_input("Modelo", placeholder="Ex: FH 540", key="modelo_veiculo")

            # Tipo de veículo / tração (cavalo, carreta, etc.)
            tipo_veiculo = st.selectbox(
                "Tipo de Veículo / Tração",
                [
                    "Cavalo Mecânico",
                    "Carreta",
                    "Truck",
                    "Toco",
                    "VLC / 3/4",
                    "VAN / Micro-ônibus",
                    "Utilitário",
                    "Outro",
                ],
                key="tipo_veiculo",
            )

            combustivel_tipo = st.selectbox("Tipo de Combustível", ["Gasolina", "Etanol", "Diesel", "GNV", "Flex"], key="tipo_comb")

            # Proprietário do veículo (mostrar CPF/CNPJ em vez de ID)
            proprietario_opcoes = {}
            for _, row in df_pessoas.iterrows():
                cpf_valor = row.get("CPF_CNPJ", "")
                cpf_str = ""
                if pd.notna(cpf_valor) and str(cpf_valor).strip() != "":
                    # Evitar exibir .0 em valores numéricos
                    try:
                        cpf_str = str(int(float(str(cpf_valor))))
                    except Exception:
                        cpf_str = str(cpf_valor)

                if cpf_str:
                    label = f"{row['NOME']} - {cpf_str}"
                else:
                    label = f"{row['NOME']}"

                proprietario_opcoes[label] = row["ID"]

            proprietario_selecionado = st.selectbox("Proprietário", list(proprietario_opcoes.keys()), key="proprietario_select")
            id_proprietario = proprietario_opcoes[proprietario_selecionado]

        with col2:
            ano = st.number_input("Ano", min_value=1990, max_value=2026, value=2020, key="ano_veiculo")
            cor = st.text_input("Cor (Opcional)", key="cor_veiculo")
            renavam = st.text_input("RENAVAM (Opcional)", key="renavam_veiculo")

        submitted_veiculo = st.form_submit_button("➕ Adicionar Veículo", type="primary", width="stretch")

        if submitted_veiculo:
            if not placa or not modelo:
                st.error("❌ Placa e Modelo são obrigatórios!")
            else:
                with st.spinner("Salvando..."):
                    spreadsheet = get_sheets_client()
                    if spreadsheet:
                        try:
                            worksheet = spreadsheet.worksheet("VEICULOS")
                            next_id = get_next_id(worksheet)

                            # Preparar dados (colunas: ID, PLACA, TIPO_VEICULO, MARCA, MODELO, ANO, ID_PROPRIETARIO, CHASSIS, RENAVAM, SEGURADORA, NUMERO_APÓLICE, COR, COMBUSTIVEL_TIPO, CAPACIDADE_TANQUE, KM_INICIAL, DATA_AQUISICAO, ATIVO)
                            novo_veiculo = [
                                next_id,
                                placa.upper(),
                                tipo_veiculo,  # TIPO_VEICULO
                                "",  # MARCA
                                modelo,
                                ano,
                                id_proprietario,
                                "",  # CHASSIS
                                renavam or "",
                                "",  # SEGURADORA
                                "",  # NUMERO_APÓLICE
                                cor or "",
                                combustivel_tipo,
                                100,  # CAPACIDADE_TANQUE padrão
                                0,  # KM_INICIAL
                                datetime.now().strftime("%d/%m/%Y"),  # DATA_AQUISICAO
                                "Sim",  # ATIVO
                            ]

                            # Adicionar linha
                            worksheet.append_row(novo_veiculo)

                            st.success(f"✅ Veículo {placa.upper()} cadastrado com sucesso! ID: {next_id}")
                            st.balloons()

                            # Limpar cache
                            st.cache_resource.clear()
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {str(e)}")

    # Mostrar veículos cadastrados
    st.markdown("---")
    st.markdown("#### 🚙 Veículos Cadastrados")

    if "df_veiculos" in st.session_state and not st.session_state["df_veiculos"].empty:
        df_veiculos = st.session_state["df_veiculos"]
        df_pessoas = st.session_state["df_pessoas"]

        # Filtro por tipo de combustível
        if "COMBUSTIVEL_TIPO" in df_veiculos.columns:
            combustiveis = df_veiculos["COMBUSTIVEL_TIPO"].unique()
            tipo_comb_filtro = st.multiselect(
                "Filtrar por combustível:",
                combustiveis,
                default=combustiveis,
            )
            df_filtrado = df_veiculos[df_veiculos["COMBUSTIVEL_TIPO"].isin(tipo_comb_filtro)].copy()
        else:
            df_filtrado = df_veiculos.copy()

        # Enriquecer com dados do proprietário se coluna existir
        if "ID_PROPRIETARIO" in df_filtrado.columns and not df_pessoas.empty:
            proprietarios_map = df_pessoas.set_index("ID")["NOME"].to_dict()
            df_filtrado["PROPRIETARIO"] = df_filtrado["ID_PROPRIETARIO"].map(proprietarios_map)

        # Construir lista de colunas a exibir
        colunas_exibir = []
        for col in ["ID", "PLACA", "TIPO_VEICULO", "MODELO", "COMBUSTIVEL_TIPO", "ANO", "COR", "PROPRIETARIO"]:
            if col in df_filtrado.columns:
                colunas_exibir.append(col)

        st.dataframe(
            df_filtrado[colunas_exibir],
            width="stretch",
            hide_index=True,
            height=300,
        )
    else:
        st.info("ℹ️ Nenhum veículo cadastrado ainda.")

# ============= TAB 3: LANÇAMENTO DE ABASTECIMENTOS =============
with tab3:
    st.subheader("⛽ Lançamento de Abastecimento")
    st.caption("Registre um novo abastecimento")

    # Verificar se há dados necessários
    if "df_pessoas" not in st.session_state or "df_veiculos" not in st.session_state:
        st.warning("⚠️ Carregando dados... Aguarde.")
        st.stop()

    df_pessoas = st.session_state["df_pessoas"]
    df_veiculos = st.session_state["df_veiculos"]

    # Filtrar motoristas e postos
    motoristas = df_pessoas[df_pessoas["TIPO"] == "MOTORISTA"]
    postos = df_pessoas[df_pessoas["TIPO"] == "POSTO"]

    if motoristas.empty or postos.empty or df_veiculos.empty:
        st.error("❌ É necessário ter ao menos 1 motorista, 1 posto e 1 veículo cadastrados!")
        st.info("💡 Cadastre pessoas e veículos nas abas anteriores.")
        st.stop()

    with st.form("form_abastecimento", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            # Data (formato brasileiro)
            data_abast = st.date_input("Data do Abastecimento", value=datetime.now(), key="data_abast", format="DD/MM/YYYY")

            # Motorista (mostrar CPF/CNPJ ao invés de ID)
            motorista_opcoes = {}
            for _, row in motoristas.iterrows():
                cpf_valor = row.get("CPF_CNPJ", "")
                cpf_str = ""
                if pd.notna(cpf_valor) and str(cpf_valor).strip() != "":
                    try:
                        cpf_str = str(int(float(str(cpf_valor))))
                    except Exception:
                        cpf_str = str(cpf_valor)

                if cpf_str:
                    label = f"{row['NOME']} - {cpf_str}"
                else:
                    label = f"{row['NOME']}"

                motorista_opcoes[label] = row["ID"]

            motorista_selecionado = st.selectbox("Motorista", list(motorista_opcoes.keys()), key="motorista_select")
            id_motorista = motorista_opcoes[motorista_selecionado]

            # Veículo (mantém ID apenas internamente)
            veiculo_opcoes = {f"{row['PLACA']} - {row['MODELO']}": row["ID"] for _, row in df_veiculos.iterrows()}
            veiculo_selecionado = st.selectbox("Veículo", list(veiculo_opcoes.keys()), key="veiculo_select")
            id_veiculo = veiculo_opcoes[veiculo_selecionado]

            # Posto (mostrar CPF/CNPJ ao invés de ID)
            posto_opcoes = {}
            for _, row in postos.iterrows():
                cpf_valor = row.get("CPF_CNPJ", "")
                cpf_str = ""
                if pd.notna(cpf_valor) and str(cpf_valor).strip() != "":
                    try:
                        cpf_str = str(int(float(str(cpf_valor))))
                    except Exception:
                        cpf_str = str(cpf_valor)

                if cpf_str:
                    label = f"{row['NOME']} - {cpf_str}"
                else:
                    label = f"{row['NOME']}"

                posto_opcoes[label] = row["ID"]

            posto_selecionado = st.selectbox("Posto", list(posto_opcoes.keys()), key="posto_select")
            id_posto = posto_opcoes[posto_selecionado]

        with col2:
            # Odômetro
            odometro = st.number_input("Odômetro (KM)", min_value=0, value=0, step=1, key="odometro")

            # Litros
            litros = st.number_input("Litros", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="litros")

            # Valor Unitário
            valor_unitario = st.number_input("Valor Unitário (R$/L)", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="valor_unit")

            # Calcular valor total automaticamente
            valor_total = litros * valor_unitario
            # Para valores muito pequenos, mostrar mais casas decimais para não parecer 0,00
            if valor_total < 1:
                valor_total_str = f"R$ {valor_total:.4f}"
            else:
                valor_total_str = f"R$ {valor_total:.2f}"

            st.metric("💰 Valor Total", valor_total_str)

        # Observações
        observacoes = st.text_area("Observações (Opcional)", key="obs_abast")

        submitted_abast = st.form_submit_button("⛽ Registrar Abastecimento", type="primary", width="stretch")

        if submitted_abast:
            if litros <= 0 or valor_unitario <= 0:
                st.error("❌ Litros e Valor Unitário devem ser maiores que zero!")
            elif odometro <= 0:
                st.error("❌ Odômetro deve ser maior que zero!")
            else:
                # Validação: KM não pode ser menor que o último registrado para o veículo
                df_abast_state = st.session_state.get("df_abastecimentos")
                ultimo_km = get_ultimo_km_veiculo(df_abast_state, id_veiculo) if df_abast_state is not None else None
                if ultimo_km is not None and odometro < ultimo_km:
                    st.error(
                        f"❌ Odômetro ({odometro} km) não pode ser menor que o último registrado para este veículo ({int(ultimo_km)} km)!"
                    )
                else:
                    with st.spinner("Salvando..."):
                        spreadsheet = get_sheets_client()
                        if spreadsheet:
                            try:
                                worksheet = spreadsheet.worksheet("ABASTECIMENTOS")
                                next_id = get_next_id(worksheet)

                                # Preparar dados
                                data_formatada = data_abast.strftime("%d/%m/%Y")
                                data_cadastro = datetime.now().strftime("%d/%m/%Y")

                                # Encontrar tipo de combustível do veículo selecionado
                                veiculo_row = df_veiculos[df_veiculos["ID"] == id_veiculo].iloc[0]
                                combustivel_tipo = veiculo_row.get("COMBUSTIVEL_TIPO", "")

                                novo_abastecimento = [
                                    next_id,  # ID
                                    data_formatada,  # DATA (DD/MM/YYYY)
                                    id_veiculo,  # ID_VEICULO
                                    id_motorista,  # ID_MOTORISTA
                                    id_posto,  # ID_POSTO
                                    litros,  # LITROS
                                    odometro,  # KM_ODOMETRO
                                    valor_unitario,  # VALOR_UNITARIO
                                    valor_total,  # VALOR_TOTAL
                                    combustivel_tipo,  # COMBUSTIVEL_TIPO
                                    "",  # NIVEL_TANQUE (optional)
                                    observacoes or "",  # OBSERVACOES
                                    data_cadastro,  # DATA_CADASTRO
                                ]

                                # Adicionar linha
                                worksheet.append_row(novo_abastecimento)

                                st.success(f"✅ Abastecimento registrado com sucesso! ID: {next_id}")
                                st.success(f"📊 Valor Total: R$ {valor_total:.2f} | Litros: {litros:.2f}L")
                                st.balloons()

                                # Limpar cache
                                st.cache_resource.clear()
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar: {str(e)}")

    # Mostrar últimos abastecimentos
    st.markdown("---")
    st.markdown("#### 📊 Últimos Abastecimentos")

    if "df_abastecimentos" in st.session_state and not st.session_state["df_abastecimentos"].empty:
        df_abast = st.session_state["df_abastecimentos"]

        # Pegar últimos 10
        df_ultimos = df_abast.sort_values("DATA", ascending=False).head(10)

        # Enriquecer dados
        if not motoristas.empty and not postos.empty and not df_veiculos.empty:
            motoristas_map = motoristas.set_index("ID")["NOME"].to_dict()
            postos_map = postos.set_index("ID")["NOME"].to_dict()
            veiculos_map = df_veiculos.set_index("ID")["PLACA"].to_dict()

            df_ultimos["MOTORISTA"] = df_ultimos["ID_MOTORISTA"].map(motoristas_map)
            df_ultimos["POSTO"] = df_ultimos["ID_POSTO"].map(postos_map)
            df_ultimos["PLACA"] = df_ultimos["ID_VEICULO"].map(veiculos_map)

            # Formatar data para exibição
            df_ultimos["DATA_FORMAT"] = df_ultimos["DATA"].dt.strftime("%d/%m/%Y")

            st.dataframe(
                df_ultimos[
                    [
                        "ID",
                        "DATA_FORMAT",
                        "MOTORISTA",
                        "PLACA",
                        "POSTO",
                        "LITROS",
                        "VALOR_UNITARIO",
                        "VALOR_TOTAL",
                    ]
                ],
                width="stretch",
                hide_index=True,
                height=300,
            )
    else:
        st.info("ℹ️ Nenhum abastecimento registrado ainda.")

# ============= RODAPÉ =============
st.markdown("---")
st.info(
    """
    💡 **Dica:** Todos os cadastros são salvos diretamente no Google Sheets.
    Após cadastrar, clique em "🔄 Atualizar Dados" no sidebar para atualizar as análises.
    """
)
