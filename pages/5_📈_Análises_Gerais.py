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

st.set_page_config(page_title="Análises Gerais", page_icon="📈", layout="wide")
st.title("📈 Análises e Comparativos")

check_data_loaded()
render_sidebar_lancar_abastecimento()

df_pessoas, df_veiculos, df_abastecimentos = get_data()
df_filtrado = apply_filters(df_abastecimentos, df_pessoas, df_veiculos)
view_mode = ui_view_mode()

if not df_filtrado.empty:

    # ========== COMPARAÇÃO MOTORISTAS ==========
    st.subheader("👥 Comparação entre Motoristas")

    df_mot = (
        df_filtrado.groupby("NOME_MOTORISTA")
        .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "KM_L": "mean", "VALOR_UNITARIO": "mean"})
        .reset_index()
    )
    df_mot.columns = ["Motorista", "Abastecimentos", "Litros", "Custo", "KM/L", "Preço Médio"]
    df_mot = df_mot.sort_values("Custo", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(
            df_mot,
            x="Motorista",
            y="Litros",
            title="Consumo (Litros) por Motorista",
            color="Litros",
            color_continuous_scale="Blues",
            text="Litros",
        )
        fig1.update_traces(texttemplate="%{text:,.0f} L", textposition="outside")
        fig1.update_xaxes(tickangle=-45)
        st.plotly_chart(fig1, width="stretch")

    with col2:
        fig2 = px.bar(
            df_mot, x="Motorista", y="Custo", title="Gastos por Motorista", color="Custo", color_continuous_scale="Reds", text="Custo"
        )
        fig2.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
        fig2.update_xaxes(tickangle=-45)
        st.plotly_chart(fig2, width="stretch")

    # Eficiência dos motoristas
    df_mot_kml = df_mot[df_mot["KM/L"].notna() & (df_mot["KM/L"] > 0)].sort_values("KM/L", ascending=False)

    if not df_mot_kml.empty:
        st.markdown("---")
        st.subheader("⛽ Eficiência dos Motoristas")

        fig3 = px.bar(
            df_mot_kml,
            x="Motorista",
            y="KM/L",
            title="KM/L Médio por Motorista",
            color="KM/L",
            color_continuous_scale="Greens",
            text="KM/L",
        )
        fig3.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig3.update_xaxes(tickangle=-45)
        st.plotly_chart(fig3, width="stretch")

    # ========== COMPARAÇÃO VEÍCULOS ==========
    st.markdown("---")
    st.subheader("🚙 Comparação entre Veículos")

    df_veic = (
        df_filtrado.groupby(["PLACA_VEICULO", "MODELO_VEICULO"])
        .agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "KM_L": "mean"})
        .reset_index()
    )
    df_veic.columns = ["Placa", "Modelo", "Abastecimentos", "Litros", "Custo", "KM/L"]
    df_veic = df_veic.sort_values("Litros", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig4 = px.pie(df_veic.head(10), values="Litros", names="Placa", title="Distribuição de Consumo por Veículo (Top 10)", hole=0.4)
        st.plotly_chart(fig4, width="stretch")

    with col2:
        fig5 = px.pie(
            df_veic.head(10),
            values="Custo",
            names="Placa",
            title="Distribuição de Gastos por Veículo (Top 10)",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig5, width="stretch")

    # Eficiência dos veículos
    df_veic_kml = df_veic[df_veic["KM/L"].notna() & (df_veic["KM/L"] > 0)].sort_values("KM/L", ascending=False).head(10)

    if not df_veic_kml.empty:
        st.markdown("---")
        st.subheader("🏆 Top 10 Veículos Mais Eficientes")

        fig6 = px.bar(
            df_veic_kml,
            x="Placa",
            y="KM/L",
            title="Veículos com Melhor KM/L",
            color="KM/L",
            color_continuous_scale="RdYlGn",
            text="KM/L",
            hover_data=["Modelo"],
        )
        fig6.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig6.update_xaxes(tickangle=-45)
        st.plotly_chart(fig6, width="stretch")

    # ========== COMPARAÇÃO POSTOS ==========
    st.markdown("---")
    st.subheader("⛽ Comparação entre Postos")

    df_postos = (
        df_filtrado.groupby("NOME_POSTO")
        .agg({"ID": "count", "VALOR_UNITARIO": "mean", "VALOR_TOTAL": "sum", "LITROS": "sum"})
        .reset_index()
    )
    df_postos.columns = ["Posto", "Abastecimentos", "Preço Médio", "Faturamento", "Litros"]
    df_postos = df_postos.sort_values("Preço Médio")

    col1, col2 = st.columns(2)

    with col1:
        fig7 = px.bar(
            df_postos,
            x="Posto",
            y="Preço Médio",
            title="Preço Médio por Posto",
            color="Preço Médio",
            color_continuous_scale="RdYlGn_r",
            text="Preço Médio",
        )
        fig7.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
        fig7.update_xaxes(tickangle=-45)
        st.plotly_chart(fig7, width="stretch")

    with col2:
        df_postos_freq = df_postos.sort_values("Abastecimentos", ascending=False).head(10)
        fig8 = px.bar(
            df_postos_freq,
            x="Posto",
            y="Abastecimentos",
            title="Postos Mais Utilizados (Top 10)",
            color="Abastecimentos",
            color_continuous_scale="Viridis",
            text="Abastecimentos",
        )
        fig8.update_traces(textposition="outside")
        fig8.update_xaxes(tickangle=-45)
        st.plotly_chart(fig8, width="stretch")

    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📊 Evolução Temporal")

            # Agrupar por mês
            df_tempo = df_filtrado.copy()
            df_tempo["MES"] = df_tempo["DATA"].dt.to_period("M").astype(str)

            df_mensal = (
                df_tempo.groupby("MES").agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum", "VALOR_UNITARIO": "mean"}).reset_index()
            )
            df_mensal.columns = ["Mês", "Abastecimentos", "Litros", "Custo", "Preço Médio"]

            col1, col2 = st.columns(2)

            with col1:
                fig9 = px.line(df_mensal, x="Mês", y="Litros", markers=True, title="Consumo Mensal (Litros)")
                st.plotly_chart(fig9, width="stretch")

            with col2:
                fig10 = px.line(df_mensal, x="Mês", y="Custo", markers=True, title="Gastos Mensais (R$)")
                st.plotly_chart(fig10, width="stretch")

            # Preço ao longo do tempo
            fig11 = px.line(df_mensal, x="Mês", y="Preço Médio", markers=True, title="Evolução do Preço Médio do Combustível")
            fig11.update_traces(line_color="red")
            st.plotly_chart(fig11, width="stretch")

            # Tabelas resumo
            st.subheader("📋 Tabelas Resumo")

            tab1, tab2, tab3 = st.tabs(["Por Motorista", "Por Veículo", "Por Posto"])

            with tab1:
                df_mot_display = df_mot.copy()
                df_mot_display["Litros"] = df_mot_display["Litros"].apply(lambda x: f"{x:,.0f} L")
                df_mot_display["Custo"] = df_mot_display["Custo"].apply(lambda x: f"R$ {x:,.2f}")
                df_mot_display["KM/L"] = df_mot_display["KM/L"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                df_mot_display["Preço Médio"] = df_mot_display["Preço Médio"].apply(lambda x: f"R$ {x:.2f}")
                st.dataframe(df_mot_display, width="stretch", hide_index=True)

            with tab2:
                df_veic_display = df_veic.copy()
                df_veic_display["Litros"] = df_veic_display["Litros"].apply(lambda x: f"{x:,.0f} L")
                df_veic_display["Custo"] = df_veic_display["Custo"].apply(lambda x: f"R$ {x:,.2f}")
                df_veic_display["KM/L"] = df_veic_display["KM/L"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
                st.dataframe(df_veic_display, width="stretch", hide_index=True)

            with tab3:
                df_postos_display = df_postos.copy()
                df_postos_display["Litros"] = df_postos_display["Litros"].apply(lambda x: f"{x:,.0f} L")
                df_postos_display["Faturamento"] = df_postos_display["Faturamento"].apply(lambda x: f"R$ {x:,.2f}")
                df_postos_display["Preço Médio"] = df_postos_display["Preço Médio"].apply(lambda x: f"R$ {x:.2f}")
                st.dataframe(df_postos_display, width="stretch", hide_index=True)

    # ========== INSIGHTS ==========
    render_insights(insights_gerais(df_filtrado))

else:
    st.warning("⚠️ Nenhum dado disponível.")
