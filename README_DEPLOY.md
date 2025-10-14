# Radar de ações — MVP (deploy simples)

Este repositório contém um MVP que encontra automaticamente recomendações de compra/venda de ações
em sites conceituados (via RSS), extrai preço de entrada, preço-alvo, stop e horizonte (day/swing/positional)
e avalia performance usando yfinance.

## Passo a passo (para iniciantes)

1. Crie conta no GitHub: https://github.com/join
2. Crie um novo repositório (por exemplo: `radar-de-acoes`) e faça upload dos arquivos deste pacote.
   - Se não souber git, use a interface do GitHub: _Add file → Upload files_ e envie todos os arquivos do pacote.
3. No repositório, vá em **Actions** → verá o workflow **schedule-crawler**. Você pode executar manualmente ("Run workflow")
   ou esperar a execução agendada (a cada 4 horas).
4. Para publicar o site:
   - Acesse https://streamlit.io/cloud e faça login com GitHub ("Sign in with GitHub").
   - Clique em **New app** → escolha este repositório → Branch: main → File: `app.py` → Deploy.
5. O Streamlit instalará dependências e publicará a página. URL pública gratuita do tipo: `https://<seu-usuario>.streamlit.app`.
6. Para ajustar fontes (feeds RSS), edite `WHITELIST_FEEDS` em `buscar_recomendacoes.py` e faça commit.
7. Para extração mais precisa, habilite `extrair_nlp.py` e configure uma chave de API (Hugging Face ou OpenAI) e ajuste o crawler para invocar esse módulo quando regex falhar.

## Observações importantes
- O sistema agrega links e trechos públicos; **não copie textos inteiros** sem permissão.
- Sempre inclua o disclaimer no site (já incluído no `app.py`).
- Respeite termos de uso dos sites e `robots.txt`. Use feeds/sitemaps preferencialmente.
