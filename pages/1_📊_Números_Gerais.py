import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import (
    check_data_loaded,
    get_data,
    apply_filters,
    ui_view_mode,
    render_kpis,
    section_advanced,
    insights_gerais,
    render_insights,
    render_sidebar_lancar_abastecimento,
)

st.set_page_config(page_title="Números Gerais", page_icon="📊", layout="wide")
st.title("📊 Números Gerais de Abastecimentos")
check_data_loaded()
render_sidebar_lancar_abastecimento()

# Carregar e filtrar dados
df_pessoas, df_veiculos, df_abastecimentos = get_data()
df_filtrado = apply_filters(df_abastecimentos, df_pessoas, df_veiculos)
view_mode = ui_view_mode()

if not df_filtrado.empty:

    # ========== KPIs ESSENCIAIS ==========
    total_abast = len(df_filtrado)
    litros_total = df_filtrado["LITROS"].sum()
    custo_total = df_filtrado["VALOR_TOTAL"].sum()
    preco_medio = df_filtrado["VALOR_UNITARIO"].mean()

    # Calcular KM/L médio (só dos registros válidos)
    df_kml = df_filtrado[df_filtrado["KM_L"].notna() & (df_filtrado["KM_L"] > 0)]
    km_l_medio = df_kml["KM_L"].mean() if not df_kml.empty else 0

    render_kpis(
        [
            {"label": "⛽ Total Abastecimentos", "value": f"{total_abast}", "help": "Abastecimentos no período"},
            {"label": "🛢️ Litros Total", "value": f"{litros_total:,.0f} L", "help": "Volume total abastecido"},
            {"label": "💰 Gastos Totais", "value": f"R$ {custo_total:,.2f}", "help": "Custo total com combustível"},
            {"label": "💵 Preço Médio", "value": f"R$ {preco_medio:.2f}/L", "help": "Preço médio por litro"},
        ]
    )

    st.markdown("---")

    # ========== GRÁFICO PRINCIPAL: Litros por Tipo de Combustível ==========
    st.subheader("📊 Distribuição por Tipo de Combustível")

    if "COMBUSTIVEL_TIPO" in df_filtrado.columns:
        combustivel_df = df_filtrado.groupby("COMBUSTIVEL_TIPO").agg({"LITROS": "sum", "VALOR_TOTAL": "sum", "ID": "count"}).reset_index()
        combustivel_df.columns = ["Tipo", "Litros", "Valor", "Quantidade"]

        col1, col2 = st.columns(2)

        with col1:
            fig1 = px.pie(
                combustivel_df,
                values="Litros",
                names="Tipo",
                title="Litros por Tipo de Combustível",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig1, width="stretch")

        with col2:
            fig2 = px.bar(
                combustivel_df,
                x="Tipo",
                y="Valor",
                title="Gastos por Tipo de Combustível",
                text="Valor",
                color="Tipo",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig2.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
            st.plotly_chart(fig2, width="stretch")

    # ========== KM/L Médio ==========
    if km_l_medio > 0:
        st.markdown("---")
        st.subheader("⛽ Eficiência da Frota")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📊 KM/L Médio", f"{km_l_medio:.2f}", help="Eficiência média da frota")

        with col2:
            if not df_kml.empty:
                st.metric("🏆 Melhor", f"{df_kml['KM_L'].max():.2f}", help="Melhor eficiência registrada")

        with col3:
            if not df_kml.empty:
                st.metric("📉 Pior", f"{df_kml['KM_L'].min():.2f}", help="Pior eficiência registrada")

    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Resumo por Motorista")

            df_mot = (
                df_filtrado.groupby("NOME_MOTORISTA")
                .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "VALOR_UNITARIO": "mean"})
                .reset_index()
            )
            df_mot.columns = ["Motorista", "Abastecimentos", "Litros", "Custo", "Preço Médio"]
            df_mot = df_mot.sort_values("Litros", ascending=False)

            # Formatar valores
            df_mot["Litros"] = df_mot["Litros"].apply(lambda x: f"{x:,.0f} L")
            df_mot["Custo"] = df_mot["Custo"].apply(lambda x: f"R$ {x:,.2f}")
            df_mot["Preço Médio"] = df_mot["Preço Médio"].apply(lambda x: f"R$ {x:.2f}")

            st.dataframe(df_mot, width="stretch", hide_index=True)

            st.subheader("🚙 Resumo por Veículo")

            df_veic = (
                df_filtrado.groupby(["PLACA_VEICULO", "MODELO_VEICULO"])
                .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "KM_L": "mean"})
                .reset_index()
            )
            df_veic.columns = ["Placa", "Modelo", "Abastecimentos", "Litros", "Custo", "KM/L Médio"]
            df_veic = df_veic.sort_values("Litros", ascending=False)

            # Formatar valores
            df_veic["Litros"] = df_veic["Litros"].apply(lambda x: f"{x:,.0f} L")
            df_veic["Custo"] = df_veic["Custo"].apply(lambda x: f"R$ {x:,.2f}")
            df_veic["KM/L Médio"] = df_veic["KM/L Médio"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

            st.dataframe(df_veic, width="stretch", hide_index=True)

            st.subheader("⛽ Resumo por Posto")

            df_posto = (
                df_filtrado.groupby("NOME_POSTO")
                .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "VALOR_UNITARIO": "mean"})
                .reset_index()
            )
            df_posto.columns = ["Posto", "Abastecimentos", "Litros", "Faturamento", "Preço Médio"]
            df_posto = df_posto.sort_values("Faturamento", ascending=False)

            # Formatar valores
            df_posto["Litros"] = df_posto["Litros"].apply(lambda x: f"{x:,.0f} L")
            df_posto["Faturamento"] = df_posto["Faturamento"].apply(lambda x: f"R$ {x:,.2f}")
            df_posto["Preço Médio"] = df_posto["Preço Médio"].apply(lambda x: f"R$ {x:.2f}")

            st.dataframe(df_posto, width="stretch", hide_index=True)

    # ========== INSIGHTS ==========
    render_insights(insights_gerais(df_filtrado))

else:
    st.warning("⚠️ Nenhum dado com os filtros atuais.")
