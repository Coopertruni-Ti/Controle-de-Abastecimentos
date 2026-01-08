import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import (
    check_data_loaded,
    get_data,
    apply_filters,
    ui_view_mode,
    render_kpis,
    section_advanced,
    insights_veiculo,
    render_insights,
    render_sidebar_lancar_abastecimento,
)

st.set_page_config(page_title="Por Veículo", page_icon="🚙", layout="wide")
st.title("🚙 Análise por Veículo")

check_data_loaded()
render_sidebar_lancar_abastecimento()

df_pessoas, df_veiculos, df_abastecimentos = get_data()
df_filtrado = apply_filters(df_abastecimentos, df_pessoas, df_veiculos)
view_mode = ui_view_mode()

if not df_filtrado.empty:

    veiculos = sorted(df_filtrado["PLACA_VEICULO"].dropna().unique().tolist())
    if not veiculos:
        st.warning("⚠️ Nenhum veículo encontrado nos dados.")
        st.stop()

    veiculo = st.selectbox("🔍 Selecione o veículo:", veiculos)

    df_veic = df_filtrado[df_filtrado["PLACA_VEICULO"] == veiculo]

    if df_veic.empty:
        st.warning("⚠️ Nenhum dado para o veículo selecionado.")
        st.stop()

    # ========== KPIs ==========
    total_abast = len(df_veic)
    litros_total = df_veic["LITROS"].sum()
    custo_total = df_veic["VALOR_TOTAL"].sum()

    # KM/L médio
    df_kml = df_veic[df_veic["KM_L"].notna() & (df_veic["KM_L"] > 0)]
    km_l_medio = df_kml["KM_L"].mean() if not df_kml.empty else 0

    # KM rodados
    km_rodados = 0
    if "KM_ODOMETRO" in df_veic.columns:
        km_inicial = df_veic["KM_ODOMETRO"].min()
        km_final = df_veic["KM_ODOMETRO"].max()
        km_rodados = km_final - km_inicial

    render_kpis(
        [
            {"label": "⛽ Abastecimentos", "value": f"{total_abast}"},
            {"label": "🛢️ Litros Total", "value": f"{litros_total:,.0f} L"},
            {"label": "💰 Custo Total", "value": f"R$ {custo_total:,.2f}"},
            {"label": "📊 KM/L Médio", "value": f"{km_l_medio:.2f}" if km_l_medio > 0 else "N/A"},
        ]
    )

    st.markdown("---")

    # ========== INFORMAÇÕES DO VEÍCULO ==========
    st.subheader("🚗 Informações do Veículo")

    col1, col2, col3 = st.columns(3)

    with col1:
        modelo = df_veic["MODELO_VEICULO"].iloc[0] if "MODELO_VEICULO" in df_veic.columns else "N/A"
        st.info(f"**Modelo:** {modelo}")

    with col2:
        tipo = df_veic["TIPO_VEICULO"].iloc[0] if "TIPO_VEICULO" in df_veic.columns else "N/A"
        st.info(f"**Tipo:** {tipo}")

    with col3:
        if km_rodados > 0:
            st.info(f"**KM Rodados:** {km_rodados:,.0f} km")
        else:
            st.info("**KM Rodados:** N/A")

    st.markdown("---")

    # ========== GRÁFICO: CONSUMO E CUSTOS ==========
    st.subheader("📊 Evolução de Consumo e Custos")

    df_tempo = df_veic.sort_values("DATA")
    df_tempo["DATA_STR"] = df_tempo["DATA"].dt.strftime("%d/%m/%Y")

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.line(
            df_tempo, x="DATA", y="LITROS", markers=True, title="Litros por Abastecimento", labels={"LITROS": "Litros", "DATA": "Data"}
        )
        fig1.update_traces(line_color="#2ca02c", marker=dict(size=8))
        st.plotly_chart(fig1, width="stretch")

    with col2:
        fig2 = px.line(
            df_tempo,
            x="DATA",
            y="VALOR_TOTAL",
            markers=True,
            title="Gastos por Abastecimento",
            labels={"VALOR_TOTAL": "Valor (R$)", "DATA": "Data"},
        )
        fig2.update_traces(line_color="#d62728", marker=dict(size=8))
        st.plotly_chart(fig2, width="stretch")

    # ========== EFICIÊNCIA ==========
    if km_l_medio > 0:
        st.markdown("---")
        st.subheader("⛽ Análise de Eficiência")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📊 KM/L Médio", f"{km_l_medio:.2f}")

        with col2:
            st.metric("🏆 Melhor", f"{df_kml['KM_L'].max():.2f}")

        with col3:
            st.metric("📉 Pior", f"{df_kml['KM_L'].min():.2f}")

        # Gráfico de eficiência
        df_kml_plot = df_kml.sort_values("DATA")
        df_kml_plot["DATA_STR"] = df_kml_plot["DATA"].dt.strftime("%d/%m/%Y")

        fig3 = px.bar(
            df_kml_plot, x="DATA_STR", y="KM_L", title="Eficiência (KM/L) ao Longo do Tempo", color="KM_L", color_continuous_scale="RdYlGn"
        )
        fig3.update_xaxes(tickangle=-45)
        fig3.add_hline(y=km_l_medio, line_dash="dash", line_color="red", annotation_text=f"Média: {km_l_medio:.2f}")
        st.plotly_chart(fig3, width="stretch")

    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Histórico de Abastecimentos")

            df_historico = df_veic[
                ["DATA", "NOME_MOTORISTA", "NOME_POSTO", "LITROS", "VALOR_UNITARIO", "VALOR_TOTAL", "KM_ODOMETRO", "KM_L"]
            ].copy()
            df_historico = df_historico.sort_values("DATA", ascending=False)
            df_historico["DATA"] = df_historico["DATA"].dt.strftime("%d/%m/%Y")

            # Formatar
            df_historico["LITROS"] = df_historico["LITROS"].apply(lambda x: f"{x:,.1f} L")
            df_historico["VALOR_UNITARIO"] = df_historico["VALOR_UNITARIO"].apply(lambda x: f"R$ {x:.2f}")
            df_historico["VALOR_TOTAL"] = df_historico["VALOR_TOTAL"].apply(lambda x: f"R$ {x:,.2f}")
            df_historico["KM_L"] = df_historico["KM_L"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

            df_historico.columns = ["Data", "Motorista", "Posto", "Litros", "Preço/L", "Total", "KM", "KM/L"]

            st.dataframe(df_historico, width="stretch", hide_index=True)

            # Análise por motorista
            st.subheader("👤 Motoristas que Utilizaram")
            df_mots = df_veic.groupby("NOME_MOTORISTA").agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum"}).reset_index()
            df_mots.columns = ["Motorista", "Abastecimentos", "Litros", "Gasto"]
            df_mots = df_mots.sort_values("Abastecimentos", ascending=False)

            fig4 = px.bar(
                df_mots,
                x="Motorista",
                y="Abastecimentos",
                title="Abastecimentos por Motorista",
                text="Abastecimentos",
                color="Abastecimentos",
                color_continuous_scale="Blues",
            )
            fig4.update_traces(textposition="outside")
            fig4.update_xaxes(tickangle=-45)
            st.plotly_chart(fig4, width="stretch")

    # ========== INSIGHTS ==========
    render_insights(insights_veiculo(df_veic))

else:
    st.warning("⚠️ Nenhum dado disponível.")
