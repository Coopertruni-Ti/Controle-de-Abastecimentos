import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
from utils import render_sidebar_lancar_abastecimento

# ============= CONFIGURAÇÃO DA PÁGINA =============
st.set_page_config(
    page_title="Coopertruni - Dashboard de Abastecimentos",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============= CONFIGURAÇÃO GOOGLE SHEETS =============
GOOGLE_SHEETS_ID = "1w_Zkf5HbDBsStnvrHu_eifLjgWvGMaUyhC_CEE74GDA"
CREDS_FILE = "google_creds.json"


# ============= CARREGAMENTO AUTOMÁTICO =============
@st.cache_resource
def load_google_sheets():
    """Carrega dados do Google Sheets com cache"""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        # Tentar acessar secrets (Cloud ou secrets.toml local)
        try:
            secrets = st.secrets
        except Exception:
            secrets = {}

        # Preferir credenciais vindas de st.secrets (Streamlit Cloud)
        if isinstance(secrets, dict) and "gcp_service_account" in secrets:
            service_account_info = dict(secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        else:
            # Fallback para arquivo local (desenvolvimento)
            creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)

        client = gspread.authorize(creds)

        # Permitir sobrepor o ID da planilha via secrets, se desejado
        sheet_id = GOOGLE_SHEETS_ID
        if isinstance(secrets, dict) and "GOOGLE_SHEETS_ID" in secrets:
            sheet_id = secrets["GOOGLE_SHEETS_ID"]

        spreadsheet = client.open_by_key(sheet_id)

        # Carregar abas
        df_pessoas = pd.DataFrame(spreadsheet.worksheet("PESSOAS").get_all_records())
        df_veiculos = pd.DataFrame(spreadsheet.worksheet("VEICULOS").get_all_records())
        df_abastecimentos = pd.DataFrame(spreadsheet.worksheet("ABASTECIMENTOS").get_all_records())

        # Converter datas (formato brasileiro DD/MM/YYYY)
        if "DATA" in df_abastecimentos.columns:
            df_abastecimentos["DATA"] = pd.to_datetime(df_abastecimentos["DATA"], format="%d/%m/%Y", errors="coerce")

        return df_pessoas, df_veiculos, df_abastecimentos, True
    except Exception as e:
        # Exibir erro para facilitar diagnóstico (especialmente no Streamlit Cloud)
        st.error(f"❌ Erro ao carregar dados do Google Sheets: {e}")
        return None, None, None, False


# Carregar automaticamente ao iniciar
if "data_loaded" not in st.session_state:
    with st.spinner("⏳ Carregando dados do Google Sheets..."):
        df_pessoas, df_veiculos, df_abastecimentos, success = load_google_sheets()

        # Considerar carregamento bem-sucedido mesmo que não haja registros ainda
        if success and df_abastecimentos is not None:
            st.session_state["df_pessoas"] = df_pessoas
            st.session_state["df_veiculos"] = df_veiculos
            st.session_state["df_abastecimentos"] = df_abastecimentos
            st.session_state["data_loaded"] = True
            st.session_state["last_update"] = datetime.now()
            st.rerun()
        else:
            # Marcar falha de carregamento para não ficar em loop de "carregando"
            st.session_state["data_loaded"] = False
# ============= SIDEBAR MELHORADA =============
render_sidebar_lancar_abastecimento()

# ============= CONTEÚDO PRINCIPAL =============
if "data_loaded" not in st.session_state or not st.session_state.get("data_loaded", False):
    st.warning("⏳ Carregando dados... Por favor, aguarde.")
    st.info(
        """
    O dashboard está carregando seus dados do Google Sheets automaticamente.
    Este processo acontece uma única vez e seus dados serão cacheados para performance.
    """
    )
    st.stop()

# Dados carregados
df_pessoas = st.session_state["df_pessoas"]
df_veiculos = st.session_state["df_veiculos"]
df_abastecimentos = st.session_state["df_abastecimentos"]

# ============= HOME PAGE =============

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("⛽ Abastecimentos", f"{len(df_abastecimentos):,}", help="Total de registros de abastecimento")

with col2:
    st.metric("🛢️ Volume Total", f"{df_abastecimentos['LITROS'].sum():,.0f} L", help="Litros totais abastecidos")

with col3:
    st.metric("💰 Investimento", f"R$ {df_abastecimentos['VALOR_TOTAL'].sum():,.2f}", help="Valor total investido")

with col4:
    preco_medio = df_abastecimentos["VALOR_UNITARIO"].mean()
    st.metric("💵 Preço Médio", f"R$ {preco_medio:.2f}/L", help="Preço médio por litro")

# ============= CARDS DE INFORMAÇÕES =============
st.subheader("📊 Panorama da Frota")

col1, col2, col3, col4 = st.columns(4)

with col1:
    motoristas = df_pessoas[df_pessoas["TIPO"] == "MOTORISTA"]["NOME"].nunique()
    st.info(f"**👤 Motoristas**\n{motoristas}", icon="👤")

with col2:
    veiculos = len(df_veiculos)
    st.info(f"**🚗 Veículos**\n{veiculos}", icon="🚗")

with col3:
    postos = df_pessoas[df_pessoas["TIPO"] == "POSTO"]["NOME"].nunique()
    st.info(f"**⛽ Postos**\n{postos}", icon="⛽")

with col4:
    data_min = df_abastecimentos["DATA"].min()
    data_max = df_abastecimentos["DATA"].max()
    dias = (data_max - data_min).days
    st.info(f"**📅 Período**\n{dias} dias", icon="📅")

# ============= SEÇÃO DE ANÁLISES =============
st.subheader("📈 Análises Rápidas")

tab1, tab2, tab3 = st.tabs(["Por Motorista", "Por Veículo", "Por Posto"])

with tab1:
    st.markdown("#### 👤 Top 10 Motoristas por Consumo")

    df_mot = df_abastecimentos.groupby("ID_MOTORISTA").agg({"LITROS": "sum", "VALOR_TOTAL": "sum", "ID": "count"}).reset_index()

    # Mapear nomes
    motoristas_map = df_pessoas[df_pessoas["TIPO"] == "MOTORISTA"].set_index("ID")["NOME"].to_dict()
    df_mot["NOME"] = df_mot["ID_MOTORISTA"].map(motoristas_map)

    df_mot = df_mot.dropna(subset=["NOME"]).sort_values("LITROS", ascending=False).head(10)
    df_mot.columns = ["ID_MOTORISTA", "Litros", "Gasto", "Abastecimentos", "Motorista"]

    st.dataframe(df_mot[["Motorista", "Abastecimentos", "Litros", "Gasto"]], width="stretch", hide_index=True)

with tab2:
    st.markdown("#### 🚙 Top 10 Veículos por Consumo")

    df_veic = df_abastecimentos.groupby("ID_VEICULO").agg({"LITROS": "sum", "VALOR_TOTAL": "sum", "ID": "count"}).reset_index()

    # Mapear placas
    placas_map = df_veiculos.set_index("ID")["PLACA"].to_dict()
    df_veic["PLACA"] = df_veic["ID_VEICULO"].map(placas_map)

    df_veic = df_veic.dropna(subset=["PLACA"]).sort_values("LITROS", ascending=False).head(10)
    df_veic.columns = ["ID_VEICULO", "Litros", "Gasto", "Abastecimentos", "Placa"]

    st.dataframe(df_veic[["Placa", "Abastecimentos", "Litros", "Gasto"]], width="stretch", hide_index=True)

with tab3:
    st.markdown("#### ⛽ Top 10 Postos por Faturamento")

    df_posto = (
        df_abastecimentos.groupby("ID_POSTO")
        .agg({"VALOR_TOTAL": "sum", "LITROS": "sum", "VALOR_UNITARIO": "mean", "ID": "count"})
        .reset_index()
    )

    # Mapear nomes
    postos_map = df_pessoas[df_pessoas["TIPO"] == "POSTO"].set_index("ID")["NOME"].to_dict()
    df_posto["POSTO"] = df_posto["ID_POSTO"].map(postos_map)

    df_posto = df_posto.dropna(subset=["POSTO"]).sort_values("VALOR_TOTAL", ascending=False).head(10)
    df_posto.columns = ["ID_POSTO", "Faturamento", "Litros", "Preço Médio", "Frequência", "Posto"]

    st.dataframe(
        df_posto[["Posto", "Frequência", "Litros", "Preço Médio", "Faturamento"]],
        width="stretch",
        hide_index=True,
    )

# ============= NAVEGAÇÃO =============
st.markdown("---")
st.subheader("🗺️ Navegue pelas Análises")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Números Gerais", width="stretch", key="nav_gerais"):
        st.switch_page("pages/1_📊_Números_Gerais.py")

with col2:
    if st.button("👤 Por Motorista", width="stretch", key="nav_motorista"):
        st.switch_page("pages/2_👤_Por_Motorista.py")

with col3:
    if st.button("🚙 Por Veículo", width="stretch", key="nav_veiculo"):
        st.switch_page("pages/3_🚙_Por_Veículo.py")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⛽ Por Posto", width="stretch", key="nav_posto"):
        st.switch_page("pages/4_⛽_Por_Posto.py")

with col2:
    if st.button("📈 Análises Gerais", width="stretch", key="nav_analises"):
        st.switch_page("pages/5_📈_Análises_Gerais.py")

with col3:
    if st.button("📝 Cadastros", width="stretch", key="nav_cadastros"):
        st.switch_page("pages/6_📝_Cadastros.py")

# ============= RODAPÉ =============
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #999; padding: 1rem 0;'>
    <p style='margin: 0;'><strong>Coopertruni - Dashboard de Abastecimentos v3.0</strong></p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem;'>
        Carregamento automático ✓ | Google Sheets | Streamlit
    </p>
</div>
""",
    unsafe_allow_html=True,
)
