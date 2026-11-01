import json
import chromadb
from chromadb.utils import embedding_functions

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
 
try:
    chroma_client.delete_collection(name="producoes_dcomp_ufs")
except Exception:
    pass

collection = chroma_client.create_collection(
    name="producoes_dcomp_ufs",
    embedding_function=ef
)

with open('dissertacoes_mcc_limpo.json', 'r', encoding='utf-8') as f:
    publicacoes = json.load(f)

documents, metadatas, ids = [], [], []

for idx, pub in enumerate(publicacoes):
    autores = pub.get("authors", "")
    titulo = pub.get("titulo", "")
    resumo = pub.get("resumo", "")
    keywords = ", ".join(pub.get("keywords", [])) if isinstance(pub.get("keywords"), list) else pub.get("keywords", "")
 
    texto_vetor = f"Título: {titulo}\nAutor(es): {autores}\nPalavras-Chave: {keywords}\nResumo: {resumo}"
    
    if not titulo and not resumo:
        continue

    documents.append(texto_vetor)
    metadatas.append({
        "type": pub.get("type", "Dissertação"),
        "title": titulo,
        "authors": autores,
        "issue_date": pub.get("issue_date", ""),
        "resumo": resumo,
        "keywords": keywords,
        "citation": pub.get("citation", ""),
        "link": pub.get("link", "")
    })
    ids.append(f"doc_{idx}")

collection.add(documents=documents, metadatas=metadatas, ids=ids)
print(f"Banco populado com sucesso! Total de itens: {collection.count()}")