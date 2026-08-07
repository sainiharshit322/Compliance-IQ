from services.collector_agent.tools import check_blob_storage_immutability, scan_azure_policy_state


def test_scan_azure_policy_state_output_schema():
    sub_id = "00000000-0000-0000-0000-000000000000"
    res = scan_azure_policy_state(subscription_id=sub_id, resource_group="rg-prod")

    assert res["subscription_id"] == sub_id
    assert "timestamp" in res
    assert "total_resources_evaluated" in res
    assert "non_compliant_count" in res
    assert isinstance(res["evaluations"], list)
    assert len(res["evaluations"]) > 0

    first_eval = res["evaluations"][0]
    assert "resource_id" in first_eval
    assert "policy_assignment_name" in first_eval
    assert "compliance_state" in first_eval


def test_scan_azure_policy_state_all_filter():
    sub_id = "00000000-0000-0000-0000-000000000000"
    res = scan_azure_policy_state(subscription_id=sub_id, compliance_state_filter="All")
    assert res["total_resources_evaluated"] >= 1


def test_check_blob_storage_immutability_compliant_container():
    res = check_blob_storage_immutability(
        subscription_id="00000000-0000-0000-0000-000000000000",
        storage_account_name="stcomplianceiqdev",
        container_name="evidence-worm",
    )

    assert res["storage_account_name"] == "stcomplianceiqdev"
    assert res["container_name"] == "evidence-worm"
    assert res["has_immutability_policy"] is True
    assert res["is_locked"] is True
    assert res["legal_hold_status"] is True
    assert res["is_compliant"] is True


def test_check_blob_storage_immutability_non_compliant_container():
    res = check_blob_storage_immutability(
        subscription_id="00000000-0000-0000-0000-000000000000",
        storage_account_name="stcomplianceiqdev",
        container_name="public-logs",
    )

    assert res["container_name"] == "public-logs"
    assert res["has_immutability_policy"] is False
    assert res["is_locked"] is False
    assert res["is_compliant"] is False
