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
    insights_motorista,
    render_insights,
    render_sidebar_lancar_abastecimento,
)

st.set_page_config(page_title="Por Motorista", page_icon="👤", layout="wide")
st.title("👤 Análise por Motorista")

check_data_loaded()
render_sidebar_lancar_abastecimento()

df_pessoas, df_veiculos, df_abastecimentos = get_data()
df_filtrado = apply_filters(df_abastecimentos, df_pessoas, df_veiculos)
view_mode = ui_view_mode()

if not df_filtrado.empty:

    # Seleção de motorista
    motoristas = sorted(df_filtrado["NOME_MOTORISTA"].dropna().unique().tolist())
    if not motoristas:
        st.warning("⚠️ Nenhum motorista encontrado nos dados.")
        st.stop()

    motorista = st.selectbox("🔍 Selecione o motorista:", motoristas)

    df_mot = df_filtrado[df_filtrado["NOME_MOTORISTA"] == motorista]

    if df_mot.empty:
        st.warning("⚠️ Nenhum dado para o motorista selecionado.")
        st.stop()

    # ========== KPIs ==========
    total_abast = len(df_mot)
    litros_total = df_mot["LITROS"].sum()
    custo_total = df_mot["VALOR_TOTAL"].sum()
    preco_medio = df_mot["VALOR_UNITARIO"].mean()

    # KM/L médio
    df_kml = df_mot[df_mot["KM_L"].notna() & (df_mot["KM_L"] > 0)]
    km_l_medio = df_kml["KM_L"].mean() if not df_kml.empty else 0

    render_kpis(
        [
            {"label": "⛽ Abastecimentos", "value": f"{total_abast}"},
            {"label": "🛢️ Litros Total", "value": f"{litros_total:,.0f} L"},
            {"label": "💰 Custo Total", "value": f"R$ {custo_total:,.2f}"},
            {"label": "📊 KM/L Médio", "value": f"{km_l_medio:.2f}" if km_l_medio > 0 else "N/A"},
        ]
    )

    st.markdown("---")

    # ========== GRÁFICO PRINCIPAL ==========
    st.subheader("📈 Evolução de Gastos ao Longo do Tempo")

    df_tempo = df_mot.sort_values("DATA")
    df_tempo["DATA_STR"] = df_tempo["DATA"].dt.strftime("%d/%m/%Y")

    fig = px.line(
        df_tempo,
        x="DATA",
        y="VALOR_TOTAL",
        markers=True,
        title=f"Gastos por abastecimento — {motorista}",
        labels={"VALOR_TOTAL": "Valor (R$)", "DATA": "Data"},
    )
    fig.update_traces(line_color="#1f77b4", marker=dict(size=8))
    st.plotly_chart(fig, width="stretch")

    # ========== GRÁFICOS ADICIONAIS ==========
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛢️ Litros por Abastecimento")
        fig2 = px.bar(df_tempo, x="DATA_STR", y="LITROS", title="Volume abastecido", color="LITROS", color_continuous_scale="Blues")
        fig2.update_xaxes(tickangle=-45)
        st.plotly_chart(fig2, width="stretch")

    with col2:
        if km_l_medio > 0:
            st.subheader("⛽ Eficiência (KM/L)")
            df_kml_plot = df_kml.sort_values("DATA")
            df_kml_plot["DATA_STR"] = df_kml_plot["DATA"].dt.strftime("%d/%m/%Y")
            fig3 = px.bar(
                df_kml_plot, x="DATA_STR", y="KM_L", title="KM/L ao longo do tempo", color="KM_L", color_continuous_scale="Greens"
            )
            fig3.update_xaxes(tickangle=-45)
            st.plotly_chart(fig3, width="stretch")

    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Histórico Completo")

            df_historico = df_mot[
                ["DATA", "PLACA_VEICULO", "NOME_POSTO", "LITROS", "VALOR_UNITARIO", "VALOR_TOTAL", "KM_ODOMETRO", "KM_L"]
            ].copy()
            df_historico = df_historico.sort_values("DATA", ascending=False)
            df_historico["DATA"] = df_historico["DATA"].dt.strftime("%d/%m/%Y")

            # Formatar
            df_historico["LITROS"] = df_historico["LITROS"].apply(lambda x: f"{x:,.1f} L")
            df_historico["VALOR_UNITARIO"] = df_historico["VALOR_UNITARIO"].apply(lambda x: f"R$ {x:.2f}")
            df_historico["VALOR_TOTAL"] = df_historico["VALOR_TOTAL"].apply(lambda x: f"R$ {x:,.2f}")
            df_historico["KM_L"] = df_historico["KM_L"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

            df_historico.columns = ["Data", "Veículo", "Posto", "Litros", "Preço/L", "Total", "KM", "KM/L"]

            st.dataframe(df_historico, width="stretch", hide_index=True)

            # Análise por posto
            st.subheader("⛽ Postos Mais Utilizados")
            df_postos = df_mot.groupby("NOME_POSTO").agg({"ID": "count", "LITROS": "sum", "VALOR_TOTAL": "sum"}).reset_index()
            df_postos.columns = ["Posto", "Vezes", "Litros", "Gasto"]
            df_postos = df_postos.sort_values("Vezes", ascending=False)

            fig4 = px.bar(
                df_postos,
                x="Posto",
                y="Vezes",
                title="Frequência de uso por posto",
                text="Vezes",
                color="Vezes",
                color_continuous_scale="Viridis",
            )
            fig4.update_traces(textposition="outside")
            fig4.update_xaxes(tickangle=-45)
            st.plotly_chart(fig4, width="stretch")

    # ========== INSIGHTS ==========
    render_insights(insights_motorista(df_mot))

else:
    st.warning("⚠️ Nenhum dado disponível.")
