import requests
from bs4 import BeautifulSoup
import pandas as pd
import fitz  # PyMuPDF
from tqdm import tqdm

# URLs principais
URL_BASE = "https://guaratingueta.camarasempapel.com.br"
URL_CONSULTA = f"{URL_BASE}/consulta-producao.aspx?autor=214"

# Função para extrair os links dos processos
def extrair_links_processo():
    response = requests.get(URL_CONSULTA)
    soup = BeautifulSoup(response.content, "lxml")

    tabela = soup.find("table", {"id": "conteudo_gdvConsultaProducao"})
    linhas = tabela.find_all("tr")[1:]  # Pula o cabeçalho

    dados = []
    for linha in tqdm(linhas, desc="Extraindo dados"):
        colunas = linha.find_all("td")
        titulo = colunas[1].get_text(strip=True)
        data = colunas[2].get_text(strip=True)

        links = colunas[3].find_all("a")
        link_processo = None
        link_pdf = None
        respondido = "Não Respondido"

        for link in links:
            href = link.get("href")
            texto = link.get_text(strip=True).lower()
            if "processo.aspx" in href:
                link_processo = f"{URL_BASE}/{href}"
            elif "visualizar-proposicao" in href and "ofício resposta" in texto:
                respondido = "Respondido"
            elif "visualizar-proposicao" in href and "ofício resposta" not in texto:
                link_pdf = f"{URL_BASE}/{href}"

        bairro = extrair_bairro_do_pdf(link_pdf) if link_pdf else ""

        dados.append({
            "Título": titulo,
            "Data": data,
            "Link do Processo": link_processo,
            "Respondido": respondido,
            "Bairro": bairro
        })

    return pd.DataFrame(dados)

# Função para extrair o nome do bairro de um PDF
def extrair_bairro_do_pdf(url_pdf):
    try:
        resposta = requests.get(url_pdf)
        with fitz.open(stream=resposta.content, filetype="pdf") as doc:
            texto = ""
            for pagina in doc:
                texto += pagina.get_text()

            for linha in texto.splitlines():
                if "bairro" in linha.lower():
                    return linha.strip()
        return ""
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return ""

# Executa o scraper
if __name__ == "__main__":
    df_final = extrair_links_processo()
    df_final.to_csv("tabela_legislativa.csv", index=False)
    print("✅ Tabela gerada com sucesso: tabela_legislativa.csv")

