import logging
from typing import Any, Dict
from dotenv import load_dotenv

from services.gap_analysis_agent.engine import GapAnalysisEngine
from services.gap_analysis_agent.schemas import GapAnalysisInput

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gap_analysis_agent")


def evaluate_evidence_gap(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Exposes evidence gap evaluation helper for queue workers & API gateway."""
    engine = GapAnalysisEngine()
    input_model = GapAnalysisInput.model_validate(input_dict)
    result = engine.evaluate(input_model)
    return result.model_dump()


def main():
    logger.info("Initializing Gap Analysis Agent engine service...")


if __name__ == "__main__":
    main()
