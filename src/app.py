"""Aplicação Streamlit do TributaIA — Assistente Virtual de Reforma Tributária (CFC-RFB)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from llm_client import responder
from retriever import KnowledgeRetriever

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="TributaIA — Assistente da Reforma Tributária",
    page_icon="⚖️",
    layout="wide",
)


@st.cache_resource
def carregar_retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever(DATA_DIR / "base_conhecimento_rtc.json")


@st.cache_data
def carregar_perfis() -> list[dict]:
    with open(DATA_DIR / "perfis_consulente.json", "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def carregar_catalogo() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "modulos_catalogo.csv")


retriever = carregar_retriever()
perfis = carregar_perfis()
catalogo = carregar_catalogo()

# ============ SIDEBAR ============
with st.sidebar:
    st.title("⚙️ Configurações")
    perfil_nomes = [p["nome"] for p in perfis]
    perfil_sel_nome = st.selectbox("Perfil do Consulente", perfil_nomes)
    perfil_atual = next(p for p in perfis if p["nome"] == perfil_sel_nome)

    modulos_disp = ["Todos"] + retriever.listar_modulos()
    modulo_sel = st.selectbox("Filtrar por Módulo (CFC-RFB)", modulos_disp)

    st.divider()
    modo_ia = st.selectbox(
        "Motor de IA",
        [
            "Automático (Híbrido)",
            "Google Gemini",
            "OpenAI",
            "Ollama Local",
            "Offline (Base Local)",
        ],
    )
    gemini_key = st.text_input("GEMINI_API_KEY (opcional)", type="password")
    openai_key = st.text_input("OPENAI_API_KEY (opcional)", type="password")
    ollama_model = st.text_input("Modelo Ollama", value="llama3.2")

    st.divider()
    st.caption(
        f"📚 Base carregada: **{len(catalogo)} apresentações** "
        f"({len(retriever.chunks)} trechos indexados)."
    )
    if st.button("Limpar conversa"):
        st.session_state.mensagens = []
        st.rerun()

# ============ CABEÇALHO ============
st.title("⚖️ TributaIA — Assistente de Reforma Tributária")
st.markdown(
    "Assistente virtual baseado nos materiais oficiais do treinamento **Receita Federal (RFB) e CFC**. "
    "Faça perguntas sobre **IBS, CBS, Imposto Seletivo, Simples Nacional, Obrigações Acessórias e Regimes Específicos**."
)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Sugestões rápidas
st.caption("💡 Sugestões de perguntas para testar:")
cols = st.columns(3)
sugestoes = [
    "Como funciona o Simples Nacional na Reforma Tributária?",
    "O que muda na NFS-e e nos Documentos Fiscais?",
    "O que é o Imposto Seletivo e sobre o que incide?",
]
pergunta_clicada = None
for col, sug in zip(cols, sugestoes):
    if col.button(sug, use_container_width=True):
        pergunta_clicada = sug

# Histórico do chat
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("fontes"):
            with st.expander(f"📎 Fontes consultadas ({len(msg['fontes'])} trechos) — Motor: {msg.get('motor', '-')}"):
                for f_item in msg["fontes"]:
                    st.markdown(
                        f"- **{f_item['modulo']}** | `{f_item['arquivo']}` ({f_item['referencia']}) — *Score: {f_item['score']}*"
                    )

# Input do usuário
pergunta = st.chat_input("Digite sua dúvida sobre a Reforma Tributária...") or pergunta_clicada

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando base CFC-RFB e gerando resposta..."):
            trechos = retriever.buscar(pergunta, top_k=5, modulo_filtro=modulo_sel)
            try:
                texto_resp, motor_usado = responder(
                    pergunta=pergunta,
                    perfil=perfil_atual,
                    trechos=trechos,
                    modo=modo_ia,
                    gemini_key=gemini_key,
                    openai_key=openai_key,
                    ollama_model=ollama_model,
                )
            except Exception as exc:
                texto_resp = f"⚠️ Erro ao consultar o motor selecionado: `{exc}`"
                motor_usado = "Erro"

            st.markdown(texto_resp)
            if trechos:
                with st.expander(f"📎 Fontes consultadas ({len(trechos)} trechos) — Motor: {motor_usado}"):
                    for f_item in trechos:
                        st.markdown(
                            f"- **{f_item['modulo']}** | `{f_item['arquivo']}` ({f_item['referencia']}) — *Score: {f_item['score']}*"
                        )

    st.session_state.mensagens.append(
        {
            "role": "assistant",
            "content": texto_resp,
            "fontes": trechos,
            "motor": motor_usado,
        }
    )
