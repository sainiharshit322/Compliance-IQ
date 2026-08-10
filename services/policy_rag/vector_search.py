import logging
import os
from typing import Any, Dict, List, Optional
from services.policy_rag.schemas import CitationItem

logger = logging.getLogger("policy_rag.vector_search")


class RetrievedControlSnippet:
    def __init__(
        self,
        framework_code: str,
        control_code: str,
        title: str,
        description: str,
        similarity_score: float,
    ):
        self.framework_code = framework_code
        self.control_code = control_code
        self.title = title
        self.description = description
        self.similarity_score = similarity_score

    def to_citation(self) -> CitationItem:
        return CitationItem(
            framework_code=self.framework_code,
            control_code=self.control_code,
            title=self.title,
            similarity_score=round(self.similarity_score, 4),
        )


class VectorSearchEngine:
    def __init__(self, db_connection: Optional[Any] = None, openai_client: Optional[Any] = None):
        self.db_connection = db_connection
        self.openai_client = openai_client

    def search_similar_controls(
        self,
        query: str,
        framework_code: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RetrievedControlSnippet]:
        """
        Queries pgvector HNSW vector index using cosine operator (<=>).
        Uses PostgreSQL connection if active; otherwise generates mock search results.
        """
        logger.info(f"Executing pgvector HNSW search for query '{query}' (Framework: {framework_code})...")

        if self.db_connection:
            try:
                return self._search_pgvector(query, framework_code, top_k)
            except Exception as ex:
                logger.warning(f"PostgreSQL pgvector query failed ({ex}). Falling back to mock vector search.")

        return self._search_mock_vector_database(query, framework_code, top_k)

    def _search_pgvector(
        self,
        query: str,
        framework_code: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RetrievedControlSnippet]:
        embedding = self._generate_embedding(query)
        sql = """
            SELECT control_code, framework_id, title, description,
                   1 - (embedding <=> %s::vector) AS similarity_score
            FROM controls
            WHERE (%s IS NULL OR framework_id = %s)
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """
        cursor = self.db_connection.cursor()
        cursor.execute(sql, (embedding, framework_code, framework_code, embedding, top_k))
        rows = cursor.fetchall()

        results = []
        for r in rows:
            results.append(
                RetrievedControlSnippet(
                    control_code=r[0],
                    framework_code=r[1],
                    title=r[2],
                    description=r[3],
                    similarity_score=float(r[4]),
                )
            )
        return results

    def _generate_embedding(self, text: str) -> List[float]:
        if self.openai_client or os.getenv("OPENAI_API_KEY"):
            try:
                import openai
                client = self.openai_client or openai.OpenAI()
                res = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text,
                )
                return res.data[0].embedding
            except Exception as ex:
                logger.warning(f"OpenAI embedding generation failed ({ex}). Returning dummy vector.")

        # Return dummy 1536-dim vector for testing
        return [0.01] * 1536

    def _search_mock_vector_database(
        self,
        query: str,
        framework_code: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RetrievedControlSnippet]:
        """Offline mock vector database containing regulatory framework controls."""
        q_lower = query.lower()

        mock_controls = [
            RetrievedControlSnippet(
                framework_code="EU_AI_ACT",
                control_code="ART_14",
                title="Human Oversight System Design",
                description="High-risk AI systems must be designed to enable natural persons to oversee operation and prevent or minimize risks.",
                similarity_score=0.94 if any(k in q_lower for k in ["human", "oversight", "ai", "risk", "article 14"]) else 0.35,
            ),
            RetrievedControlSnippet(
                framework_code="SOC2_TYPE2",
                control_code="CC6.1",
                title="Infrastructure Encryption at Rest",
                description="Logical access controls enforce infrastructure AES-256 data encryption at rest across infrastructure components.",
                similarity_score=0.92 if any(k in q_lower for k in ["encrypt", "storage", "soc2", "rest", "cc6.1"]) else 0.30,
            ),
            RetrievedControlSnippet(
                framework_code="GDPR",
                control_code="ART_32",
                title="Security of Processing",
                description="Controllers and processors shall implement appropriate technical and organizational measures to ensure security of processing.",
                similarity_score=0.88 if any(k in q_lower for k in ["gdpr", "processing", "personal", "data", "security"]) else 0.25,
            ),
            RetrievedControlSnippet(
                framework_code="HIPAA",
                control_code="164.312",
                title="Technical Safeguards Access Control",
                description="Implement technical policies and procedures for electronic information systems to allow access only to authorized persons.",
                similarity_score=0.86 if any(k in q_lower for k in ["hipaa", "health", "access", "phi", "safeguard"]) else 0.20,
            ),
        ]

        if framework_code:
            mock_controls = [c for c in mock_controls if c.framework_code == framework_code]

        mock_controls.sort(key=lambda x: x.similarity_score, reverse=True)
        return mock_controls[:top_k]
