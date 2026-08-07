from services.collector_agent.tools import get_entra_id_mfa_status, read_github_pr_rules


def test_get_entra_id_mfa_status_output_schema():
    tenant_id = "00000000-0000-0000-0000-000000000000"
    res = get_entra_id_mfa_status(tenant_id=tenant_id)

    assert res["tenant_id"] == tenant_id
    assert "timestamp" in res
    assert "total_users_checked" in res
    assert "mfa_enforced_count" in res
    assert "mfa_disabled_count" in res
    assert "conditional_access_mfa_active" in res
    assert isinstance(res["user_summaries"], list)
    assert len(res["user_summaries"]) > 0


def test_get_entra_id_mfa_status_admin_only_filter():
    tenant_id = "00000000-0000-0000-0000-000000000000"
    res = get_entra_id_mfa_status(tenant_id=tenant_id, include_admin_roles_only=True)
    assert len(res["user_summaries"]) >= 1
    assert all(u["is_admin_role"] for u in res["user_summaries"])


def test_read_github_pr_rules_default_branch_master():
    res = read_github_pr_rules(repository_owner="ComplianceIQ", repository_name="compliance-core")

    assert res["repository"] == "ComplianceIQ/compliance-core"
    assert res["branch"] == "master"
    assert res["is_protected"] is True
    assert res["required_approving_review_count"] >= 1
    assert res["require_code_owner_reviews"] is True
    assert res["is_compliant"] is True


def test_read_github_pr_rules_custom_branch():
    res = read_github_pr_rules(
        repository_owner="ComplianceIQ",
        repository_name="compliance-core",
        branch_name="main",
    )

    assert res["branch"] == "main"
    assert res["is_protected"] is True
