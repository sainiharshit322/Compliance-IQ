import logging
from typing import Any, Dict
from dotenv import load_dotenv

from services.policy_rag.schemas import PolicyQARequest
from services.policy_rag.service import PolicyRAGService

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("policy_rag")


def answer_policy_question(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Exposes Policy Q&A helper for orchestrator API & Next.js HITL portal integration."""
    service = PolicyRAGService()
    request_model = PolicyQARequest.model_validate(input_dict)
    response_model = service.answer_question(request_model)
    return response_model.model_dump()


def main():
    logger.info("Initializing Policy Q&A RAG Agent service...")


if __name__ == "__main__":
    main()
