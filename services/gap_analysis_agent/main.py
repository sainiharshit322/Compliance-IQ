import logging
from typing import Any, Dict, Optional, Tuple
from dotenv import load_dotenv

from services.gap_analysis_agent.engine import GapAnalysisEngine
from services.gap_analysis_agent.schemas import GapAnalysisInput

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gap_analysis_agent")


def evaluate_evidence_gap(
    input_dict: Dict[str, Any],
    save_audit_trail: bool = True,
    cosmos_container: Optional[Any] = None,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Exposes evidence gap evaluation and optional audit trail persistence helper."""
    engine = GapAnalysisEngine(cosmos_container=cosmos_container)
    input_model = GapAnalysisInput.model_validate(input_dict)

    if save_audit_trail:
        output, audit_doc = engine.process_and_audit(input_model)
        return output.model_dump(), audit_doc
    else:
        output = engine.evaluate(input_model)
        return output.model_dump(), None


def main():
    logger.info("Initializing Gap Analysis Agent engine service...")


if __name__ == "__main__":
    main()
