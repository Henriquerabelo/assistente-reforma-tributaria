"""Testes automatizados do recuperador e do fluxo offline/anti-alucinação do TributaIA."""

from __future__ import annotations

import json
from pathlib import Path

from llm_client import responder
from retriever import KnowledgeRetriever

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def executar_testes() -> None:
    retriever = KnowledgeRetriever(DATA_DIR / "base_conhecimento_rtc.json")
    with open(DATA_DIR / "perfis_consulente.json", "r", encoding="utf-8") as f:
        perfis = json.load(f)
    perfil_contador = perfis[0]

    casos = [
        ("Simples Nacional e transferência de crédito", "Como funciona o Simples Nacional na Reforma Tributária?"),
        ("NFS-e e documentos fiscais", "O que muda na NFS-e e nos documentos fiscais?"),
        ("Imposto Seletivo", "O que é o Imposto Seletivo e sobre o que ele incide?"),
        ("Calculadora RTC", "Para que serve a Calculadora ou Motor Oficial de Cálculo na RTC?"),
        ("Fora de escopo (previsão do tempo)", "Qual a previsão do tempo para amanhã em São Paulo?"),
    ]

    for nome, pergunta in casos:
        trechos = retriever.buscar(pergunta, top_k=3)
        resposta, motor = responder(
            pergunta=pergunta,
            perfil=perfil_contador,
            trechos=trechos,
            modo="Offline (Base Local)",
        )
        print(f"=== {nome} ===")
        print(f"Motor: {motor} | Trechos encontrados: {len(trechos)}")
        for t in trechos:
            print(f"  - {t['modulo']} | {t['arquivo']} ({t['referencia']}) | score={t['score']}")
        print("Prévia da resposta:", resposta.splitlines()[0])
        print()


if __name__ == "__main__":
    executar_testes()
