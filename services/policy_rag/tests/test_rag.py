from services.policy_rag.schemas import PolicyQARequest
from services.policy_rag.service import UNGROUNDED_FALLBACK_ANSWER, PolicyRAGService
from services.policy_rag.vector_search import VectorSearchEngine


def test_vector_search_engine_retrieval():
    engine = VectorSearchEngine()
    results = engine.search_similar_controls("human oversight in high-risk AI systems", top_k=2)

    assert len(results) > 0
    top = results[0]
    assert top.framework_code == "EU_AI_ACT"
    assert top.control_code == "ART_14"
    assert top.similarity_score >= 0.90


def test_policy_rag_service_grounded_answer():
    service = PolicyRAGService()
    req = PolicyQARequest(user_query="What are the requirements for infrastructure encryption under SOC2?")
    res = service.answer_question(req)

    assert res.confidence_score > 0.0
    assert len(res.citations) > 0
    assert "SOC2_TYPE2" in [c.framework_code for c in res.citations]
    assert res.answer != UNGROUNDED_FALLBACK_ANSWER


def test_policy_rag_service_guardrail_3_ungrounded_fallback():
    # Test query with irrelevant terms resulting in low similarity < 0.40
    service = PolicyRAGService(similarity_threshold=0.99)
    req = PolicyQARequest(user_query="Unrelated query about cooking recipes and sports scores")
    res = service.answer_question(req)

    # Verify Guardrail 3 enforced: returns strict fallback string and 0.0 confidence
    assert res.answer == UNGROUNDED_FALLBACK_ANSWER
    assert res.confidence_score == 0.0
    assert len(res.citations) == 0
