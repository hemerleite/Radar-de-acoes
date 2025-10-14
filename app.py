import streamlit as st
import pandas as pd
import os

st.set_page_config("Radar de ações", layout="wide")
st.title("🔎 Radar de ações — recomendações extraídas automaticamente")

st.markdown("""
Este painel mostra recomendações extraídas automaticamente de fontes confiáveis (via RSS).
- O crawler é `buscar_recomendacoes.py` e salva em `recomendacoes.csv`.
- O script `avaliar_performance.py` avalia se targets/stops foram atingidos usando yfinance.
""")

CSV = "recomendacoes.csv"
CSV_AV = "recomendacoes_avaliadas.csv"

if not os.path.exists(CSV):
    st.warning("Ainda não há recomendações. Rode o crawler (ver README) ou aguarde o GitHub Actions.")
else:
    df = pd.read_csv(CSV)
    st.subheader("Recomendações extraídas (últimas)")
    display_cols = ["extraido_em","data_publicacao","fonte","ticker","tipo","entrada","alvos","stops","horizonte","titulo"]
    cols_available = [c for c in display_cols if c in df.columns]
    st.dataframe(df[cols_available].sort_values(by="extraido_em", ascending=False).reset_index(drop=True), height=420)

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("Rodar avaliação (executa avaliar_performance.py)"):
        st.info("Rodando avaliação... isto pode demorar alguns segundos dependendo do número de recomendações.")
        try:
            import avaliar_performance as ap
            ap.main()
            st.success("Avaliação concluída. Veja arquivo recomendacoes_avaliadas.csv")
        except Exception as e:
            st.error(f"Erro ao rodar avaliação: {e}")

with col2:
    if os.path.exists(CSV_AV):
        st.success("Arquivo de avaliação encontrado.")
        dfav = pd.read_csv(CSV_AV)
        st.subheader("Resultados da avaliação")
        show_cols = ["extraido_em","data_publicacao","fonte","ticker","tipo","status","data_ocorrencia","dias","retorno"]
        cols_ok = [c for c in show_cols if c in dfav.columns]
        st.dataframe(dfav[cols_ok].sort_values(by="extraido_em", ascending=False).reset_index(drop=True), height=420)
    else:
        st.info("Nenhuma avaliação rodada ainda.")

st.markdown("---")
st.caption("As informações são agregadas automaticamente de fontes públicas e NÃO constituem recomendação de investimento.")
