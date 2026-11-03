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
  "Qual foi o objetivo da dissertação de Samuel Santana de Almeida (Análise exploratória e prática da aplicação de NER em notícias sobre saúde) e quais modelos de Deep Learning baseados em Transformers foram comparados em seus experimentos?",
  "Qual metodologia e tipo de rede o autor Jean Louis Silva Santos utilizou para gerar dados sintéticos voltados ao apoio à decisão na alta segura neonatal sem expor registros médicos reais?",
  "Na dissertação de Douglas Costa Braga sobre classificação de células leucêmicas, qual arquitetura atingiu o maior F1-Score (97,89%) e qual a relevância constatada sobre mecanismos de ateção por canal?",
  "Na pesquisa desenvolvida por João Alysson dos Santos Guimarães, quais métodos e algoritmos foram propostos para a tarefa de resumo automático de textos para auxílio na auditoria do SUS?",
  "O trabalho de Denisson Santos Alves Freitas propôs um framework para conformidade contínua com a LGPD. Qual tecnologia/protocolo de análise estática de código foi utilizado em pipelines DevSecOps nessa solução?",
  "Quais ferramentas e metodologias foram desenvolvidas por Waldson Rodrigues Cardoso na dissertação \"APSEA\" para atuar na conscientização e prevenção contra ataques de engenharia social?",
  "Como a ferramenta Galactus Snitch, proposta por Luan Bruno Barbosa de Souza Costa, atua na identificação de riscos de fraudes (red flags) em contratos públicos no âmbito do GAECO/MPSE?",
  "Qual a abordagem metodológica proposta por Laramy de Oliveira Carvalho para fazer a \"ponte entre a lei e o código\", visando padronizar os Registros Eletrônicos de Dados Governamentais (REDG)?",
  "Na dissertação de Andre Reges Souza Meira, qual a principal constatação sobre o gap entre as arquiteturas de conjunto de instruções (ISA) ARM e RISC-V quando aplicadas a IA e robótica?",
  "Qual combinação de protocolo da camada de aplicação e tipo de rede móvel apresentou o melhor desempenho para ultrapassagens seguras na pesquisa de Sandro Andrade Monteiro Menezes?",
  "Ao analisar os protocolos IoT (MQTT e CoAP) em redes de satélites, quais duas órbitas (e provedores) foram avaliadas no estudo experimental de Rodrigo Cavalcante Faria?",
  "Qual foi a ferramenta/plataforma desenvolvida por Camila Patrícia Cardoso dos Santos para monitoramento da mortalidade materna alinhada aos Objetivos de Desenvolvimento Sustentável (ODS)?",
  "O framework ISAA, proposto por Gustavo dos Santos Melo, foi baseado em qual cláusula da norma ISO/IEC/IEEE 42020:2019 e em qual método clássico de avaliação de arquiteturas (ATAM)?",
  "Na pesquisa de Diego de Jesus Santos, como a linguagem SysML foi avaliada e combinada com a UML para a engenharia de sistemas complexos no domínio automotivo?",
  "Qual foi o foco e a proposta de modelo conceitual desenvolvido por Marcos Venícius Santos para estimativa de custos de desenvolvimento de software em Pequenas e Médias Empresas (PMEs)?",
  "Qual técnica visual de alinhamento de requisitos e domínio de negócio foi estudada por Marcos Cesar Barbosa dos Santos em suas guidelines para a adoção de microsserviços?",
  "Quais foram os principais efeitos e recursos (como RAM) afetados pelo envelhecimento de software (software aging) identificados por Paulo do Amaral Costa ao estressar seis SGBDs (relacionais e NoSQL)?",
  "Na dissertação de Cristiano Lima Oliveira sobre reconhecedores automáticos de placas veiculares, como a escolha de funções de perda perceptuais (ex: VGG Loss vs. OCR Loss) influenciou a super-resolução sob degradações sintéticas?",
  "De acordo com os experimentos de Antonio Carlos Sousa utilizando Knative, qual combinação de sistema operacional e plataforma de contêineres (Ubuntu, Debian, Docker, Podman) apresentou o melhor desempenho e eficiência?",
  "Qual foi o método de reamostragem avaliado por Jesy Karolayne Sales dos Santos para a correção de viés na estimação de parâmetros de modelos de regressão Dirichlet aplicados a dados composicionais?"
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
