"""RAG Service — knowledge base retrieval + recommendation generation via ChromaDB + Ollama."""
from typing import Optional

import httpx

from app.core.config import settings


DISCLAIMER = (
    "⚠️ This is informational content generated from medical guidelines and is NOT medical advice. "
    "Consult a healthcare professional before making changes."
)


class RAGService:
    """Retrieval-Augmented Generation for health recommendations."""

    def __init__(self):
        self.chromadb_url = settings.chromadb_url
        self.ollama_url = settings.ollama_base_url

    async def retrieve(
        self,
        biomarker_name: str,
        value: float,
        unit: str,
        direction: str,
        loinc_code: Optional[str] = None,
        top_k: int = 5,
    ) -> list[str]:
        """Retrieve relevant medical guideline snippets from ChromaDB."""
        query = f"dietary and lifestyle recommendations for {direction} {biomarker_name} with value {value} {unit}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get embedding from Ollama
                embed_resp = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": query},
                )
                if embed_resp.status_code != 200:
                    return []
                embedding = embed_resp.json().get("embedding", [])

                # Query ChromaDB
                where_filter = {}
                if loinc_code:
                    where_filter = {"biomarker_loinc_codes": {"$contains": loinc_code}}

                chroma_resp = await client.post(
                    f"{self.chromadb_url}/api/v1/collections/health_guidelines/query",
                    json={
                        "query_embeddings": [embedding],
                        "n_results": top_k,
                        "where": where_filter,
                    },
                )
                if chroma_resp.status_code != 200:
                    return []

                data = chroma_resp.json()
                docs = []
                for result_set in data.get("results", []):
                    for doc in result_set.get("documents", []):
                        if isinstance(doc, str):
                            docs.append(doc)
                return docs

        except httpx.HTTPError:
            return []

    async def generate_recommendation(
        self,
        biomarker_name: str,
        value: float,
        unit: str,
        direction: str,
        ref_low: Optional[float],
        ref_high: Optional[float],
        contexts: list[str],
    ) -> str:
        """Generate a health recommendation using Ollama."""
        ref_range = f"{ref_low or '?'}-{ref_high or '?'} {unit}"

        context_str = "\n\n".join(f"---\n{c}" for c in contexts) if contexts else "No specific guidelines available."

        prompt = f"""You are a health information assistant. Based ONLY on the provided medical guidelines below,
generate actionable, specific dietary and lifestyle recommendations for a patient with
{direction} {biomarker_name} ({value} {unit}, reference: {ref_range}).

Medical guidelines context:
{context_str}

Rules:
- Be specific and actionable (mention specific foods, amounts, frequency)
- Do NOT recommend specific medications or supplements doses
- Include a disclaimer that this is informational only and not medical advice
- Response length: 150-250 words
- Format: 2-3 short paragraphs"""

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": settings.ollama_model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7},
                    },
                )
                resp.raise_for_status()
                text = resp.json().get("response", "")
                return f"{DISCLAIMER}\n\n{text}"
        except httpx.HTTPError:
            return f"{DISCLAIMER}\n\nUnable to generate recommendation at this time."
