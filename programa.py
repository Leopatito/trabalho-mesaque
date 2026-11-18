from typing import TypedDict, Literal
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

if not os.getenv("OPENROUTER_API_KEY"):
    raise RuntimeError(
        "OPENROUTER_API_KEY não configurada. Crie um arquivo .env com: OPENROUTER_API_KEY=sua_chave"
    )

# 1. Definição do Estado (State Store)
class TicketState(TypedDict):
    ticket_texto: str
    categoria: str          # 'bug' ou 'feature'
    resposta_rascunho: str
    aprovado_por_humano: bool

# Configuração do LLM (OpenRouter)
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# 2. Nós / Agentes (Agents)

def triage_agent(state: TicketState):
    """Agente de Roteamento: Decide o destino baseado na ambiguidade do texto."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "És um classificador de tickets. Responde APENAS com 'bug' ou 'feature'."),
        ("user", "{ticket}")
    ])
    chain = prompt | llm
    resultado = chain.invoke({"ticket": state["ticket_texto"]}).content.strip().lower()
    
    # Fallback determinístico (Guardrail de saída)
    categoria = resultado if resultado in ["bug", "feature"] else "feature"
    return {"categoria": categoria}

def bug_agent(state: TicketState):
    """Especialista A: Lida com defeitos técnicos."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "És um engenheiro de suporte técnico. Escreve um rascunho de resposta pedindo logs de erro e passos para reproduzir o problema."),
        ("user", "{ticket}")
    ])
    chain = prompt | llm
    resposta = chain.invoke({"ticket": state["ticket_texto"]}).content
    return {"resposta_rascunho": resposta}

def feature_agent(state: TicketState):
    """Especialista B: Refina requisitos."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "És um Product Manager. Escreve um rascunho agradecendo a sugestão e fazendo 2 perguntas para refinar o requisito de negócio."),
        ("user", "{ticket}")
    ])
    chain = prompt | llm
    resposta = chain.invoke({"ticket": state["ticket_texto"]}).content
    return {"resposta_rascunho": resposta}

def human_review(state: TicketState):
    """Guardrail L2 (Slide 26): Aprovação antes do envio."""
    print("\n--- REVISÃO HUMANA NECESSÁRIA ---")
    print(f"Categoria identificada: {state['categoria'].upper()}")
    print(f"Rascunho do Agente:\n{state['resposta_rascunho']}")
    
    # Em produção, isto pausaria a execução (interrupt_before) para um endpoint de API.
    # Aqui simulamos o input do terminal.
    aprovacao = input("\nAprovar envio ao cliente? (s/n): ").strip().lower()
    
    return {"aprovado_por_humano": aprovacao == 's'}

# 3. Orquestração e Lógica de Roteamento (Orchestrator)

def route_triage(state: TicketState) -> Literal["bug_agent", "feature_agent"]:
    """Lê o estado e decide o próximo nó dinamicamente."""
    if state["categoria"] == "bug":
        return "bug_agent"
    return "feature_agent"

# 4. Construção do Grafo (Arquitetura)

workflow = StateGraph(TicketState)

# Adiciona os nós
workflow.add_node("triage", triage_agent)
workflow.add_node("bug_agent", bug_agent)
workflow.add_node("feature_agent", feature_agent)
workflow.add_node("human_review", human_review)

# Define as arestas e o fluxo
workflow.set_entry_point("triage")

# O roteamento condicional tira o controlo fixo do código e baseia-se na decisão do LLM
workflow.add_conditional_edges("triage", route_triage)

# Independentemente de quem processa, converge para a revisão humana
workflow.add_edge("bug_agent", "human_review")
workflow.add_edge("feature_agent", "human_review")
workflow.add_edge("human_review", END)

# Compila a aplicação agentic
app = workflow.compile()

# --- TESTE DE EXECUÇÃO (Trace e Observabilidade) ---
if __name__ == "__main__":
    ticket_teste = "boa tarde, eu queria que o sistema adicionasse mais uma forma de fazer filtro, já que não estou conseguindo me confortar com esse atual"
    
    estado_inicial = {
        "ticket_texto": ticket_teste,
        "categoria": "",
        "resposta_rascunho": "",
        "aprovado_por_humano": False
    }
    
    print("Iniciando processamento Agentic...\n")
    # O stream permite criar logs/traces de cada etapa (Slide 27)
    for evento in app.stream(estado_inicial):
        for node_name, node_state in evento.items():
            print(f"-> Nó executado: {node_name}")
            
    print("\nExecução finalizada.")