import logging
from typing import Any, Dict
from dotenv import load_dotenv

from services.remediation_advisor.generator import RemediationAdvisorGenerator
from services.remediation_advisor.schemas import RemediationAdvisorInput

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("remediation_advisor")


def generate_remediation_plan(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Exposes remediation plan generator helper for orchestrator API & HITL portal integration."""
    generator = RemediationAdvisorGenerator()
    input_model = RemediationAdvisorInput.model_validate(input_dict)
    output_model = generator.generate_remediation(input_model)
    return output_model.model_dump()


def main():
    logger.info("Initializing Remediation Advisor Agent service...")


if __name__ == "__main__":
    main()
