import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

GOOGLE_SHEETS_ID = "1w_Zkf5HbDBsStnvrHu_eifLjgWvGMaUyhC_CEE74GDA"
CREDS_FILE = "google_creds.json"

# ===================== VERIFICAÇÃO E CARREGAMENTO =====================


def check_data_loaded():
    """Verifica se dados foram carregados"""
    if "df_abastecimentos" not in st.session_state:
        st.warning("⚠️ Nenhum dado carregado. Volte à página inicial e clique em 'Carregar Dados'.")
        st.stop()


def get_data():
    """Retorna os dataframes carregados"""
    return (
        st.session_state.get("df_pessoas", pd.DataFrame()),
        st.session_state.get("df_veiculos", pd.DataFrame()),
        st.session_state.get("df_abastecimentos", pd.DataFrame()),
    )


def _get_sheets_client():
    """Retorna cliente autenticado do Google Sheets para escrita."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        # Preferir credenciais vindas de st.secrets (Streamlit Cloud)
        if "gcp_service_account" in st.secrets:
            service_account_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        else:
            # Fallback para arquivo local (desenvolvimento)
            creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)

        client = gspread.authorize(creds)

        # Permitir sobrepor o ID da planilha via secrets, se desejado
        sheet_id = GOOGLE_SHEETS_ID
        if "GOOGLE_SHEETS_ID" in st.secrets:
            sheet_id = st.secrets["GOOGLE_SHEETS_ID"]

        return client.open_by_key(sheet_id)
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Google Sheets: {str(e)}")
        return None


def _get_next_id(worksheet):
    """Obtém o próximo ID disponível em uma aba."""
    try:
        data = worksheet.get_all_records()
        if not data:
            return 1
        return max([row.get("ID", 0) for row in data]) + 1
    except Exception:
        return 1


# ===================== ENRIQUECIMENTO DE DADOS =====================


def enrich_abastecimentos(df_abast, df_pessoas, df_veiculos):
    """Enriquece dados de abastecimentos com informações de pessoas e veículos"""
    if df_abast.empty:
        return df_abast

    df = df_abast.copy()

    # Mapear nomes de motoristas
    motoristas_map = df_pessoas[df_pessoas["TIPO"] == "MOTORISTA"].set_index("ID")["NOME"].to_dict()
    df["NOME_MOTORISTA"] = df["ID_MOTORISTA"].map(motoristas_map)

    # Mapear postos
    postos_map = df_pessoas[df_pessoas["TIPO"] == "POSTO"].set_index("ID")["NOME"].to_dict()
    df["NOME_POSTO"] = df["ID_POSTO"].map(postos_map)

    # Mapear veículos
    veiculos_map = df_veiculos.set_index("ID")["PLACA"].to_dict()
    df["PLACA_VEICULO"] = df["ID_VEICULO"].map(veiculos_map)

    modelo_map = df_veiculos.set_index("ID")["MODELO"].to_dict()
    df["MODELO_VEICULO"] = df["ID_VEICULO"].map(modelo_map)

    tipo_map = df_veiculos.set_index("ID")["TIPO_VEICULO"].to_dict()
    df["TIPO_VEICULO"] = df["ID_VEICULO"].map(tipo_map)

    return df


def calcular_kml(df_abast):
    """Calcula KM/L baseado em abastecimentos consecutivos"""
    if df_abast.empty or "KM_ODOMETRO" not in df_abast.columns:
        return df_abast

    df = df_abast.copy()
    df = df.sort_values(["ID_VEICULO", "DATA", "KM_ODOMETRO"])

    # Calcular diferença de KM e litros para cada veículo
    df["KM_RODADOS"] = df.groupby("ID_VEICULO")["KM_ODOMETRO"].diff()
    df["KM_L"] = df["KM_RODADOS"] / df["LITROS"]

    # Limpar valores inválidos (negativos ou muito altos)
    df.loc[df["KM_L"] < 0, "KM_L"] = np.nan
    df.loc[df["KM_L"] > 50, "KM_L"] = np.nan

    return df


def get_ultimo_km_veiculo(df_abast, id_veiculo):
    """Retorna o último KM_ODOMETRO registrado para um veículo, ou None se não houver."""

    if df_abast is None or df_abast.empty or "KM_ODOMETRO" not in df_abast.columns:
        return None

    df_v = df_abast[df_abast["ID_VEICULO"] == id_veiculo]
    if df_v.empty:
        return None

    return df_v["KM_ODOMETRO"].max()


# ===================== FILTROS =====================


def apply_filters(df_abast, df_pessoas, df_veiculos):
    """Aplica filtros na sidebar e retorna dados enriquecidos e filtrados"""

    df = enrich_abastecimentos(df_abast, df_pessoas, df_veiculos)
    df = calcular_kml(df)

    if df.empty:
        return df

    st.sidebar.header("🔍 Filtros")

    # Filtro de período
    st.sidebar.subheader("📅 Período")
    col1, col2 = st.sidebar.columns(2)

    with col1:
        data_inicio = st.date_input(
            "Início",
            value=df["DATA"].min().date() if pd.notna(df["DATA"].min()) else pd.Timestamp.now().date(),
            key="data_inicio",
            format="DD/MM/YYYY",
        )

    with col2:
        data_fim = st.date_input(
            "Fim",
            value=df["DATA"].max().date() if pd.notna(df["DATA"].max()) else pd.Timestamp.now().date(),
            key="data_fim",
            format="DD/MM/YYYY",
        )

    # Aplicar filtro de data
    df = df[(df["DATA"] >= pd.to_datetime(data_inicio)) & (df["DATA"] <= pd.to_datetime(data_fim))]

    # Filtro de motorista
    motoristas = ["Todos"] + sorted(df["NOME_MOTORISTA"].dropna().unique().tolist())
    motorista = st.sidebar.selectbox("👤 Motorista", motoristas)

    if motorista != "Todos":
        df = df[df["NOME_MOTORISTA"] == motorista]

    # Filtro de veículo
    veiculos = ["Todos"] + sorted(df["PLACA_VEICULO"].dropna().unique().tolist())
    veiculo = st.sidebar.selectbox("🚗 Veículo", veiculos)

    if veiculo != "Todos":
        df = df[df["PLACA_VEICULO"] == veiculo]

    # Filtro de posto
    postos = ["Todos"] + sorted(df["NOME_POSTO"].dropna().unique().tolist())
    posto = st.sidebar.selectbox("⛽ Posto", postos)

    if posto != "Todos":
        df = df[df["NOME_POSTO"] == posto]

    # Exportar dados filtrados (CSV)
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        "📥 Exportar dados filtrados (CSV)",
        data=csv_data,
        file_name="abastecimentos_filtrados.csv",
        mime="text/csv",
    )

    return df


# ===================== UI HELPERS =====================


def ui_view_mode():
    """Seletor de modo de visualização"""
    st.sidebar.markdown("---")
    return st.sidebar.radio("🧭 Modo de visualização", ["Essencial", "Completo"], help="Essencial: resumo. Completo: detalhes avançados.")


def render_kpis(kpis):
    """Renderiza cards de KPIs"""
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        col.metric(label=kpi["label"], value=kpi["value"], delta=kpi.get("delta"), help=kpi.get("help"))


def section_advanced(title="🔬 Análises Detalhadas"):
    """Cria expander para seção avançada"""
    return st.expander(title, expanded=False)


@st.dialog("⛽ Lançar Abastecimento")
def lancar_abastecimento_dialog():
    """Dialog global para lançamento rápido de abastecimentos."""

    df_pessoas, df_veiculos, df_abastecimentos = get_data()

    if df_pessoas.empty or df_veiculos.empty:
        st.error("❌ É necessário ter pessoas e veículos carregados para lançar abastecimentos.")
        return

    motoristas = df_pessoas[df_pessoas["TIPO"] == "MOTORISTA"]
    postos = df_pessoas[df_pessoas["TIPO"] == "POSTO"]

    if motoristas.empty or postos.empty or df_veiculos.empty:
        st.error("❌ Cadastre ao menos 1 motorista, 1 posto e 1 veículo antes de lançar abastecimentos.")
        return

    col1, col2 = st.columns(2)

    with col1:
        data_abast = st.date_input("Data do Abastecimento", value=datetime.now(), format="DD/MM/YYYY")

        # Motorista (mostrar CPF/CNPJ quando existir)
        motorista_opcoes = {}
        for _, row in motoristas.iterrows():
            cpf_valor = row.get("CPF_CNPJ", "")
            cpf_str = ""
            if pd.notna(cpf_valor) and str(cpf_valor).strip() != "":
                try:
                    cpf_str = str(int(float(str(cpf_valor))))
                except Exception:
                    cpf_str = str(cpf_valor)

            label = f"{row['NOME']} - {cpf_str}" if cpf_str else f"{row['NOME']}"
            motorista_opcoes[label] = row["ID"]

        motorista_label = st.selectbox("Motorista", list(motorista_opcoes.keys()))
        id_motorista = motorista_opcoes[motorista_label]

        # Veículo
        veiculo_opcoes = {f"{row['PLACA']} - {row['MODELO']}": row["ID"] for _, row in df_veiculos.iterrows()}
        veiculo_label = st.selectbox("Veículo", list(veiculo_opcoes.keys()))
        id_veiculo = veiculo_opcoes[veiculo_label]

        # Posto (mostrar CPF/CNPJ)
        posto_opcoes = {}
        for _, row in postos.iterrows():
            cpf_valor = row.get("CPF_CNPJ", "")
            cpf_str = ""
            if pd.notna(cpf_valor) and str(cpf_valor).strip() != "":
                try:
                    cpf_str = str(int(float(str(cpf_valor))))
                except Exception:
                    cpf_str = str(cpf_valor)

            label = f"{row['NOME']} - {cpf_str}" if cpf_str else f"{row['NOME']}"
            posto_opcoes[label] = row["ID"]

        posto_label = st.selectbox("Posto", list(posto_opcoes.keys()))
        id_posto = posto_opcoes[posto_label]

    with col2:
        odometro = st.number_input("Odômetro (KM)", min_value=0, value=0, step=1)
        litros = st.number_input("Litros", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        valor_unitario = st.number_input("Valor Unitário (R$/L)", min_value=0.0, value=0.0, step=0.0001, format="%.4f")

        valor_total = litros * valor_unitario
        st.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")

    observacoes = st.text_area("Observações (Opcional)")

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        cancelar = st.button("Cancelar")

    with col_b2:
        salvar = st.button("✅ Lançar Abastecimento", type="primary")

    if cancelar:
        st.rerun()

    if salvar:
        if litros <= 0 or valor_unitario <= 0:
            st.error("❌ Litros e Valor Unitário devem ser maiores que zero!")
            return
        if odometro <= 0:
            st.error("❌ Odômetro deve ser maior que zero!")
            return

        # Validação: KM não pode ser menor que o último registrado para o veículo
        ultimo_km = get_ultimo_km_veiculo(df_abastecimentos, id_veiculo)
        if ultimo_km is not None and odometro < ultimo_km:
            st.error(f"❌ Odômetro ({odometro} km) não pode ser menor que o último registrado para este veículo ({int(ultimo_km)} km)!")
            return

        spreadsheet = _get_sheets_client()
        if not spreadsheet:
            return

        try:
            worksheet = spreadsheet.worksheet("ABASTECIMENTOS")
            next_id = _get_next_id(worksheet)

            data_formatada = data_abast.strftime("%d/%m/%Y")
            data_cadastro = datetime.now().strftime("%d/%m/%Y")

            veiculo_row = df_veiculos[df_veiculos["ID"] == id_veiculo].iloc[0]
            combustivel_tipo = veiculo_row.get("COMBUSTIVEL_TIPO", "")

            novo_abastecimento = [
                next_id,
                data_formatada,
                id_veiculo,
                id_motorista,
                id_posto,
                litros,
                odometro,
                valor_unitario,
                valor_total,
                combustivel_tipo,
                "",
                observacoes or "",
                data_cadastro,
            ]

            worksheet.append_row(novo_abastecimento)

            st.toast(f"✅ Abastecimento registrado com sucesso! ID: {next_id}")
            st.cache_resource.clear()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao salvar abastecimento: {str(e)}")


def render_sidebar_lancar_abastecimento():
    """Renderiza botão fixo na sidebar para abrir o diálogo de abastecimento."""
    if st.sidebar.button("⛽ Lançar Abastecimento", width="stretch"):
        lancar_abastecimento_dialog()


# ===================== FORMATAÇÃO =====================


def fmt_money(v):
    """R$ 1.234,56"""
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_num(v):
    """1.234"""
    return f"{v:,.0f}".replace(",", ".")


def fmt_float(v, decimals=2):
    """12.34"""
    return f"{v:.{decimals}f}".replace(".", ",")


# ===================== INSIGHTS =====================


def insights_gerais(df):
    """Calcula insights gerais dos abastecimentos"""
    if df is None or df.empty:
        return []

    insights = []

    try:
        # Melhor eficiência
        df_kml = df[df["KM_L"].notna() & (df["KM_L"] > 0)]
        if not df_kml.empty:
            row = df_kml.loc[df_kml["KM_L"].idxmax()]
            insights.append(
                {
                    "icon": "⛽",
                    "title": "Melhor Eficiência",
                    "desc": f"{fmt_float(row['KM_L'])} km/L",
                    "extra": f"Veículo: {row.get('PLACA_VEICULO', 'N/A')}",
                }
            )
    except:
        pass

    try:
        # Menor preço
        row = df.loc[df["VALOR_UNITARIO"].idxmin()]
        insights.append(
            {
                "icon": "💰",
                "title": "Menor Preço",
                "desc": f"{fmt_money(row['VALOR_UNITARIO'])}/L",
                "extra": f"Posto: {row.get('NOME_POSTO', 'N/A')}",
            }
        )
    except:
        pass

    try:
        # Maior abastecimento
        row = df.loc[df["LITROS"].idxmax()]
        insights.append(
            {
                "icon": "🛢️",
                "title": "Maior Abastecimento",
                "desc": f"{fmt_num(row['LITROS'])} litros",
                "extra": f"{row.get('PLACA_VEICULO', 'N/A')} • {fmt_money(row['VALOR_TOTAL'])}",
            }
        )
    except:
        pass

    try:
        # Total gasto
        total = df["VALOR_TOTAL"].sum()
        media = df["VALOR_TOTAL"].mean()
        insights.append(
            {"icon": "💸", "title": "Gastos Totais", "desc": f"{fmt_money(total)}", "extra": f"Média por abastecimento: {fmt_money(media)}"}
        )
    except:
        pass

    return insights


def insights_motorista(df):
    """Insights específicos de um motorista"""
    if df is None or df.empty:
        return []

    insights = []

    try:
        insights.append(
            {
                "icon": "⛽",
                "title": "Abastecimentos",
                "desc": f"{len(df)} registros",
                "extra": f"Total: {fmt_num(df['LITROS'].sum())} litros",
            }
        )
    except:
        pass

    try:
        df_kml = df[df["KM_L"].notna() & (df["KM_L"] > 0)]
        if not df_kml.empty:
            insights.append(
                {
                    "icon": "📊",
                    "title": "Eficiência Média",
                    "desc": f"{fmt_float(df_kml['KM_L'].mean())} km/L",
                    "extra": f"Melhor: {fmt_float(df_kml['KM_L'].max())} km/L",
                }
            )
    except:
        pass

    try:
        total = df["VALOR_TOTAL"].sum()
        media = df["VALOR_TOTAL"].mean()
        insights.append(
            {"icon": "💰", "title": "Gastos Totais", "desc": f"{fmt_money(total)}", "extra": f"Média: {fmt_money(media)} por abastecimento"}
        )
    except:
        pass

    try:
        row = df.loc[df["VALOR_TOTAL"].idxmax()]
        insights.append(
            {
                "icon": "💸",
                "title": "Maior Gasto",
                "desc": f"{fmt_money(row['VALOR_TOTAL'])}",
                "extra": f"{fmt_num(row['LITROS'])} L • {row.get('NOME_POSTO', 'N/A')}",
            }
        )
    except:
        pass

    return insights


def insights_veiculo(df):
    """Insights de um veículo"""
    if df is None or df.empty:
        return []

    insights = []

    try:
        insights.append(
            {
                "icon": "⛽",
                "title": "Abastecimentos",
                "desc": f"{len(df)} registros",
                "extra": f"Total: {fmt_num(df['LITROS'].sum())} litros",
            }
        )
    except:
        pass

    try:
        df_kml = df[df["KM_L"].notna() & (df["KM_L"] > 0)]
        if not df_kml.empty:
            insights.append(
                {
                    "icon": "📊",
                    "title": "Eficiência Média",
                    "desc": f"{fmt_float(df_kml['KM_L'].mean())} km/L",
                    "extra": f"Melhor: {fmt_float(df_kml['KM_L'].max())} km/L",
                }
            )
    except:
        pass

    try:
        if "KM_ODOMETRO" in df.columns:
            km_inicial = df["KM_ODOMETRO"].min()
            km_final = df["KM_ODOMETRO"].max()
            km_rodados = km_final - km_inicial
            insights.append(
                {
                    "icon": "📏",
                    "title": "KM Rodados",
                    "desc": f"{fmt_num(km_rodados)} km",
                    "extra": f"De {fmt_num(km_inicial)} até {fmt_num(km_final)} km",
                }
            )
    except:
        pass

    try:
        total = df["VALOR_TOTAL"].sum()
        litros = df["LITROS"].sum()
        custo_litro = total / litros if litros > 0 else 0
        insights.append(
            {"icon": "💰", "title": "Custo Total", "desc": f"{fmt_money(total)}", "extra": f"Custo médio: {fmt_money(custo_litro)}/L"}
        )
    except:
        pass

    return insights


def insights_posto(df):
    """Insights de um posto"""
    if df is None or df.empty:
        return []

    insights = []

    try:
        insights.append(
            {
                "icon": "⛽",
                "title": "Abastecimentos",
                "desc": f"{len(df)} registros",
                "extra": f"Total vendido: {fmt_num(df['LITROS'].sum())} litros",
            }
        )
    except:
        pass

    try:
        preco_medio = df["VALOR_UNITARIO"].mean()
        preco_min = df["VALOR_UNITARIO"].min()
        preco_max = df["VALOR_UNITARIO"].max()
        insights.append(
            {
                "icon": "💵",
                "title": "Preço Médio",
                "desc": f"{fmt_money(preco_medio)}/L",
                "extra": f"Min: {fmt_money(preco_min)} • Max: {fmt_money(preco_max)}",
            }
        )
    except:
        pass

    try:
        total = df["VALOR_TOTAL"].sum()
        media = df["VALOR_TOTAL"].mean()
        insights.append(
            {
                "icon": "💰",
                "title": "Faturamento Total",
                "desc": f"{fmt_money(total)}",
                "extra": f"Média por abastecimento: {fmt_money(media)}",
            }
        )
    except:
        pass

    try:
        veiculos = df["PLACA_VEICULO"].nunique()
        motoristas = df["NOME_MOTORISTA"].nunique()
        insights.append(
            {"icon": "🚗", "title": "Clientes Únicos", "desc": f"{veiculos} veículos", "extra": f"{motoristas} motoristas diferentes"}
        )
    except:
        pass

    return insights


def render_insights(insights, title="💡 Insights e Estatísticas"):
    """Renderiza seção de insights"""
    st.markdown("---")
    st.subheader(title)

    if not insights:
        st.info("Sem insights para o filtro atual.")
        return

    cols = st.columns(2)
    for i, insight in enumerate(insights):
        with cols[i % 2]:
            st.success(
                f"""
**{insight['icon']} {insight['title']}**  
{insight['desc']}  
_{insight.get('extra', '')}_
            """
            )
