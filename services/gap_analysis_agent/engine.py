import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from services.gap_analysis_agent.audit_handler import AuditTrailHandler
from services.gap_analysis_agent.schemas import (
    ComplianceStatusEnum,
    ControlContext,
    ControlSeverityEnum,
    EvidenceContext,
    GapAnalysisInput,
    GapAnalysisOutput,
    GapDetails,
)

logger = logging.getLogger("gap_analysis_agent.engine")

GAP_ANALYSIS_SYSTEM_PROMPT = """You are the ComplianceIQ Gap Analysis Agent—an expert regulatory compliance auditor.
Your job is to evaluate raw collected evidence JSON against strict compliance control requirements.

CRITICAL OPERATIONAL RULES:
1. Compare the provided Evidence JSON against the Control Requirement Description and Evidence Rule AST.
2. Determine the Compliance Status: COMPLIANT, NON_COMPLIANT, PARTIAL, or NEEDS_HUMAN_REVIEW.
3. Calculate a Risk Score from 0.00 (No Risk) to 10.00 (Critical Exposure).
4. Assign a Confidence Score from 0 to 100 based on evidence completeness:
   - 90-100: Complete, deterministic evidence directly proving compliance/non-compliance.
   - 85-89: Clear evidence with minor contextual assumptions.
   - 0-84: Ambiguous, incomplete, or throttled evidence payload.
5. MANDATORY GUARDRAIL: If your Confidence Score is less than 85, you MUST set `compliance_status` to "NEEDS_HUMAN_REVIEW" and set `flagged_for_hitl` to true with reason "Ambiguous Evidence".
6. Respond ONLY in valid JSON matching the required schema. No markdown wrapping or extra text.
"""


class GapAnalysisEngine:
    def __init__(
        self,
        openai_client: Optional[Any] = None,
        cosmos_container: Optional[Any] = None,
        model_name: str = "gpt-4o",
    ):
        self.openai_client = openai_client
        self.model_name = os.getenv("OPENAI_MODEL", model_name)
        self.audit_handler = AuditTrailHandler(cosmos_container=cosmos_container)

    def evaluate(self, input_data: GapAnalysisInput) -> GapAnalysisOutput:
        """
        Main entrypoint evaluating evidence against control requirements.
        Attempts GPT-4o JSON mode call if OpenAI API is configured;
        otherwise runs deterministic AST rule evaluation.
        Enforces Guardrail 2 (<85% confidence threshold routing).
        """
        logger.info(
            f"Evaluating gap analysis for control '{input_data.control.control_code}' ({input_data.control.framework})..."
        )

        output: Optional[GapAnalysisOutput] = None

        # Try LLM evaluation if client/key is available
        if self._can_use_llm():
            try:
                output = self._evaluate_with_llm(input_data)
            except Exception as ex:
                logger.warning(f"LLM evaluation failed ({ex}). Falling back to AST rule evaluation.")

        # Fallback to deterministic AST rule evaluation engine
        if output is None:
            output = self._evaluate_with_ast_rules(input_data)

        # Enforce Guardrail 2: Confidence Threshold Routing (<85% HITL Fallback)
        output = self._enforce_guardrail_2(output)

        logger.info(
            f"Gap Analysis result for {input_data.control.control_code}: status={output.compliance_status}, "
            f"risk={output.risk_score}, confidence={output.confidence_score}, hitl={output.flagged_for_hitl}"
        )
        return output

    def process_and_audit(self, input_data: GapAnalysisInput) -> Tuple[GapAnalysisOutput, Dict[str, Any]]:
        """Evaluates evidence and persists formatted audit trail document."""
        output = self.evaluate(input_data)
        audit_record = self.audit_handler.save_audit_trail(input_data, output)
        return output, audit_record

    def _can_use_llm(self) -> bool:
        return (
            self.openai_client is not None
            or bool(os.getenv("OPENAI_API_KEY"))
            or bool(os.getenv("AZURE_OPENAI_API_KEY"))
        )

    def _evaluate_with_llm(self, input_data: GapAnalysisInput) -> GapAnalysisOutput:
        import openai

        client = self.openai_client or openai.OpenAI()

        prompt_payload = {
            "control": input_data.control.model_dump(),
            "evidence": input_data.evidence.model_dump(),
        }

        response = client.chat.completions.create(
            model=self.model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": GAP_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(prompt_payload)},
            ],
            temperature=0.0,
        )

        content = response.choices[0].message.content
        raw_json = json.loads(content)
        return GapAnalysisOutput.model_validate(raw_json)

    def _evaluate_with_ast_rules(self, input_data: GapAnalysisInput) -> GapAnalysisOutput:
        """Deterministic AST rule evaluation logic when LLM is offline/testing."""
        control = input_data.control
        evidence = input_data.evidence
        payload = evidence.payload

        # Check for degraded/throttled evidence status
        if payload.get("status") == "PARTIAL_THROTTLED":
            return GapAnalysisOutput(
                compliance_status=ComplianceStatusEnum.NEEDS_HUMAN_REVIEW,
                risk_score=5.00,
                confidence_score=40,
                reasoning_chain=[
                    "Evidence payload indicates PARTIAL_THROTTLED rate limit exhaustion.",
                    "Evidence data is incomplete due to cloud provider throttling.",
                    "Routing control evaluation to HITL Compliance Officer review.",
                ],
                gap_details=GapDetails(
                    summary=f"Throttled evidence collected for control {control.control_code}.",
                    failed_conditions=["Cloud API rate limit exceeded during evidence scan."],
                ),
                flagged_for_hitl=True,
                hitl_reason="Throttled Evidence Payload (HTTP 429)",
            )

        failed_conditions: List[str] = []
        reasoning: List[str] = [
            f"Evaluating evidence for control '{control.control_code}' under framework '{control.framework}'.",
        ]

        rule = control.evidence_rule_expression
        is_compliant = True

        if rule:
            required_prop = rule.get("required_property")
            expected_val = rule.get("expected_value")

            if required_prop:
                val = self._extract_nested_property(payload, required_prop)
                reasoning.append(f"Inspected property '{required_prop}'. Found value '{val}' (Expected '{expected_val}').")
                if val != expected_val:
                    is_compliant = False
                    failed_conditions.append(
                        f"Property '{required_prop}' value '{val}' does not match expected '{expected_val}'."
                    )
        else:
            is_compliant = payload.get("is_compliant", True)
            if not is_compliant:
                failed_conditions.append("Evidence payload contains non-compliant configuration status.")

        if is_compliant:
            status = ComplianceStatusEnum.COMPLIANT
            risk_score = 0.00
            confidence_score = 95
            reasoning.append("Control requirements fully satisfied by evidence payload.")
            summary = f"Control '{control.control_code}' is fully compliant based on evidence scan."
        else:
            status = ComplianceStatusEnum.NON_COMPLIANT
            risk_score = self._map_severity_to_risk(control.severity)
            confidence_score = 90
            reasoning.append(f"Control failed requirement evaluation. Assigned risk score {risk_score}.")
            summary = f"Control '{control.control_code}' is non-compliant: {'; '.join(failed_conditions)}"

        return GapAnalysisOutput(
            compliance_status=status,
            risk_score=risk_score,
            confidence_score=confidence_score,
            reasoning_chain=reasoning,
            gap_details=GapDetails(
                summary=summary,
                failed_conditions=failed_conditions,
            ),
            flagged_for_hitl=False,
            hitl_reason=None,
        )

    def _enforce_guardrail_2(self, output: GapAnalysisOutput) -> GapAnalysisOutput:
        """
        Guardrail 2: Confidence Threshold Routing (HITL < 85%)
        If confidence_score < 85, forces NEEDS_HUMAN_REVIEW and flagged_for_hitl = True.
        """
        if output.confidence_score < 85:
            logger.warning(
                f"Guardrail 2 Triggered: confidence_score {output.confidence_score} < 85. Routing to HITL."
            )
            output.compliance_status = ComplianceStatusEnum.NEEDS_HUMAN_REVIEW
            output.flagged_for_hitl = True
            if not output.hitl_reason:
                output.hitl_reason = "Ambiguous Evidence (Confidence Score < 85%)"
        return output

    def _extract_nested_property(self, data: Dict[str, Any], path: str) -> Any:
        keys = path.split(".")
        val = data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return None
        return val

    def _map_severity_to_risk(self, severity: ControlSeverityEnum) -> float:
        mapping = {
            ControlSeverityEnum.CRITICAL: 9.00,
            ControlSeverityEnum.HIGH: 7.50,
            ControlSeverityEnum.MEDIUM: 5.00,
            ControlSeverityEnum.LOW: 2.50,
        }
        return mapping.get(severity, 5.00)
