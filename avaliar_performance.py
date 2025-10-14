#!/usr/bin/env python3
"""
avaliar_performance.py
Lê recomendacoes.csv e avalia se targets / stops foram atingidos nas janelas definidas.
Produz recomendacoes_avaliadas.csv com colunas extras: status, data_ocorrencia, dias, retorno
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import os

INPUT = "recomendacoes.csv"
OUTPUT = "recomendacoes_avaliadas.csv"
OBS_DAYS = 180

def parse_list_field(val):
    if pd.isna(val) or not val:
        return []
    try:
        return [float(x) for x in str(val).split("|") if x.strip()]
    except:
        return []

def fetch_prices(ticker, start, end):
    try:
        df = yf.download(ticker, start=start.strftime("%Y-%m-%d"), end=(end+timedelta(days=1)).strftime("%Y-%m-%d"), progress=False)
        if df.empty:
            return None
        df = df[['Open','High','Low','Close']].copy()
        df.index = pd.to_datetime(df.index).date
        return df
    except Exception as e:
        print("Erro yfinance:", e)
        return None

def evaluate_row(row):
    try:
        pub = row.get("data_publicacao")
        if not pub or pd.isna(pub):
            pub_date = datetime.utcnow().date()
        else:
            pub_date = pd.to_datetime(pub).date()

        yf_t = row.get("ticker")
        if not yf_t:
            return {"status":"no_ticker"}
        yf_t = yf_t.strip().upper()
        if not yf_t.endswith(".SA") and any(ch.isdigit() for ch in yf_t):
            yf_t = yf_t + ".SA"

        start = pub_date
        end = pub_date + timedelta(days=OBS_DAYS)
        prices = fetch_prices(yf_t, start, end)
        if prices is None:
            return {"status":"no_data"}

        entry_price = None
        if pd.notna(row.get("entrada")) and row.get("entrada") != "":
            entry_price = float(row.get("entrada"))
        else:
            possible = [d for d in prices.index if d >= pub_date]
            if possible:
                entry_price = float(prices.loc[min(possible),'Close'])
            else:
                entry_price = float(prices['Close'].iloc[0])

        alvos = parse_list_field(row.get("alvos",""))
        stops = parse_list_field(row.get("stops",""))
        tipo = str(row.get("tipo","compra")).lower()

        for d in sorted([d for d in prices.index if d >= pub_date]):
            high = float(prices.loc[d,'High'])
            low = float(prices.loc[d,'Low'])
            if tipo == "compra" or tipo=="":
                if alvos:
                    for a in alvos:
                        if high >= a:
                            retorno = (a / entry_price - 1) * 100
                            return {"status":"hit_alvo","data_ocorrencia":d.isoformat(),"dias":(d - pub_date).days,"retorno":retorno}
                if stops:
                    for s in stops:
                        if low <= s:
                            retorno = (s / entry_price - 1) * 100
                            return {"status":"hit_stop","data_ocorrencia":d.isoformat(),"dias":(d - pub_date).days,"retorno":retorno}
            else:
                if alvos:
                    for a in alvos:
                        if low <= a:
                            retorno = (entry_price / a - 1) * 100
                            return {"status":"hit_alvo","data_ocorrencia":d.isoformat(),"dias":(d - pub_date).days,"retorno":retorno}
                if stops:
                    for s in stops:
                        if high >= s:
                            retorno = (entry_price / s - 1) * 100
                            return {"status":"hit_stop","data_ocorrencia":d.isoformat(),"dias":(d - pub_date).days,"retorno":retorno}
        last_date = max(d for d in prices.index if d >= pub_date)
        last_price = float(prices.loc[last_date,'Close'])
        if tipo == "compra" or tipo=="":
            retorno = (last_price / entry_price - 1) * 100
        else:
            retorno = (entry_price / last_price - 1) * 100
        return {"status":"expirada","data_ocorrencia":last_date.isoformat(),"dias":(last_date - pub_date).days,"retorno":retorno}
    except Exception as e:
        return {"status":"error","error":str(e)}

def main():
    if not os.path.exists(INPUT):
        print("Arquivo não encontrado:", INPUT)
        return
    df = pd.read_csv(INPUT, dtype=str)
    results = []
    for _, row in df.iterrows():
        res = evaluate_row(row)
        results.append(res if res else {"status":"no_eval"})
    df_results = pd.DataFrame(results)
    out = pd.concat([df.reset_index(drop=True), df_results.reset_index(drop=True)], axis=1)
    out.to_csv(OUTPUT, index=False)
    print("Avaliação salva em", OUTPUT)

if __name__ == "__main__":
    main()
