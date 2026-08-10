import json
import logging
import os
from typing import Any, Dict, List, Optional

from services.policy_rag.schemas import CitationItem, PolicyQARequest, PolicyQAResponse
from services.policy_rag.vector_search import VectorSearchEngine

logger = logging.getLogger("policy_rag.service")

POLICY_QA_SYSTEM_PROMPT = """You are the ComplianceIQ Policy Q&A Assistant—an expert on regulatory frameworks (SOC 2, ISO 27001, GDPR, HIPAA, EU AI Act).

You will answer user questions strictly using the retrieved regulatory context snippets provided below.

RETRIEVED CONTEXT SNIPPETS:
--------------------------------------------------
{retrieved_snippets}
--------------------------------------------------

INSTRUCTIONS:
1. Answer the user prompt accurately based ONLY on the retrieved snippets.
2. Synthesize a concise, executive-friendly response.
3. Cite every claim by referencing `[FrameworkCode - ControlCode / Article]`.
4. If the retrieved snippets do not contain enough information, reply: "Insufficient regulatory context retrieved to answer with certainty."
5. Calculate a `confidence_score` (0.00 to 1.00).

USER QUESTION: {user_query}
TARGET FRAMEWORK: {framework_code}
"""

UNGROUNDED_FALLBACK_ANSWER = "Insufficient regulatory context retrieved to answer with certainty."


class PolicyRAGService:
    def __init__(
        self,
        vector_search_engine: Optional[VectorSearchEngine] = None,
        openai_client: Optional[Any] = None,
        model_name: str = "gpt-4o",
        similarity_threshold: float = 0.40,
    ):
        self.vector_search_engine = vector_search_engine or VectorSearchEngine()
        self.openai_client = openai_client
        self.model_name = os.getenv("OPENAI_MODEL", model_name)
        self.similarity_threshold = similarity_threshold

    def answer_question(self, request: PolicyQARequest) -> PolicyQAResponse:
        """
        Main entrypoint processing user regulatory Q&A query.
        Retrieves vector context snippets, enforces Guardrail 3 grounding,
        and synthesizes cited responses.
        """
        logger.info(f"Processing Policy Q&A query: '{request.user_query}'...")

        # 1. Retrieve vector search context snippets
        snippets = self.vector_search_engine.search_similar_controls(
            query=request.user_query,
            framework_code=request.framework_code,
            top_k=request.top_k,
        )

        # Filter snippets above similarity threshold
        relevant_snippets = [s for s in snippets if s.similarity_score >= self.similarity_threshold]

        # 2. Enforce Guardrail 3: Zero-Hallucination Grounding
        if not relevant_snippets:
            logger.warning(
                f"Guardrail 3 Triggered: No snippets above similarity threshold {self.similarity_threshold}. Returning fallback."
            )
            return PolicyQAResponse(
                answer=UNGROUNDED_FALLBACK_ANSWER,
                confidence_score=0.00,
                citations=[],
            )

        citations = [s.to_citation() for s in relevant_snippets]

        # 3. LLM Synthesis or template fallback
        if self._can_use_llm():
            try:
                return self._synthesize_with_llm(request, relevant_snippets, citations)
            except Exception as ex:
                logger.warning(f"LLM synthesis failed ({ex}). Using template response.")

        return self._synthesize_with_templates(request, relevant_snippets, citations)

    def _can_use_llm(self) -> bool:
        return (
            self.openai_client is not None
            or bool(os.getenv("OPENAI_API_KEY"))
            or bool(os.getenv("AZURE_OPENAI_API_KEY"))
        )

    def _synthesize_with_llm(
        self,
        request: PolicyQARequest,
        snippets: List[Any],
        citations: List[CitationItem],
    ) -> PolicyQAResponse:
        import openai

        client = self.openai_client or openai.OpenAI()

        snippets_text = "\n\n".join(
            [f"[{s.framework_code} - {s.control_code}] {s.title}: {s.description}" for s in snippets]
        )

        prompt = POLICY_QA_SYSTEM_PROMPT.format(
            retrieved_snippets=snippets_text,
            user_query=request.user_query,
            framework_code=request.framework_code or "ALL",
        )

        response = client.chat.completions.create(
            model=self.model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        content = response.choices[0].message.content
        raw_json = json.loads(content)
        return PolicyQAResponse.model_validate(raw_json)

    def _synthesize_with_templates(
        self,
        request: PolicyQARequest,
        snippets: List[Any],
        citations: List[CitationItem],
    ) -> PolicyQAResponse:
        """Deterministic grounding template synthesizer for offline/testing environments."""
        top = snippets[0]
        answer = (
            f"Under [{top.framework_code} - {top.control_code}], {top.description} "
            f"Regulatory provisions mandate compliance enforcement across target environments."
        )
        avg_score = sum(c.similarity_score for c in citations) / len(citations)

        return PolicyQAResponse(
            answer=answer,
            confidence_score=round(avg_score, 2),
            citations=citations,
        )
