import json
from unittest.mock import AsyncMock, MagicMock
import pytest

from services.collector_agent.models import CollectorType, ScanJobMessage
from services.collector_agent.worker import QueueConsumerWorker


@pytest.mark.asyncio
async def test_scan_job_message_parsing():
    valid_payload = {
        "job_id": "11111111-1111-1111-1111-111111111111",
        "control_id": "22222222-2222-2222-2222-222222222222",
        "collector_type": "AZURE_POLICY",
        "target_resource_id": "/subscriptions/0000/resourceGroups/rg-test",
    }
    job = ScanJobMessage.model_validate(valid_payload)
    assert job.job_id == "11111111-1111-1111-1111-111111111111"
    assert job.collector_type == CollectorType.AZURE_POLICY


@pytest.mark.asyncio
async def test_worker_process_single_message_success():
    mock_queue_client = AsyncMock()
    mock_queue_client.delete_message = AsyncMock()

    mock_message = MagicMock()
    mock_message.id = "msg-001"
    mock_message.pop_receipt = "receipt-001"
    mock_message.pop_count = 1
    mock_message.content = json.dumps({
        "job_id": "33333333-3333-3333-3333-333333333333",
        "control_id": "44444444-4444-4444-4444-444444444444",
        "collector_type": "BLOB_IMMUTABILITY",
        "target_resource_id": "stcomplianceiqdev",
    })

    worker = QueueConsumerWorker(queue_name="evidence-jobs", connection_string="mock-conn-string")
    await worker._process_single_message(mock_queue_client, mock_message)

    # Verify message deletion was invoked
    mock_queue_client.delete_message.assert_called_once_with("msg-001", "receipt-001")


@pytest.mark.asyncio
async def test_worker_process_malformed_json_deletes_poison_message():
    mock_queue_client = AsyncMock()
    mock_queue_client.delete_message = AsyncMock()

    mock_message = MagicMock()
    mock_message.id = "msg-poison"
    mock_message.pop_receipt = "receipt-poison"
    mock_message.content = "INVALID_JSON_PAYLOAD{"

    worker = QueueConsumerWorker(queue_name="evidence-jobs", connection_string="mock-conn-string")
    await worker._process_single_message(mock_queue_client, mock_message)

    # Verify malformed poison message is deleted
    mock_queue_client.delete_message.assert_called_once_with("msg-poison", "receipt-poison")
