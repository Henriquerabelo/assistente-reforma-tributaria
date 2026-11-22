# Passo 2 — Base de Conhecimento

## Origem dos Dados
A base de conhecimento foi construída diretamente a partir das **48 apresentações oficiais** (46 PDFs e 2 PPTX) do treinamento conjunto **Receita Federal do Brasil (RFB) e Conselho Federal de Contabilidade (CFC)** sobre a Reforma Tributária do Consumo (RTC), armazenadas no Google Drive do projeto.

A extração gerou **1.470 trechos indexáveis** com identificação de módulo, nome do arquivo e número da página ou slide.

## Arquivos da Pasta `data/`

| Arquivo | Formato | Finalidade no TributaIA |
|---------|---------|-------------------------|
| `base_conhecimento_rtc.json` | JSON | Contém os 1.470 trechos extraídos das 48 apresentações (`id`, `modulo`, `arquivo`, `referencia`, `conteudo`). |
| `modulos_catalogo.csv` | CSV | Catálogo completo dos 48 arquivos com módulo inferido, tipo (`PDF`/`PPTX`), total de páginas/slides e páginas com texto. |
| `conceitos_chave_rtc.json` | JSON | Mapeamento resumido dos grandes temas (IBS/CBS, Imposto Seletivo, Obrigações Acessórias, Simples Nacional, Regimes Específicos). |
| `perfis_consulente.json` | JSON | Perfis de usuário (Contador, Consultor/Estudante, Simples Nacional/MEI) usados para adaptar o tom e os exemplos da resposta. |

---

## Estratégia de Integração (RAG Lexical)

Em vez de enviar todas as apresentações de uma só vez no prompt (o que excederia limites de contexto e aumentaria custo/latência), o agente utiliza **recuperação dinâmica sob demanda** via `KnowledgeRetriever` (`src/retriever.py`):

1. **Normalização:** Remove acentos, converte para minúsculas e descarta *stopwords* em português;
2. **Ranqueamento BM25:** Calcula a relevância de cada um dos 1.470 trechos frente à pergunta do usuário (com filtro opcional por módulo);
3. **Filtro de Segurança (`min_score = 8.0`):** Descarta correspondências fracas para evitar que o modelo responda sobre temas fora do escopo;
4. **Injeção no Prompt:** Apenas os **top-5 trechos** mais relevantes são injetados no contexto enviado ao LLM (ou exibidos de forma estruturada no modo Offline).

### Exemplo de Contexto Formatado Enviado ao LLM

```text
PERFIL DO CONSULENTE: Contador(a) / Escritório Contábil
OBJETIVO: Aplicar corretamente as regras da Reforma Tributária no dia a dia dos clientes...
TOM PREFERIDO: Técnico-prático, objetivo, com foco em legislação (EC 132/2023 e LC 214/2025)...

CONTEXTO RECUPERADO (Curso CFC-RFB):
[Fonte 1] Módulo 8 | Arquivo: Módulo 8 - CFC - RTC - Simples Nacional, MEI - Gustavo Salton - vf.pdf | Página 2
Conteúdo: ...

[Fonte 2] Módulo 5 | Arquivo: 5° Módulo - CFC -RFB - Obrigações Acessórias - Documentos Fiscais - NFS-e - Hermano.pdf | Página 2
Conteúdo: ...

PERGUNTA DO USUÁRIO:
Como funciona o Simples Nacional na Reforma Tributária?
```
