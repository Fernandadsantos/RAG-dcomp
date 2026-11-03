import time
import json
import csv
import os
from langchain_groq import ChatGroq
from retriever import buscar_contexto_rag
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("API_KEY")

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="openai/gpt-oss-120b", 
    temperature=0.1
)
 
PERGUNTAS = [
    "Qual foi o objetivo da dissertação entitulada 'Análise exploratória e prática da aplicação de NER em notícias sobre saúde' de Samuel Santana de Almeida ",
    "Quantas arquiteturas foram comparadas na dissertação entitulada 'Análise comparativa de arquiteturas de Deep Learning para classificação de células leucêmicas' de Douglas Costa Braga",
    "A dissertação entitulada 'Framework para conformidade contínua com a LGPD: uma implementação com language server protocol em pipelines DevSecOps' de Denisson Santos Alves Freitas teve como objetivo desenvolver e validar o que?"
]

def rodar_benchmark():
    relatorio_experimento = []

    for idx, pergunta in enumerate(PERGUNTAS, 1):
        print(f"\n==========================================")
        print(f" PERGUNTA {idx}: {pergunta}")
        print(f"==========================================")
 
        prompt_sem_rag = f"Responda à seguinte pergunta de forma direta e factual em Português:\n{pergunta}"
        
        inicio_a = time.perf_counter()
        resposta_sem_rag = llm.invoke(prompt_sem_rag).content
        tempo_sem_rag = time.perf_counter() - inicio_a

        print(f"\n--- [Cenário A: Sem RAG] ---")
        print(f"Tempo: {tempo_sem_rag:.2f}s")
        print(f"Resposta:\n{resposta_sem_rag}\n")
 
        inicio_retrieval = time.perf_counter()
        contexto, fontes = buscar_contexto_rag(pergunta, n_results=3)
        tempo_retrieval = time.perf_counter() - inicio_retrieval

        prompt_com_rag = f"""Você é um assistente acadêmico do DCOMP/UFS.
Use APENAS o contexto fornecido abaixo para responder à pergunta.
Se a informação não estiver presente no contexto, responda estritamente: "A informação não está disponível nos dados recuperados." Não invente nada.

CONTEXTO RECUPERADO:
{contexto}

PERGUNTA:
{pergunta}
"""

        inicio_b = time.perf_counter()
        resposta_com_rag = llm.invoke(prompt_com_rag).content
        tempo_llm_rag = time.perf_counter() - inicio_b
        tempo_total_rag = tempo_retrieval + tempo_llm_rag

        print(f"--- [Cenário B: Com RAG] ---")
        print(f"Tempo de Busca no Banco: {tempo_retrieval:.3f}s")
        print(f"Tempo da LLM: {tempo_llm_rag:.2f}s")
        print(f"Tempo Total RAG: {tempo_total_rag:.2f}s")
        print(f"Resposta:\n{resposta_com_rag}\n")

        titulos_fontes = [f.get('title', '') for f in fontes]

        relatorio_experimento.append({
            "id": idx,
            "pergunta": pergunta,
            "sem_rag": {
                "resposta": resposta_sem_rag,
                "tempo_segundos": round(tempo_sem_rag, 2)
            },
            "com_rag": {
                "resposta": resposta_com_rag,
                "tempo_retrieval_segundos": round(tempo_retrieval, 3),
                "tempo_llm_segundos": round(tempo_llm_rag, 2),
                "tempo_total_segundos": round(tempo_total_rag, 2),
                "fontes_usadas": titulos_fontes
            }
        })
 
    with open("resultado_benchmark_rag.json", "w", encoding="utf-8") as f:
        json.dump(relatorio_experimento, f, ensure_ascii=False, indent=2)

    with open("resultado_benchmark_rag.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Pergunta", 
            "Tempo_Sem_RAG(s)", "Resposta_Sem_RAG", 
            "Tempo_Retrieval(s)", "Tempo_LLM_RAG(s)", "Tempo_Total_RAG(s)", 
            "Resposta_Com_RAG", "Fontes_Recuperadas"
        ])
        for row in relatorio_experimento:
            writer.writerow([
                row["id"],
                row["pergunta"],
                row["sem_rag"]["tempo_segundos"],
                row["sem_rag"]["resposta"].replace("\n", " "),
                row["com_rag"]["tempo_retrieval_segundos"],
                row["com_rag"]["tempo_llm_segundos"],
                row["com_rag"]["tempo_total_segundos"],
                row["com_rag"]["resposta"].replace("\n", " "),
                " | ".join(row["com_rag"]["fontes_usadas"])
            ])

    print("\n Experimento concluído! Resultados salvos em 'resultado_benchmark_rag.json' e 'resultado_benchmark_rag.csv'.")

if __name__ == "__main__":
    rodar_benchmark()
