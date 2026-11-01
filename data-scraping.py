import json
import re
import time
import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ri.ufs.br"
COLLECTION_URL = f"{BASE_URL}/handle/riufs/2491/browse?type=dateissued&sort_by=2&order=DESC&rpp=20&offset="
ARQUIVO_SAIDA = "dissertacoes_mcc_limpo.json"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def carregar_dados_existentes(): 
    if os.path.exists(ARQUIVO_SAIDA):
        try:
            with open(ARQUIVO_SAIDA, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salvar_dados(dados): 
    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def fazer_requisicao_com_retry(url, max_tentativas=5, espera_base=2): 
    for tentativa in range(1, max_tentativas + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                return resp
            elif resp.status_code in [503, 429, 500, 502]:
                tempo_espera = espera_base ** tentativa
                print(f"    [HTTP {resp.status_code}] Servidor sobrecarregado. Aguardando {tempo_espera}s (Tentativa {tentativa}/{max_tentativas})...")
                time.sleep(tempo_espera)
            else:
                print(f"    [HTTP {resp.status_code}] Falha na requisição.")
                return None
        except requests.exceptions.RequestException as e:
            tempo_espera = espera_base ** tentativa
            print(f"    [Erro de Conexão] {e}. Aguardando {tempo_espera}s...")
            time.sleep(tempo_espera)
    return None

def extrair_detalhes_item(item_url): 
    resp = fazer_requisicao_com_retry(item_url)
    if not resp:
        return {}
    
    soup = BeautifulSoup(resp.text, 'html.parser')
     
    resumo = ""
    meta_abstract = soup.find('meta', attrs={'name': re.compile(r'^(DCTERMS\.abstract|DC\.description)$', re.I)})
    if meta_abstract and meta_abstract.get('content'):
        resumo = meta_abstract['content'].strip()
    
    if not resumo:
        abstract_elem = (
            soup.find('td', class_='dc_description_abstract') or
            soup.find('div', class_='simple-item-view-description') or
            soup.find('div', class_='item-page-field-wrapper-description')
        )
        if abstract_elem:
            resumo = abstract_elem.text.strip()

    if not resumo:
        for div in soup.find_all(['div', 'td', 'p']):
            texto_div = div.text.strip()
            if texto_div.startswith("Resumo:") or texto_div.startswith("Abstract:"):
                resumo = texto_div
                break

    if resumo:
        resumo = re.sub(r'^(Resumo|Abstract):\s*', '', resumo, flags=re.I).strip()
 
    autores_list = []
    meta_authors = soup.find_all('meta', attrs={'name': re.compile(r'^(DC\.creator|DCTERMS\.creator|DC\.contributor\.author)$', re.I)})
    for m in meta_authors:
        if m.get('content'):
            autores_list.append(m['content'].strip())
    
    autores = "; ".join(autores_list) if autores_list else ""
    
    if not autores:
        authors_elem = soup.find('td', class_='dc_contributor_author') or soup.find('div', class_='simple-item-view-authors')
        if authors_elem:
            autores = re.sub(r'^Authors?:\s*', '', authors_elem.text.strip(), flags=re.I)
 
    issue_date = ""
    meta_date = soup.find('meta', attrs={'name': re.compile(r'^(DC\.date|DCTERMS\.issued|DC\.date\.issued)$', re.I)})
    if meta_date and meta_date.get('content'):
        issue_date = meta_date['content'].strip()
        
    if not issue_date:
        date_elem = soup.find('td', class_='dc_date_issued') or soup.find('div', class_='simple-item-view-date')
        if date_elem:
            issue_date = re.sub(r'^Issue Date:\s*|^Data:\s*', '', date_elem.text.strip(), flags=re.I)
 
    keywords = []
    meta_subjects = soup.find_all('meta', attrs={'name': re.compile(r'^(DC\.subject|DCTERMS\.subject)$', re.I)})
    for m in meta_subjects:
        if m.get('content'):
            keywords.append(m['content'].strip())
            
    if not keywords:
        keywords_elem = soup.find('td', class_='dc_subject') or soup.find('div', class_='simple-item-view-keyword')
        if keywords_elem:
            raw_kw = re.sub(r'^Keywords?:\s*|^Palavras-chave:\s*', '', keywords_elem.text.strip(), flags=re.I)
            keywords = [k.strip() for k in re.split(r'[;,]', raw_kw) if k.strip()]
 
    citation = ""
    meta_citation = soup.find('meta', attrs={'name': re.compile(r'^(DC\.identifier\.citation|DCTERMS\.bibliographicCitation)$', re.I)})
    if meta_citation and meta_citation.get('content'):
        citation = meta_citation['content'].strip()
        
    if not citation:
        citation_elem = soup.find('td', class_='dc_identifier_citation') or soup.find('div', class_='simple-item-view-citation')
        if citation_elem:
            citation = re.sub(r'^Citation:\s*', '', citation_elem.text.strip(), flags=re.I)
        else:
            citation = f"{autores}. {issue_date}. {item_url}"
 
    pdf_link = ""
    file_a = soup.find('a', href=lambda h: h and '/bitstream/' in h)
    if file_a:
        href = file_a['href']
        pdf_link = BASE_URL + href if href.startswith('/') else href

    return {
        "type": "Dissertação",
        "authors": autores,
        "issue_date": issue_date,
        "resumo": resumo,
        "keywords": keywords,
        "citation": citation,
        "pdf_url": pdf_link
    }

def link_de_producao_valida(href, texto): 
    texto_lower = texto.lower().strip()
    palavras_ignorar = [
        'next', 'previous', 'browse', 'título', 'autor', 'assunto', 
        'data', 'dissertação', 'teses e dissertações', 'biblioteca digital'
    ]
    if any(p in texto_lower for p in palavras_ignorar):
        return False

    if 'simple-search' in href or 'filterquery' in href or '_page=' in href:
        return False

    match = re.search(r'/handle/riufs/(\d+)$', href)
    if match:
        id_handle = match.group(1)
        if id_handle != '2491':
            return True

    return False

def raspar_colecao_mcc():
    dados_finais = carregar_dados_existentes()
    links_processados = {item['link'] for item in dados_finais}
    
    print(f"Iniciando coleta. Itens já coletados anteriormente: {len(links_processados)}")

    offset = 0
    rpp = 20
    pagina = 1

    while True:
        url_pagina = f"{COLLECTION_URL}{offset}"
        print(f"\n--- Lendo Página {pagina} (Offset {offset}) ---")
        
        resp = fazer_requisicao_com_retry(url_pagina)
        if not resp:
            print("Não foi possível carregar a página de listagem. Encerrando.")
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        tabela = soup.find('table', class_='ds-table') or soup.find('table')
        
        if not tabela:
            print("Fim da listagem ou estrutura de tabela não encontrada.")
            break

        novos_itens_na_pagina = 0

        for a in tabela.find_all('a', href=True):
            href = a['href']
            titulo = a.text.strip()

            if link_de_producao_valida(href, titulo):
                full_link = BASE_URL + href if href.startswith('/') else href

                if full_link in links_processados:
                    continue

                links_processados.add(full_link)
                novos_itens_na_pagina += 1

                print(f"[{len(dados_finais) + 1}] Coletando: {titulo[:60]}...")

                detalhes = extrair_detalhes_item(full_link)
                
                time.sleep(1.2)

                dados_finais.append({
                    "titulo": titulo,
                    "link": full_link,
                    "authors": detalhes.get("authors", ""),
                    "issue_date": detalhes.get("issue_date", ""),
                    "resumo": detalhes.get("resumo", ""),
                    "keywords": detalhes.get("keywords", []),
                    "citation": detalhes.get("citation", ""),
                    "pdf_url": detalhes.get("pdf_url", "")
                })

                salvar_dados(dados_finais)

        if novos_itens_na_pagina == 0 and offset > 0:
            print("Nenhuma produção inédita nesta página. Finalizando.")
            break

        offset += rpp
        pagina += 1

    print(f"\n Scraping finalizado com sucesso! Total de {len(dados_finais)} produções salvas em '{ARQUIVO_SAIDA}'.")

if __name__ == "__main__":
    raspar_colecao_mcc()