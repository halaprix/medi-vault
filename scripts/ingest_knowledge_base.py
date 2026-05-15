"""Ingest knowledge base markdown files into ChromaDB."""
import os, sys, json
from pathlib import Path

KB_DIR = Path(__file__).parent.parent / "data" / "knowledge_base"

def chunk_text(text: str, max_chars: int = 1000) -> list[str]:
    """Simple paragraph-based chunking."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) < max_chars:
            current += ("\n\n" if current else "") + p
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks

def ingest():
    """Walk KB dir, chunk files, add to ChromaDB."""
    import chromadb
    client = chromadb.HttpClient(host=os.getenv("CHROMADB_HOST", "chromadb"), port=8000)
    collection = client.get_or_create_collection("medical_knowledge")

    count = 0
    for md_file in KB_DIR.rglob("*.md"):
        text = md_file.read_text()
        metadata = {"source": str(md_file.relative_to(KB_DIR)), "category": md_file.parent.name}
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],
                metadatas=[metadata],
                ids=[f"{md_file.stem}_{i}"]
            )
            count += 1

    print(f"Ingested {count} chunks from {KB_DIR}")
    return count

if __name__ == "__main__":
    ingest()
