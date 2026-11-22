"""Recuperador lexical (BM25 simplificado) sobre a base de conhecimento da Reforma Tributária (CFC-RFB)."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

STOPWORDS_PT = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sob", "sobre",
    "e", "ou", "mas", "que", "qual", "quais", "como", "quando", "onde", "porque",
    "se", "ao", "aos", "a", "as", "pelo", "pela", "pelos", "pelas", "entre",
    "ate", "apos", "ser", "estar", "ter", "haver", "foi", "sao", "esta", "este",
    "essa", "esse", "isso", "isto", "aquilo", "meu", "minha", "seu", "sua", "nao", "sim",
}


def normalizar_texto(texto: str) -> list[str]:
    """Remove acentos, converte para minúsculas e tokeniza termos relevantes."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    tokens = re.findall(r"[a-z0-9]+", sem_acento)
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS_PT]


class KnowledgeRetriever:
    """Indexa os trechos extraídos das apresentações CFC-RFB e executa busca BM25."""

    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path
        with open(json_path, "r", encoding="utf-8") as f:
            self.chunks: list[dict[str, Any]] = json.load(f)

        self._doc_tokens: list[Counter[str]] = []
        self._doc_lens: list[int] = []
        self._df: Counter[str] = Counter()

        for chunk in self.chunks:
            texto_indexavel = f"{chunk['modulo']} {chunk['arquivo']} {chunk['conteudo']}"
            tokens = normalizar_texto(texto_indexavel)
            counts = Counter(tokens)
            self._doc_tokens.append(counts)
            self._doc_lens.append(len(tokens))
            for termo in counts:
                self._df[termo] += 1

        self._n_docs = len(self.chunks)
        self._avg_len = (sum(self._doc_lens) / self._n_docs) if self._n_docs else 1.0

    def listar_modulos(self) -> list[str]:
        """Retorna a lista ordenada de módulos disponíveis na base."""
        return sorted({c["modulo"] for c in self.chunks})

    def buscar(
        self,
        consulta: str,
        top_k: int = 5,
        modulo_filtro: str | None = None,
        min_score: float = 8.0,
    ) -> list[dict[str, Any]]:
        """Retorna os top_k trechos mais relevantes para a consulta."""
        query_tokens = normalizar_texto(consulta)
        if not query_tokens or self._n_docs == 0:
            return []

        k1 = 1.5
        b = 0.75
        resultados: list[tuple[float, dict[str, Any]]] = []

        for idx, chunk in enumerate(self.chunks):
            if modulo_filtro and modulo_filtro != "Todos" and chunk["modulo"] != modulo_filtro:
                continue

            doc_counts = self._doc_tokens[idx]
            doc_len = self._doc_lens[idx]
            if doc_len == 0:
                continue

            score = 0.0
            for termo in query_tokens:
                tf = doc_counts.get(termo, 0)
                if tf == 0:
                    continue
                df = self._df.get(termo, 0)
                idf = math.log(1 + (self._n_docs - df + 0.5) / (df + 0.5))
                denom = tf + k1 * (1 - b + b * (doc_len / self._avg_len))
                score += idf * ((tf * (k1 + 1)) / denom)

            if score >= min_score:
                resultados.append((score, chunk))

        resultados.sort(key=lambda item: item[0], reverse=True)
        return [
            {**chunk, "score": round(score, 3)}
            for score, chunk in resultados[:top_k]
        ]
