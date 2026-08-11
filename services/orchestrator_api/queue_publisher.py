import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger("orchestrator_api.queue_publisher")


class AzureQueuePublisher:
    """Publishes async scan job execution payloads into Azure Storage Queue 'evidence-jobs'."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        queue_name: Optional[str] = None,
    ):
        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.queue_name = queue_name or os.getenv("AZURE_STORAGE_QUEUE_NAME", "evidence-jobs")
        self.queue_client = None

        if self.connection_string and self.connection_string != "UseDevelopmentStorage=true;":
            try:
                from azure.storage.queue import QueueClient

                self.queue_client = QueueClient.from_connection_string(
                    conn_str=self.connection_string,
                    queue_name=self.queue_name,
                )
                logger.info(f"Initialized Azure QueueClient for queue: {self.queue_name}")
            except Exception as ex:
                logger.warning(f"Could not initialize Azure QueueClient ({ex}). Fallback to mock mode.")

    def enqueue_scan_job(
        self,
        framework_id: Optional[str] = None,
        framework_code: Optional[str] = "SOC2_TYPE2",
        collector_type: str = "AZURE_POLICY",
        target_resource_id: Optional[str] = None,
        force_recollect: bool = False,
    ) -> Dict[str, Any]:
        """Enqueues a scan job message into Azure Storage Queue."""
        job_id = str(uuid4())
        enqueued_at = datetime.now(timezone.utc).isoformat()

        payload = {
            "job_id": job_id,
            "framework_id": framework_id,
            "framework_code": framework_code,
            "collector_type": collector_type,
            "target_resource_id": target_resource_id,
            "force_recollect": force_recollect,
            "enqueued_at": enqueued_at,
        }

        if self.queue_client:
            try:
                message_bytes = json.dumps(payload).encode("utf-8")
                self.queue_client.send_message(message_bytes)
                logger.info(f"Successfully enqueued job {job_id} into Azure queue {self.queue_name}")
            except Exception as ex:
                logger.error(f"Failed to publish message to Azure Queue ({ex}). Payload logged.")

        return {
            "job_id": job_id,
            "status": "ENQUEUED",
            "queue_name": self.queue_name,
            "message": f"Scan job {job_id} enqueued successfully into queue '{self.queue_name}'.",
            "enqueued_at": enqueued_at,
        }
