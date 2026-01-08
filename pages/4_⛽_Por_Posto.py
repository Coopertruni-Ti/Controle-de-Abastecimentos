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
    insights_posto,
    render_insights,
    render_sidebar_lancar_abastecimento,
)

st.set_page_config(page_title="Por Posto", page_icon="⛽", layout="wide")
st.title("⛽ Análise por Posto")

check_data_loaded()
render_sidebar_lancar_abastecimento()

df_pessoas, df_veiculos, df_abastecimentos = get_data()
df_filtrado = apply_filters(df_abastecimentos, df_pessoas, df_veiculos)
view_mode = ui_view_mode()

if not df_filtrado.empty:

    # Preparar dados de postos
    df_postos_agg = (
        df_filtrado.groupby("NOME_POSTO")
        .agg(
            {
                "ID": "count",
                "LITROS": "sum",
                "VALOR_TOTAL": "sum",
                "VALOR_UNITARIO": "mean",
                "PLACA_VEICULO": "nunique",
                "NOME_MOTORISTA": "nunique",
            }
        )
        .reset_index()
    )
    df_postos_agg.columns = ["Posto", "Abastecimentos", "Litros", "Faturamento", "Preço Médio", "Veículos", "Motoristas"]
    df_postos_agg = df_postos_agg.sort_values("Faturamento", ascending=False)

    # ========== KPIs ==========
    render_kpis(
        [
            {"label": "⛽ Postos", "value": f"{len(df_postos_agg)}"},
            {"label": "🏆 Mais Usado", "value": df_postos_agg.sort_values("Abastecimentos", ascending=False).iloc[0]["Posto"]},
            {"label": "💰 Maior Faturamento", "value": df_postos_agg.iloc[0]["Posto"]},
            {"label": "💵 Menor Preço", "value": df_postos_agg.sort_values("Preço Médio").iloc[0]["Posto"]},
        ]
    )

    st.markdown("---")

    # ========== GRÁFICO PRINCIPAL ==========
    st.subheader("📊 Top Postos por Faturamento")

    fig = px.bar(
        df_postos_agg.head(10),
        x="Posto",
        y="Faturamento",
        text="Faturamento",
        title="Postos com maior faturamento",
        color="Faturamento",
        color_continuous_scale="Greens",
    )
    fig.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, width="stretch")

    # ========== COMPARAÇÃO DE PREÇOS ==========
    st.markdown("---")
    st.subheader("💵 Comparação de Preços")

    col1, col2 = st.columns(2)

    with col1:
        fig2 = px.bar(
            df_postos_agg.sort_values("Preço Médio"),
            x="Posto",
            y="Preço Médio",
            title="Preço Médio por Posto",
            text="Preço Médio",
            color="Preço Médio",
            color_continuous_scale="RdYlGn_r",
        )
        fig2.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
        fig2.update_xaxes(tickangle=-45)
        st.plotly_chart(fig2, width="stretch")

    with col2:
        fig3 = px.bar(
            df_postos_agg.sort_values("Abastecimentos", ascending=False).head(10),
            x="Posto",
            y="Abastecimentos",
            title="Postos Mais Utilizados",
            text="Abastecimentos",
            color="Abastecimentos",
            color_continuous_scale="Blues",
        )
        fig3.update_traces(textposition="outside")
        fig3.update_xaxes(tickangle=-45)
        st.plotly_chart(fig3, width="stretch")

    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Tabela Completa de Postos")

            # Formatar tabela
            df_display = df_postos_agg.copy()
            df_display["Litros"] = df_display["Litros"].apply(lambda x: f"{x:,.0f} L")
            df_display["Faturamento"] = df_display["Faturamento"].apply(lambda x: f"R$ {x:,.2f}")
            df_display["Preço Médio"] = df_display["Preço Médio"].apply(lambda x: f"R$ {x:.2f}")

            st.dataframe(df_display, width="stretch", hide_index=True)

            # Análise de tendências de preço
            st.subheader("📈 Evolução de Preços ao Longo do Tempo")

            # Selecionar postos principais
            postos_principais = df_postos_agg.head(5)["Posto"].tolist()
            df_preco_tempo = df_filtrado[df_filtrado["NOME_POSTO"].isin(postos_principais)].copy()
            df_preco_tempo = df_preco_tempo.sort_values("DATA")

            fig4 = px.line(
                df_preco_tempo,
                x="DATA",
                y="VALOR_UNITARIO",
                color="NOME_POSTO",
                title="Evolução do Preço por Litro",
                markers=True,
                labels={"VALOR_UNITARIO": "Preço (R$/L)", "DATA": "Data", "NOME_POSTO": "Posto"},
            )
            st.plotly_chart(fig4, width="stretch")

    # ========== SELEÇÃO DE POSTO ESPECÍFICO ==========
    st.markdown("---")
    st.subheader("🔍 Análise Detalhada de Posto Específico")

    postos = sorted(df_filtrado["NOME_POSTO"].dropna().unique().tolist())
    posto_sel = st.selectbox("Selecione um posto:", postos)

    df_posto = df_filtrado[df_filtrado["NOME_POSTO"] == posto_sel]

    if not df_posto.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("⛽ Abastecimentos", f"{len(df_posto)}")

        with col2:
            st.metric("🛢️ Litros Total", f"{df_posto['LITROS'].sum():,.0f} L")

        with col3:
            st.metric("💰 Faturamento", f"R$ {df_posto['VALOR_TOTAL'].sum():,.2f}")

        with col4:
            st.metric("💵 Preço Médio", f"R$ {df_posto['VALOR_UNITARIO'].mean():.2f}/L")

        # Histórico do posto
        with st.expander("📋 Ver Histórico Completo", expanded=False):
            df_hist = df_posto[["DATA", "NOME_MOTORISTA", "PLACA_VEICULO", "LITROS", "VALOR_UNITARIO", "VALOR_TOTAL"]].copy()
            df_hist = df_hist.sort_values("DATA", ascending=False)
            df_hist["DATA"] = df_hist["DATA"].dt.strftime("%d/%m/%Y")

            df_hist["LITROS"] = df_hist["LITROS"].apply(lambda x: f"{x:,.1f} L")
            df_hist["VALOR_UNITARIO"] = df_hist["VALOR_UNITARIO"].apply(lambda x: f"R$ {x:.2f}")
            df_hist["VALOR_TOTAL"] = df_hist["VALOR_TOTAL"].apply(lambda x: f"R$ {x:,.2f}")

            df_hist.columns = ["Data", "Motorista", "Veículo", "Litros", "Preço/L", "Total"]

            st.dataframe(df_hist, width="stretch", hide_index=True)

        # Insights do posto
        render_insights(insights_posto(df_posto))

else:
    st.warning("⚠️ Nenhum dado disponível.")
