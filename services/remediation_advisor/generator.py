import json
import logging
import os
from typing import Any, Dict, Optional

from services.remediation_advisor.schemas import (
    ImpactAnalysis,
    RemediationAdvisorInput,
    RemediationAdvisorOutput,
)

logger = logging.getLogger("remediation_advisor.generator")

REMEDIATION_SYSTEM_PROMPT = """You are the ComplianceIQ Remediation Advisor Agent—an expert cloud infrastructure security architect.
Your job is to generate strictly advisory, production-ready infrastructure-as-code (Terraform HCL) and Azure CLI remediation snippets for non-compliant controls.

CRITICAL OPERATIONAL RULES:
1. You are STRICTLY ADVISORY. Never include instructions or commands that execute auto-remediation directly without human verification.
2. Provide valid HCL Terraform code using standard AzureRM provider syntax (`azurerm`).
3. Provide valid, copy-pasteable Azure CLI bash commands (`az ...`).
4. Include a clear explanation of why the change remedies the risk, and summarize potential breaking changes or service restart impacts.
5. Respond ONLY in valid JSON matching the required output schema.
"""


class RemediationAdvisorGenerator:
    def __init__(self, openai_client: Optional[Any] = None, model_name: str = "gpt-4o"):
        self.openai_client = openai_client
        self.model_name = os.getenv("OPENAI_MODEL", model_name)

    def generate_remediation(self, input_data: RemediationAdvisorInput) -> RemediationAdvisorOutput:
        """
        Main entrypoint generating advisory remediation snippets.
        Attempts GPT-4o JSON mode call if OpenAI API is configured;
        otherwise generates deterministic advisory HCL & Azure CLI templates.
        """
        logger.info(
            f"Generating remediation advisory for control '{input_data.control_code}' ({input_data.target_resource_id})..."
        )

        output: Optional[RemediationAdvisorOutput] = None

        if self._can_use_llm():
            try:
                output = self._generate_with_llm(input_data)
            except Exception as ex:
                logger.warning(f"LLM remediation generation failed ({ex}). Falling back to template generator.")

        if output is None:
            output = self._generate_with_templates(input_data)

        logger.info(f"Remediation advisory generated successfully for control '{output.control_code}'.")
        return output

    def _can_use_llm(self) -> bool:
        return (
            self.openai_client is not None
            or bool(os.getenv("OPENAI_API_KEY"))
            or bool(os.getenv("AZURE_OPENAI_API_KEY"))
        )

    def _generate_with_llm(self, input_data: RemediationAdvisorInput) -> RemediationAdvisorOutput:
        import openai

        client = self.openai_client or openai.OpenAI()

        response = client.chat.completions.create(
            model=self.model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": REMEDIATION_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(input_data.model_dump())},
            ],
            temperature=0.0,
        )

        content = response.choices[0].message.content
        raw_json = json.loads(content)
        return RemediationAdvisorOutput.model_validate(raw_json)

    def _generate_with_templates(self, input_data: RemediationAdvisorInput) -> RemediationAdvisorOutput:
        """Deterministic advisory snippet template generator for offline/testing environments."""
        code = input_data.control_code.upper()
        res_id = input_data.target_resource_id

        # Extract resource name from ID if path string
        res_name = res_id.split("/")[-1] if "/" in res_id else res_id

        if "CC6.1" in code or "ENCRYPTION" in input_data.gap_summary.upper():
            tf_snippet = (
                f'resource "azurerm_storage_account" "remediation" {{\n'
                f'  name                              = "{res_name}"\n'
                f'  resource_group_name               = "rg-complianceiq-prod"\n'
                f'  location                          = "eastus"\n'
                f'  account_tier                      = "Standard"\n'
                f'  account_replication_type          = "LRS"\n'
                f'  infrastructure_encryption_enabled = true\n'
                f'}}'
            )
            cli_cmd = (
                f"az storage account update --name {res_name} "
                f"--resource-group rg-complianceiq-prod --infrastructure-encryption true"
            )
            explanation = "Enables double infrastructure-level AES-256 encryption at rest for data storage components."
            impact = ImpactAnalysis(
                requires_recreation=True,
                estimated_downtime="Requires data migration to a new storage account. Estimated downtime: 1-2 hours.",
            )

        elif "MFA" in code or "ENTRA" in input_data.gap_summary.upper():
            tf_snippet = (
                'resource "azuread_conditional_access_policy" "enforce_mfa" {\n'
                '  display_name = "Enforce MFA for All Users"\n'
                '  state        = "enabled"\n'
                '  conditions {\n'
                '    users {\n'
                '      included_users = ["All"]\n'
                '    }\n'
                '    applications {\n'
                '      included_applications = ["All"]\n'
                '    }\n'
                '  }\n'
                '  grant_controls {\n'
                '    operator          = "OR"\n'
                '    built_in_controls = ["mfa"]\n'
                '  }\n'
                '}'
            )
            cli_cmd = "az rest --method POST --uri https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies --body @mfa_policy.json"
            explanation = "Creates a Microsoft Entra ID Conditional Access Policy enforcing Multi-Factor Authentication across all directory users."
            impact = ImpactAnalysis(
                requires_recreation=False,
                estimated_downtime="None. Users will be prompted for MFA upon next login session.",
            )

        elif "GITHUB" in code or "PR" in input_data.gap_summary.upper():
            tf_snippet = (
                f'resource "github_branch_protection" "master_protection" {{\n'
                f'  repository_id = "{res_name}"\n'
                f'  pattern       = "master"\n'
                f'  required_pull_request_reviews {{\n'
                f'    required_approving_review_count = 2\n'
                f'    require_code_owner_reviews      = true\n'
                f'    dismiss_stale_reviews           = true\n'
                f'  }}\n'
                f'  required_conversation_resolution = true\n'
                f'  enforce_admins                   = true\n'
                f'}}'
            )
            cli_cmd = (
                f"gh api --method PUT /repos/{input_data.target_resource_id}/branches/master/protection "
                f"-f required_approving_review_count=2 -f require_code_owner_reviews=true"
            )
            explanation = "Enforces GitHub branch protection requiring at least 2 approving reviews and code owner sign-off prior to merging."
            impact = ImpactAnalysis(
                requires_recreation=False,
                estimated_downtime="None. Directly affects future pull requests.",
            )

        else:
            tf_snippet = (
                f'resource "azurerm_resource_group" "remediation" {{\n'
                f'  name     = "rg-remediation-advisory"\n'
                f'  location = "eastus"\n'
                f'  tags = {{\n'
                f'    ControlCode = "{input_data.control_code}"\n'
                f'    Compliance  = "PendingHumanReview"\n'
                f'  }}\n'
                f'}}'
            )
            cli_cmd = f"az group create --name rg-remediation-advisory --location eastus --tags ControlCode={input_data.control_code}"
            explanation = f"Applies advisory remediation tag and configuration for non-compliant control {input_data.control_code}."
            impact = ImpactAnalysis(
                requires_recreation=False,
                estimated_downtime="None.",
            )

        return RemediationAdvisorOutput(
            control_code=input_data.control_code,
            advisory_terraform_snippet=tf_snippet,
            azure_cli_command=cli_cmd,
            explanation=explanation,
            impact_analysis=impact,
        )
