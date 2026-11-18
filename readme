# Sistema Agentic de Triagem de Suporte

**Disciplina:** Técnicas Avançadas de Desenvolvimento de Software (TADS)
**Instituição:** Universidade Federal de Mato Grosso do Sul (UFMS) - Câmpus de Três Lagoas
**Professor:** Dr. Vitor Mesaque Alves de Lima
**Autor:** Léo Taiki Tamura

## 1. Problema e Justificativa Agentic
O suporte técnico recebe diariamente dezenas de tickets em linguagem natural com diferentes graus de ambiguidade. Um fluxo determinístico (baseado em `if/else` ou palavras-chave) falha frequentemente ao classificar problemas reais face a sugestões de melhoria, gerando gargalos. 

A introdução de **Agentes de IA** justifica-se pois a decisão de roteamento exige interpretação semântica. Contudo, o envio de respostas técnicas aos clientes exige segurança, pelo que o sistema intercala a autonomia da IA na compreensão estrutural com limites rígidos de *Human-in-the-Loop* (Guardrails).

## 2. Arquitetura e Responsabilidades
O sistema utiliza o padrão **Handoff / Roteamento de Controlo**, gerido através de um grafo de estados (LangGraph).
* **Orquestrador (Triage Agent):** Recebe o ticket original, analisa a ambiguidade e toma a decisão local de roteamento. A sua única responsabilidade é ditar o fluxo (`bug` ou `feature`), sem redigir respostas.
* **Agente Especialista (Bug Agent):** Acionado exclusivamente para defeitos. Tem o contexto limitado a problemas técnicos e solicita *logs* e passos de reprodução.
* **Agente Especialista (Feature Agent):** Acionado para sugestões. Atua como Product Manager para refinar requisitos de negócio.
* **Guardrail (Human Review):** Nó de aprovação obrigatório (Nível 2 de Efeito Externo). Nenhuma resposta gerada pelos especialistas é enviada sem aprovação determinística.

## 3. Contexto, Estado e Segurança
* **Estado (State Store):** Mantém a mensagem original, a classificação atual e o rascunho em memória durante o ciclo de execução.
* **Tools/Ferramentas:** O modelo está limitado à inferência de texto e roteamento. O efeito externo (envio simulado) está protegido por um contrato explícito no nó de revisão.
* **Segurança:** Foi implementado um *fallback* determinístico. Se o Triage Agent falhar ou alucinar uma categoria fora do contrato (`bug` ou `feature`), o sistema aplica um *default* seguro para evitar erros de roteamento em cadeia.

## 4. Como Executar
1. Instalar dependências: `pip install langgraph langchain-openai pytest`
2. Configurar variável de ambiente: `export OPENAI_API_KEY="tua-chave"`
3. Executar o fluxo principal: `python main.py`
4. Executar a suite de testes: `pytest test_workflow.py`

graph TD
    %% Definição de Estilos
    classDef user fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef agent fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px;
    classDef expert fill:#fff3e0,stroke:#ff9800,stroke-width:2px;
    classDef guardrail fill:#ffebee,stroke:#f44336,stroke-width:2px;
    classDef output fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
    classDef state fill:#f3e5f5,stroke:#9c27b0,stroke-width:1px,stroke-dasharray: 5 5;

    %% Componentes
    U[Usuário / Ticket Entrada]:::user
    
    subgraph Orquestração e Estado
        S[(State Store: TicketState)]:::state
        T[Triage Agent\n(Roteamento)]:::agent
    end
    
    B[Bug Agent\n(Técnico)]:::expert
    F[Feature Agent\n(Negócios)]:::expert
    
    H[Human Review\n(Guardrail L2)]:::guardrail
    O[Saída Aprovada]:::output

    %% Fluxo
    U -->|Atualiza Estado| S
    U --> T
    T -->|Condicional: Bug| B
    T -->|Condicional: Feature| F
    
    B -->|Rascunho de Log| H
    F -->|Rascunho de Requisito| H
    
    H -->|Aprovação Determinística| O