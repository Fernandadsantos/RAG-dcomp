import chromadb
from chromadb.utils import embedding_functions

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="producoes_dcomp_ufs", embedding_function=ef)

def buscar_contexto_rag(query, n_results=3):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    
    contexto_formatado = "\n\n---\n\n".join(docs)
    return contexto_formatado, metas