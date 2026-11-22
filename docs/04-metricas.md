# Passo 4 — Avaliação e Métricas

## Estratégia de Avaliação

A qualidade do **TributaIA** é avaliada sob duas frentes complementares:
1. **Testes automatizados (`src/test_agente.py`):** Validação da precisão da busca BM25 sobre os 1.470 trechos e do comportamento anti-alucinação em perguntas fora de escopo;
2. **Avaliação humana (Feedback de usuários):** Teste prático com contadores/estudantes avaliando Assertividade, Segurança e Coerência em escala de 1 a 5.

---

## Métricas de Qualidade

| Métrica | O que avalia | Critério de Sucesso |
|---------|--------------|---------------------|
| **Assertividade** | O agente recupera o módulo correto e responde exatamente ao que foi perguntado? | Fontes retornadas pertencem ao módulo esperado do curso CFC-RFB |
| **Segurança (Anti-Alucinação)** | O agente evita inventar informações e recusa perguntas fora do escopo? | Retorna `0` trechos e admite limitação quando fora do domínio |
| **Coerência e Clareza** | A resposta está bem estruturada, cita fontes e sugere um próximo passo útil? | Linguagem alinhada ao perfil selecionado e citação de arquivo/página |

---

## Resultados Observados nos Testes Automatizados (`python src/test_agente.py`)

Execução realizada após o ajuste do limiar `min_score = 8.0` em `src/retriever.py` (modo `Offline (Base Local)`):

| # | Cenário de Teste | Módulo(s) Recuperado(s) | Top Score BM25 | Resultado |
|---|------------------|-------------------------|----------------|-----------|
| 1 | *"Como funciona o Simples Nacional na Reforma Tributária?"* | `Módulo 8` (Gustavo Salton; Tiago Sfreddo) e `Módulo 4` | `11.607` | [x] Aprovado |
| 2 | *"O que muda na NFS-e e nos documentos fiscais?"* | `Módulo 5` (NFS-e - Hermano, Páginas 2, 19 e 20) | `15.340` | [x] Aprovado |
| 3 | *"O que é o Imposto Seletivo e sobre o que ele incide?"* | `Módulo 17` (Rosangela; Demétrios e João Hamilton) | `9.959` | [x] Aprovado |
| 4 | *"Para que serve a Calculadora ou Motor Oficial de Cálculo na RTC?"* | `Módulo 5` (Calculadora - Ariel Bonzan, Páginas 1, 33 e 17) | `24.444` | [x] Aprovado |
| 5 | *"Qual a previsão do tempo para amanhã em São Paulo?"* (Fora de escopo) | Nenhum (`0` trechos acima de `8.0`) | `< 8.0` | [x] Aprovado (recusa segura) |

---

## Formulário de Feedback para Testes com Usuários

| Métrica | Pergunta de Avaliação | Nota (1-5) |
|---------|-----------------------|------------|
| Assertividade | A resposta trouxe exatamente o que você precisava sobre o tema? | ___ |
| Segurança | As citações de módulo, arquivo e página passaram confiança? | ___ |
| Coerência | O nível técnico foi adequado ao seu perfil? | ___ |

**Observações:**
- O ajuste de `min_score` de `3.5` para `8.0` eliminou o falso positivo em perguntas fora de escopo contendo palavras comuns como *"tempo"*.
- Como evolução futura, pretende-se incorporar embeddings vetoriais para capturar sinônimos semânticos além da correspondência lexical do BM25.
