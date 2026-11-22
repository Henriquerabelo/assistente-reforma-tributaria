"""Cliente híbrido de LLM (Gemini, OpenAI, Ollama) com fallback local estruturado."""

from __future__ import annotations

import os
from typing import Any

import requests

SYSTEM_PROMPT = """Você é o **TributaIA**, um assistente virtual especializado na Reforma Tributária do Consumo (RTC), treinado exclusivamente com os materiais oficiais do curso Receita Federal (RFB) e Conselho Federal de Contabilidade (CFC).

OBJETIVO:
Ajudar contadores, consultores, estudantes e empresários a compreenderem a Reforma Tributária (IBS, CBS, Imposto Seletivo, Simples Nacional, Obrigações Acessórias, Regimes Específicos e Transição) de forma clara, didática e fundamentada.

REGRAS ESTRITAS:
1. BASE FECHADA: Responda APENAS com base nos trechos do treinamento CFC-RFB fornecidos no CONTEXTO RECUPERADO.
2. ANTI-ALUCINAÇÃO: NUNCA invente alíquotas, prazos, artigos de lei ou regras que não constem no contexto fornecido.
3. FORA DE ESCOPO / SEM INFORMAÇÃO: Se a pergunta não for sobre Reforma Tributária ou se o contexto recuperado estiver vazio/insuficiente, diga claramente: "Não encontrei informação suficiente nas apresentações do curso CFC-RFB para responder com segurança a essa pergunta." e explique o que você pode ajudar a consultar.
4. CITAÇÃO DE FONTES: Sempre cite o Módulo, o nome do arquivo e a página/slide das fontes utilizadas.
5. ADAPTAÇÃO AO PERFIL: Ajuste a linguagem e os exemplos ao perfil do consulente informado.
6. PRÓXIMO PASSO: Ao final, sugira um próximo passo prático ou tema relacionado para o usuário continuar estudando ou aplicando.
7. CONCISÃO: Responda de forma estruturada (tópicos curtos), clara e direta.
"""


def montar_prompt_usuario(
    pergunta: str,
    perfil: dict[str, Any],
    trechos: list[dict[str, Any]],
) -> str:
    """Formata o contexto recuperado e o perfil do consulente para enviar ao modelo."""
    if trechos:
        blocos = []
        for i, t in enumerate(trechos, 1):
            blocos.append(
                f"[Fonte {i}] {t['modulo']} | Arquivo: {t['arquivo']} | {t['referencia']}\n"
                f"Conteúdo: {t['conteudo']}"
            )
        contexto_str = "\n\n".join(blocos)
    else:
        contexto_str = "NENHUM TRECHO RELEVANTE ENCONTRADO NA BASE DE CONHECIMENTO."

    return (
        f"PERFIL DO CONSULENTE: {perfil['nome']}\n"
        f"OBJETIVO: {perfil['objetivo']}\n"
        f"TOM PREFERIDO: {perfil['tom_preferido']}\n\n"
        f"CONTEXTO RECUPERADO (Curso CFC-RFB):\n{contexto_str}\n\n"
        f"PERGUNTA DO USUÁRIO:\n{pergunta}"
    )


def gerar_resposta_offline(
    pergunta: str,
    perfil: dict[str, Any],
    trechos: list[dict[str, Any]],
) -> str:
    """Gera resposta estruturada sem depender de LLM externo (fallback determinístico)."""
    if not trechos:
        return (
            "Não encontrei informação suficiente nas apresentações do curso CFC-RFB para responder "
            "com segurança a essa pergunta.\n\n"
            "**O que posso fazer por você:**\n"
            "- Tirar dúvidas sobre **IBS, CBS e Imposto Seletivo (IS)**;\n"
            "- Consultar regras de **Cadastro, NF-e, NFS-e e Calculadora RTC**;\n"
            "- Explicar impactos no **Simples Nacional, MEI, Agronegócio, Economia Digital, Combustíveis e Regimes Específicos**.\n\n"
            "💡 *Próximo passo:* Tente reformular usando termos da Reforma Tributária ou selecione um módulo específico na barra lateral."
        )

    linhas = [
        f"Com base nas apresentações do treinamento **CFC-RFB** (adaptado para *{perfil['nome']}*), encontrei os seguintes pontos relevantes para sua dúvida:\n"
    ]
    for i, t in enumerate(trechos[:3], 1):
        resumo = t["conteudo"][:420].strip()
        if len(t["conteudo"]) > 420:
            resumo += "..."
        linhas.append(
            f"**{i}. {t['modulo']}** (`{t['arquivo']}` — {t['referencia']}):\n> {resumo}\n"
        )

    modulos_sugeridos = ", ".join(sorted({t["modulo"] for t in trechos[:3]}))
    linhas.append(
        f"💡 *Próximo passo:* Recomendo revisar os materiais completos de **{modulos_sugeridos}** ou ativar uma chave de API (Gemini/OpenAI) ou Ollama local na barra lateral para obter sínteses conversacionais mais aprofundadas."
    )
    return "\n".join(linhas)


def chamar_gemini(prompt_usuario: str, api_key: str, modelo: str = "gemini-2.5-flash") -> str:
    """Chama a API do Google Gemini usando google-genai."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=modelo,
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )
    return resp.text or "Sem resposta retornada pelo modelo."


def chamar_openai(prompt_usuario: str, api_key: str, modelo: str = "gpt-4o-mini") -> str:
    """Chama a API da OpenAI."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=modelo,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_usuario},
        ],
    )
    return resp.choices[0].message.content or "Sem resposta retornada pelo modelo."


def chamar_ollama(
    prompt_usuario: str,
    modelo: str = "llama3.2",
    url: str = "http://localhost:11434/api/generate",
) -> str:
    """Chama uma instância local do Ollama."""
    payload = {
        "model": modelo,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt_usuario}",
        "stream": False,
        "options": {"temperature": 0.2},
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json().get("response", "Sem resposta retornada pelo Ollama.")


def responder(
    pergunta: str,
    perfil: dict[str, Any],
    trechos: list[dict[str, Any]],
    modo: str = "Automático (Híbrido)",
    gemini_key: str = "",
    openai_key: str = "",
    ollama_model: str = "llama3.2",
) -> tuple[str, str]:
    """Orquestra a geração da resposta e retorna (texto_resposta, motor_utilizado)."""
    prompt_usuario = montar_prompt_usuario(pergunta, perfil, trechos)
    g_key = gemini_key.strip() or os.getenv("GEMINI_API_KEY", "").strip()
    o_key = openai_key.strip() or os.getenv("OPENAI_API_KEY", "").strip()

    if modo == "Google Gemini":
        if not g_key:
            raise ValueError("Informe a GEMINI_API_KEY na barra lateral ou variável de ambiente.")
        return chamar_gemini(prompt_usuario, g_key), "Google Gemini"

    if modo == "OpenAI":
        if not o_key:
            raise ValueError("Informe a OPENAI_API_KEY na barra lateral ou variável de ambiente.")
        return chamar_openai(prompt_usuario, o_key), "OpenAI"

    if modo == "Ollama Local":
        return chamar_ollama(prompt_usuario, modelo=ollama_model), f"Ollama ({ollama_model})"

    if modo == "Offline (Base Local)":
        return gerar_resposta_offline(pergunta, perfil, trechos), "Offline (Busca CFC-RFB)"

    # Modo Automático (Híbrido): tenta Gemini -> OpenAI -> Ollama -> Fallback Offline
    if g_key:
        try:
            return chamar_gemini(prompt_usuario, g_key), "Google Gemini"
        except Exception:
            pass
    if o_key:
        try:
            return chamar_openai(prompt_usuario, o_key), "OpenAI"
        except Exception:
            pass
    try:
        resp = chamar_ollama(prompt_usuario, modelo=ollama_model)
        return resp, f"Ollama ({ollama_model})"
    except Exception:
        return gerar_resposta_offline(pergunta, perfil, trechos), "Offline (Fallback CFC-RFB)"
