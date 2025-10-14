"""
extrair_nlp.py
Módulo opcional que usa uma API de LLM (Hugging Face ou OpenAI) para extrair campos quando regex falhar.
Este arquivo está configurado como exemplo; usar exige chave de API e possivelmente adaptar o modelo.
"""

import os
import requests
import json

HF_API = os.environ.get("HF_API_TOKEN")  # opcional

def call_hf_extract(text):
    if not HF_API:
        raise RuntimeError("HF_API_TOKEN não definido")
    url = "https://api-inference.huggingface.co/models/bigscience/bloom"  # ajustar modelo
    headers = {"Authorization": f"Bearer {HF_API}"}
    prompt = f"""
    Extraia em JSON os seguintes campos do texto: ticker, tipo (compra/venda), entrada, alvos (lista), stops (lista), horizonte (day/swing/positional).
    Texto:
    {text}

    Responda apenas com JSON:
    {{
      "ticker": "...",
      "tipo": "...",
      "entrada": 0.0,
      "alvos": [0.0],
      "stops": [0.0],
      "horizonte": "..."
    }}
    """
    data = {"inputs": prompt, "options": {"wait_for_model": True}}
    r = requests.post(url, headers=headers, json=data, timeout=60)
    return r.json()

if __name__ == "__main__":
    sample = "Analistas recomendam COMPRA de PETR4 com preço-alvo de R$ 45,00 e stop loss em R$ 38,00 — indicado para swing trade."
    print(call_hf_extract(sample))
