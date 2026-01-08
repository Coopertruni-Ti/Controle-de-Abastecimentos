import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import check_data_loaded, get_data, apply_filters, section_advanced, render_kpis, render_sidebar_lancar_abastecimento

st.set_page_config(page_title="Análises Detalhadas", page_icon="🔍", layout="wide")
st.title("🔍 Análises Detalhadas da Frota")

check_data_loaded()
render_sidebar_lancar_abastecimento()

# Carregar dados
df_pessoas, df_veiculos, df_abastecimentos = get_data()

# Filtros básicos (período, motorista, veículo, posto) + enriquecimento
df_base = apply_filters(df_abastecimentos, df_pessoas, df_veiculos)

if df_base.empty:
    st.warning("⚠️ Nenhum dado disponível com os filtros selecionados.")
    st.stop()

# ================== FILTROS AVANÇADOS ==================
st.markdown("---")
st.subheader("🎛️ Filtros Avançados")

col1, col2, col3, col4 = st.columns(4)

# Proprietário (a partir do ID_PROPRIETARIO em df_veiculos)
proprietario_map = {}
if not df_veiculos.empty and "ID_PROPRIETARIO" in df_veiculos.columns:
    # Criar mapa ID -> nome
    pessoas_map = df_pessoas.set_index("ID")["NOME"].to_dict()
    proprietario_series = df_veiculos["ID_PROPRIETARIO"].map(pessoas_map)
    proprietario_unicos = sorted(proprietario_series.dropna().unique().tolist())
else:
    proprietario_unicos = []

with col1:
    prop_opcoes = ["Todos"] + proprietario_unicos
    proprietario_sel = st.selectbox("👤 Proprietário", prop_opcoes)

# Tipo de veículo / tração
with col2:
    tipos_veic = ["Todos"] + sorted(df_base["TIPO_VEICULO"].dropna().unique().tolist()) if "TIPO_VEICULO" in df_base.columns else ["Todos"]
    tipo_veic_sel = st.selectbox("🚚 Tipo de Veículo/Tração", tipos_veic)

# Tipo de combustível
with col3:
    tipos_comb = (
        ["Todos"] + sorted(df_base["COMBUSTIVEL_TIPO"].dropna().unique().tolist()) if "COMBUSTIVEL_TIPO" in df_base.columns else ["Todos"]
    )
    tipo_comb_sel = st.selectbox("⛽ Tipo de Combustível", tipos_comb)

# Perfil do motorista (MOTORISTA x PROPRIETARIO, etc.)
with col4:
    tipos_pessoa = ["Todos"] + sorted(df_pessoas["TIPO"].dropna().unique().tolist()) if not df_pessoas.empty else ["Todos"]
    tipo_pessoa_sel = st.selectbox(
        "📋 Tipo de Pessoa", tipos_pessoa, help="Filtra pelo tipo cadastrado em PESSOAS (MOTORISTA, POSTO, PROPRIETARIO, etc.)"
    )

# Aplicar filtros avançados sobre df_base
df = df_base.copy()

# Filtrar por proprietário via df_veiculos
if proprietario_sel != "Todos" and not df_veiculos.empty and "ID_PROPRIETARIO" in df_veiculos.columns:
    pessoas_map = df_pessoas.set_index("ID")["NOME"].to_dict()
    veic_prop = df_veiculos.copy()
    veic_prop["NOME_PROPRIETARIO"] = veic_prop["ID_PROPRIETARIO"].map(pessoas_map)
    ids_veic_prop = veic_prop[veic_prop["NOME_PROPRIETARIO"] == proprietario_sel]["ID"].tolist()
    df = df[df["ID_VEICULO"].isin(ids_veic_prop)]

if tipo_veic_sel != "Todos" and "TIPO_VEICULO" in df.columns:
    df = df[df["TIPO_VEICULO"] == tipo_veic_sel]

if tipo_comb_sel != "Todos" and "COMBUSTIVEL_TIPO" in df.columns:
    df = df[df["COMBUSTIVEL_TIPO"] == tipo_comb_sel]

if tipo_pessoa_sel != "Todos" and not df_pessoas.empty:
    # filtra pelos abastecimentos cujo motorista é de um certo tipo em PESSOAS
    pessoas_tipo = df_pessoas[df_pessoas["TIPO"] == tipo_pessoa_sel].set_index("ID").index.tolist()
    df = df[df["ID_MOTORISTA"].isin(pessoas_tipo)]

if df.empty:
    st.warning("⚠️ Nenhum dado após aplicar os filtros avançados.")
    st.stop()

# ================== KPIs DETALHADOS ==================
st.markdown("---")
st.subheader("📊 KPIs Detalhados")

kpis = []

total_abast = len(df)
litros_total = df["LITROS"].sum()
custo_total = df["VALOR_TOTAL"].sum()
preco_medio = df["VALOR_UNITARIO"].mean()

# Eficiência média por tipo de veículo
if "KM_L" in df.columns:
    df_kml = df[df["KM_L"].notna() & (df["KM_L"] > 0)]
    km_l_medio = df_kml["KM_L"].mean() if not df_kml.empty else 0
else:
    km_l_medio = 0

kpis.append({"label": "⛽ Abastecimentos", "value": f"{total_abast}"})
kpis.append({"label": "🛢️ Litros Total", "value": f"{litros_total:,.0f} L"})
kpis.append({"label": "💰 Custo Total", "value": f"R$ {custo_total:,.2f}"})
kpis.append({"label": "📊 KM/L Médio", "value": f"{km_l_medio:.2f}" if km_l_medio > 0 else "N/A"})

render_kpis(kpis)

# ================== ABAS DE ANÁLISE ==================
st.markdown("---")

aba1, aba2, aba3, aba4 = st.tabs(
    [
        "👥 Motoristas x Veículos",
        "🚚 Tipos de Veículo / Tração",
        "⛽ Postos e Combustíveis",
        "📈 Séries Temporais",
    ]
)

# --- Aba 1: Motoristas x Veículos ---
with aba1:
    st.subheader("👥 Comparação Motoristas x Veículos")

    df_mv = (
        df.groupby(["NOME_MOTORISTA", "PLACA_VEICULO", "TIPO_VEICULO"])
        .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "KM_L": "mean"})
        .reset_index()
    )
    df_mv.columns = ["Motorista", "Placa", "Tipo Veículo", "Abastecimentos", "Litros", "Custo", "KM/L"]

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.scatter(
            df_mv,
            x="Litros",
            y="Custo",
            color="Motorista",
            size="Abastecimentos",
            hover_data=["Placa", "Tipo Veículo", "KM/L"],
            title="Litros x Custo por Motorista e Veículo",
        )
        st.plotly_chart(fig1, width="stretch")

    with col2:
        fig2 = px.bar(
            df_mv.sort_values("KM/L", ascending=False).head(20),
            x="Motorista",
            y="KM/L",
            color="Tipo Veículo",
            hover_data=["Placa"],
            title="Top combinações Motorista x Veículo por KM/L",
        )
        fig2.update_xaxes(tickangle=-45)
        st.plotly_chart(fig2, width="stretch")

    with section_advanced("📋 Tabela Motoristas x Veículos"):
        st.dataframe(df_mv, width="stretch", hide_index=True)

# --- Aba 2: Tipos de Veículo / Tração ---
with aba2:
    st.subheader("🚚 Comparação por Tipo de Veículo / Tração")

    df_tipo = df.groupby("TIPO_VEICULO").agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "KM_L": "mean"}).reset_index()
    df_tipo.columns = ["Tipo Veículo", "Abastecimentos", "Litros", "Custo", "KM/L"]

    col1, col2 = st.columns(2)

    with col1:
        fig3 = px.bar(
            df_tipo,
            x="Tipo Veículo",
            y="Litros",
            title="Consumo (Litros) por Tipo de Veículo",
            color="Litros",
            color_continuous_scale="Blues",
            text="Litros",
        )
        fig3.update_traces(texttemplate="%{text:,.0f} L", textposition="outside")
        fig3.update_xaxes(tickangle=-45)
        st.plotly_chart(fig3, width="stretch")

    with col2:
        fig4 = px.bar(
            df_tipo,
            x="Tipo Veículo",
            y="KM/L",
            title="Eficiência Média (KM/L) por Tipo de Veículo",
            color="KM/L",
            color_continuous_scale="Greens",
            text="KM/L",
        )
        fig4.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig4.update_xaxes(tickangle=-45)
        st.plotly_chart(fig4, width="stretch")

    with section_advanced("📋 Tabela por Tipo de Veículo"):
        st.dataframe(df_tipo, width="stretch", hide_index=True)

# --- Aba 3: Postos e Combustíveis ---
with aba3:
    st.subheader("⛽ Postos e Tipos de Combustível")

    df_post_comb = (
        df.groupby(["NOME_POSTO", "COMBUSTIVEL_TIPO"])
        .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "VALOR_UNITARIO": "mean"})
        .reset_index()
    )
    df_post_comb.columns = ["Posto", "Combustível", "Abastecimentos", "Litros", "Faturamento", "Preço Médio"]

    col1, col2 = st.columns(2)

    with col1:
        fig5 = px.treemap(
            df_post_comb,
            path=["Posto", "Combustível"],
            values="Faturamento",
            color="Preço Médio",
            color_continuous_scale="RdYlGn_r",
            title="Faturamento por Posto e Combustível",
        )
        st.plotly_chart(fig5, width="stretch")

    with col2:
        fig6 = px.bar(
            df_post_comb.sort_values("Preço Médio"),
            x="Posto",
            y="Preço Médio",
            color="Combustível",
            title="Preço Médio por Posto e Combustível",
        )
        fig6.update_xaxes(tickangle=-45)
        st.plotly_chart(fig6, width="stretch")

    with section_advanced("📋 Tabela Postos x Combustíveis"):
        st.dataframe(df_post_comb, width="stretch", hide_index=True)

# --- Aba 4: Séries Temporais ---
with aba4:
    st.subheader("📈 Séries Temporais Detalhadas")

    df_tempo = df.copy()
    df_tempo["MES"] = df_tempo["DATA"].dt.to_period("M").astype(str)

    df_mensal = (
        df_tempo.groupby(["MES", "TIPO_VEICULO"])
        .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "VALOR_UNITARIO": "mean"})
        .reset_index()
    )
    df_mensal.columns = ["Mês", "Tipo Veículo", "Abastecimentos", "Litros", "Custo", "Preço Médio"]

    fig7 = px.line(
        df_mensal,
        x="Mês",
        y="Litros",
        color="Tipo Veículo",
        markers=True,
        title="Consumo Mensal (Litros) por Tipo de Veículo",
    )
    st.plotly_chart(fig7, width="stretch")

    fig8 = px.line(
        df_mensal,
        x="Mês",
        y="Custo",
        color="Tipo Veículo",
        markers=True,
        title="Gastos Mensais (R$) por Tipo de Veículo",
    )
    st.plotly_chart(fig8, width="stretch")

    with section_advanced("📋 Tabela Séries Temporais"):
        st.dataframe(df_mensal, width="stretch", hide_index=True)
