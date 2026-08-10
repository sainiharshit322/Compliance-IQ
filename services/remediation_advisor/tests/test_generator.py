from services.remediation_advisor.generator import RemediationAdvisorGenerator
from services.remediation_advisor.schemas import RemediationAdvisorInput


def test_remediation_generator_storage_encryption():
    input_data = RemediationAdvisorInput(
        control_code="CC6.1",
        framework="SOC2_TYPE2",
        failed_conditions=["Property 'encryption.requireInfrastructureEncryption' is false."],
        target_resource_id="/subscriptions/000/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/stprod01",
        gap_summary="Storage account 'stprod01' lacks infrastructure-level encryption.",
    )

    generator = RemediationAdvisorGenerator()
    output = generator.generate_remediation(input_data)

    assert output.control_code == "CC6.1"
    assert "azurerm_storage_account" in output.advisory_terraform_snippet
    assert "stprod01" in output.advisory_terraform_snippet
    assert output.azure_cli_command.startswith("az storage account update")
    assert output.impact_analysis.requires_recreation is True
    assert output.explanation is not None


def test_remediation_generator_entra_mfa():
    input_data = RemediationAdvisorInput(
        control_code="ENTRA_MFA",
        framework="SOC2_TYPE2",
        failed_conditions=["Service user accounts missing MFA registration."],
        target_resource_id="tenant-complianceiq-dev",
        gap_summary="Entra ID tenant has non-MFA registered admin users.",
    )

    generator = RemediationAdvisorGenerator()
    output = generator.generate_remediation(input_data)

    assert output.control_code == "ENTRA_MFA"
    assert "azuread_conditional_access_policy" in output.advisory_terraform_snippet
    assert output.azure_cli_command.startswith("az rest")
    assert output.impact_analysis.requires_recreation is False


def test_remediation_generator_github_pr_rules():
    input_data = RemediationAdvisorInput(
        control_code="GITHUB_PR_RULES",
        framework="ISO_27001_2022",
        failed_conditions=["Branch protection missing on master."],
        target_resource_id="ComplianceIQ/compliance-core",
        gap_summary="Repository master branch lacks mandatory code owner reviews.",
    )

    generator = RemediationAdvisorGenerator()
    output = generator.generate_remediation(input_data)

    assert output.control_code == "GITHUB_PR_RULES"
    assert "github_branch_protection" in output.advisory_terraform_snippet
    assert "master" in output.advisory_terraform_snippet
    assert output.azure_cli_command.startswith("gh api")
    assert output.impact_analysis.requires_recreation is False
