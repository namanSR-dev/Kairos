import spacy
import httpx
import math
from pydantic import BaseModel

# Try to load the spacy model. If not installed, it will be downloaded.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class ATSScore(BaseModel):
    exact_matches: list[str]
    missing_keywords: list[str]
    cosine_similarity: float

class ATSEngine:
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.embedding_model = "nomic-embed-text"

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract important nouns and proper nouns using spaCy."""
        # We must pass the original text so spaCy can read capitalization (PROPN).
        doc = nlp(text)
        keywords = set()
        for token in doc:
            if not token.is_stop and not token.is_punct and token.pos_ in ["NOUN", "PROPN"]:
                keywords.add(token.lemma_.lower())
        return keywords

    async def _get_embedding(self, text: str) -> list[float]:
        """Fetch dense vector embedding from local Ollama instance."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": text},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [])
            except httpx.RequestError as e:
                print(f"Ollama Connection Error: {e}. Is Ollama running with nomic-embed-text?")
                return []

    def _cosine_similarity(self, vecA: list[float], vecB: list[float]) -> float:
        """Calculate the cosine similarity between two mathematical vectors."""
        if not vecA or not vecB:
            return 0.0
        dot_product = sum(a * b for a, b in zip(vecA, vecB))
        magnitudeA = math.sqrt(sum(a * a for a in vecA))
        magnitudeB = math.sqrt(sum(b * b for b in vecB))
        if magnitudeA == 0 or magnitudeB == 0:
            return 0.0
        return dot_product / (magnitudeA * magnitudeB)

    async def score_resume(self, resume_text: str, job_description: str) -> ATSScore:
        """
        Calculates an Ironclad deterministic ATS score. No LLM generation used here.
        """
        # 1. Exact Keyword/Boolean Match
        job_keywords = self._extract_keywords(job_description)
        resume_keywords = self._extract_keywords(resume_text)
        
        matches = job_keywords.intersection(resume_keywords)
        missing = job_keywords.difference(resume_keywords)

        # 2. Semantic Similarity
        job_vector = await self._get_embedding(job_description)
        resume_vector = await self._get_embedding(resume_text)
        
        similarity = self._cosine_similarity(job_vector, resume_vector)

        return ATSScore(
            exact_matches=sorted(list(matches)),
            missing_keywords=sorted(list(missing)),
            cosine_similarity=round(similarity, 4)
        )
