#!/usr/bin/env python3
"""
buscar_recomendacoes.py
MVP crawler que lê feeds RSS/sitemaps de sites financeiros (whitelist),
baixa os artigos mais recentes, aplica regex/heurísticas para extrair:
- ticker (ex: PETR4)
- tipo (compra / venda)
- preco_entrada
- alvos (lista)
- stops (lista)
- horizonte (day / swing / positional)

Salva em recomendacoes.csv
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import os
import time
import uuid

# Config
CSV_FILE = "recomendacoes.csv"
WHITELIST_FEEDS = [
    "https://www.infomoney.com.br/feed/",
    "https://suno.com.br/feed/",
    "https://br.investing.com/rss/news.rss",
    "https://valor.globo.com/empresas/feed/",
    "https://www.investidor10.com.br/feed/",
    "https://www.btgpactual.com/pt-br/rss/feed",  # example, may vary
    "https://www.xpi.com.br/feed/",
    # Adicione/ajuste feeds conforme necessidade
]

RE_TICKER = re.compile(r"\b([A-Z]{3,5}\d?)\b")
RE_R_BRL = re.compile(r"R\$ ?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)")
RE_ALVO = re.compile(r"(preço[-\s]?alvo|alvo|meta)[:\s]*R\$ ?(\d{1,3}(?:[.,]\d{1,2})?)", re.IGNORECASE)
RE_STOP = re.compile(r"(stop(?:[-\s]?loss)?|stop[-\s]?loss)[:\s]*R\$ ?(\d{1,3}(?:[.,]\d{1,2})?)", re.IGNORECASE)
RE_ENTRADA = re.compile(r"(entrada|preço de entrada|entry)[:\s]*R\$ ?(\d{1,3}(?:[.,]\d{1,2})?)", re.IGNORECASE)
RE_COMPRA = re.compile(r"\b(compra|comprar|buy)\b", re.IGNORECASE)
RE_VENDA = re.compile(r"\b(venda|vender|sell)\b", re.IGNORECASE)
RE_DAY = re.compile(r"\b(day[-\s]?trade|intradiar|intradiário|intraday)\b", re.IGNORECASE)
RE_SWING = re.compile(r"\b(swing[-\s]?trade|swing)\b", re.IGNORECASE)

def parse_brl_number(s):
    if s is None:
        return None
    s = str(s).strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except:
        return None

def extract_from_text(text):
    result = {
        "ticker": None,
        "tipo": None,
        "entrada": None,
        "alvos": [],
        "stops": [],
        "horizonte": None,
        "snippet": text[:500]
    }

    alvo_matches = RE_ALVO.findall(text)
    for m in alvo_matches:
        val = parse_brl_number(m[1])
        if val:
            result["alvos"].append(val)

    stop_matches = RE_STOP.findall(text)
    for m in stop_matches:
        val = parse_brl_number(m[1])
        if val:
            result["stops"].append(val)

    entrada_matches = RE_ENTRADA.findall(text)
    for m in entrada_matches:
        val = parse_brl_number(m[1])
        if val:
            result["entrada"] = val
            break

    if not result["alvos"]:
        rbrl = RE_R_BRL.findall(text)
        if rbrl:
            cand = parse_brl_number(rbrl[0])
            if cand and result["entrada"] is None:
                result["alvos"].append(cand)

    if RE_COMPRA.search(text):
        result["tipo"] = "compra"
    elif RE_VENDA.search(text):
        result["tipo"] = "venda"

    if RE_DAY.search(text):
        result["horizonte"] = "day"
    elif RE_SWING.search(text):
        result["horizonte"] = "swing"
    else:
        result["horizonte"] = "positional"

    windows = []
    for m in re.finditer(r"(alvo|stop|entrada|preço-alvo|stop loss|recomenda)", text, flags=re.IGNORECASE):
        start = max(0, m.start()-80)
        end = min(len(text), m.end()+80)
        windows.append(text[start:end])

    candidate_tickers = set()
    for w in windows:
        for t in RE_TICKER.findall(w):
            if re.search(r"\d", t):
                candidate_tickers.add(t.strip())

    if not candidate_tickers:
        for t in RE_TICKER.findall(text[:300]):
            if re.search(r"\d", t):
                candidate_tickers.add(t.strip())

    if candidate_tickers:
        chosen = sorted(candidate_tickers, key=lambda x: (len(x), x))[-1]
        result["ticker"] = chosen

    return result

def fetch_article_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; RecoBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "lxml")
        article = soup.find("article")
        if article:
            texts = [p.get_text(" ", strip=True) for p in article.find_all("p")]
            content = "\n".join(texts)
        else:
            ps = soup.find_all("p")
            content = "\n".join([p.get_text(" ", strip=True) for p in ps])
        return content.strip()
    except Exception as e:
        print("Erro fetch:", e)
        return None

def load_existing_csv():
    if os.path.exists(CSV_FILE):
        try:
            return pd.read_csv(CSV_FILE, dtype=str)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_df(df):
    df.to_csv(CSV_FILE, index=False)

def main():
    existing = load_existing_csv()
    seen_urls = set(existing.get("url", []))
    rows = []

    for feed in WHITELIST_FEEDS:
        print("Lendo feed:", feed)
        try:
            feeddata = feedparser.parse(feed)
        except Exception as e:
            print("Erro lendo feed", feed, e)
            continue

        for entry in (feeddata.entries or [])[:40]:
            url = entry.get("link") or entry.get("id")
            if not url:
                continue
            if url in seen_urls:
                continue

            title = entry.get("title", "")
            published = entry.get("published", entry.get("updated", "")) or ""
            try:
                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    published = datetime(*published_parsed[:6]).isoformat()
            except:
                pass

            print("Processando:", title)
            text = fetch_article_text(url)
            if not text or len(text) < 80:
                print("Sem texto útil:", url)
                continue

            extracted = extract_from_text(title + "\n" + text[:3000])
            if not extracted.get("ticker") and not extracted.get("alvos") and not extracted.get("stops"):
                print("Sem campos úteis extraídos (pular).")
                continue

            row = {
                "id": str(uuid.uuid4()),
                "fonte": requests.utils.urlparse(url).netloc,
                "url": url,
                "titulo": title,
                "data_publicacao": published,
                "ticker": extracted.get("ticker"),
                "tipo": extracted.get("tipo"),
                "entrada": extracted.get("entrada"),
                "alvos": "|".join([str(x) for x in extracted.get("alvos")]) if extracted.get("alvos") else "",
                "stops": "|".join([str(x) for x in extracted.get("stops")]) if extracted.get("stops") else "",
                "horizonte": extracted.get("horizonte"),
                "snippet": extracted.get("snippet"),
                "extraido_em": datetime.utcnow().isoformat()
            }
            rows.append(row)
            seen_urls.add(url)
            time.sleep(1.2)

    if rows:
        df_new = pd.DataFrame(rows)
        df_all = pd.concat([existing, df_new], ignore_index=True, sort=False)
        save_df(df_all)
        print(f"{len(rows)} novas recomendações salvas em {CSV_FILE}. Total: {len(df_all)}")
    else:
        print("Nenhuma nova recomendação encontrada.")

if __name__ == "__main__":
    main()
