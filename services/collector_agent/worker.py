import asyncio
import inspect
import json
import logging
import os
from typing import Callable, Optional

from azure.core.exceptions import AzureError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.queue.aio import QueueClient
from pydantic import ValidationError

from services.collector_agent.models import CollectionResult, ScanJobMessage

logger = logging.getLogger("collector_agent.worker")


class QueueConsumerWorker:
    def __init__(
        self,
        queue_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        storage_account_name: Optional[str] = None,
        poll_interval: float = 5.0,
        visibility_timeout: int = 60,
        handler: Optional[Callable[[ScanJobMessage], CollectionResult]] = None,
    ):
        self.queue_name = queue_name or os.getenv("AZURE_STORAGE_QUEUE_NAME", "evidence-jobs")
        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.storage_account_name = storage_account_name or os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.poll_interval = poll_interval
        self.visibility_timeout = visibility_timeout
        self.handler = handler or self._default_handler
        self.is_running = False
        self._queue_client: Optional[QueueClient] = None

    async def _get_queue_client(self) -> QueueClient:
        if self._queue_client is not None:
            return self._queue_client

        if self.connection_string:
            logger.info("Initializing QueueClient via Connection String...")
            self._queue_client = QueueClient.from_connection_string(
                conn_str=self.connection_string,
                queue_name=self.queue_name,
            )
        elif self.storage_account_name:
            logger.info("Initializing QueueClient via DefaultAzureCredential Managed Identity...")
            account_url = f"https://{self.storage_account_name}.queue.core.windows.net"
            credential = DefaultAzureCredential()
            self._queue_client = QueueClient(
                account_url=account_url,
                queue_name=self.queue_name,
                credential=credential,
            )
        else:
            raise ValueError(
                "Neither AZURE_STORAGE_CONNECTION_STRING nor AZURE_STORAGE_ACCOUNT_NAME is configured."
            )

        return self._queue_client

    async def start(self):
        self.is_running = True
        logger.info(f"Starting Storage Queue worker loop for queue '{self.queue_name}'...")
        queue_client = await self._get_queue_client()

        async with queue_client:
            while self.is_running:
                try:
                    messages = queue_client.receive_messages(
                        messages_per_page=1,
                        visibility_timeout=self.visibility_timeout,
                    )
                    has_processed_message = False

                    async for message in messages:
                        has_processed_message = True
                        await self._process_single_message(queue_client, message)

                    if not has_processed_message:
                        logger.debug(f"Queue '{self.queue_name}' empty. Sleeping {self.poll_interval}s...")
                        await asyncio.sleep(self.poll_interval)

                except asyncio.CancelledError:
                    logger.info("Queue worker loop cancelled. Shutting down gracefully...")
                    self.is_running = False
                    break
                except AzureError as ae:
                    logger.error(f"Azure Storage Queue error: {ae}. Retrying in {self.poll_interval}s...")
                    await asyncio.sleep(self.poll_interval)
                except Exception as ex:
                    logger.error(f"Unexpected error in queue worker loop: {ex}", exc_info=True)
                    await asyncio.sleep(self.poll_interval)

    async def _process_single_message(self, queue_client: QueueClient, message):
        logger.info(f"Dequeued message ID: {message.id} (pop_count={message.pop_count})")
        try:
            raw_content = message.content
            if isinstance(raw_content, bytes):
                raw_content = raw_content.decode("utf-8")

            payload = json.loads(raw_content)
            scan_job = ScanJobMessage.model_validate(payload)
            logger.info(f"Parsed scan job: job_id={scan_job.job_id}, collector_type={scan_job.collector_type}")

            # Execute job handler
            result = await self._execute_handler(scan_job)
            logger.info(f"Scan job executed successfully: status={result.status}")

            # Delete message from queue upon successful processing
            await queue_client.delete_message(message.id, message.pop_receipt)
            logger.info(f"Successfully processed and deleted message ID: {message.id}")

        except json.JSONDecodeError as jde:
            logger.error(f"Failed to parse JSON content for message {message.id}: {jde}")
            # Delete malformed poison message
            await queue_client.delete_message(message.id, message.pop_receipt)
        except ValidationError as ve:
            logger.error(f"Invalid message payload schema for message {message.id}: {ve}")
            await queue_client.delete_message(message.id, message.pop_receipt)
        except Exception as ex:
            logger.error(f"Error processing scan job message {message.id}: {ex}", exc_info=True)

    async def _execute_handler(self, scan_job: ScanJobMessage) -> CollectionResult:
        if inspect.iscoroutinefunction(self.handler):
            return await self.handler(scan_job)
        return self.handler(scan_job)

    def _default_handler(self, scan_job: ScanJobMessage) -> CollectionResult:
        return CollectionResult(
            job_id=scan_job.job_id,
            control_id=scan_job.control_id,
            collector_type=scan_job.collector_type,
            source_resource_id=scan_job.target_resource_id,
            status="PENDING_REVIEW",
            metadata={"collector_agent_version": "1.0.0"},
        )

    def stop(self):
        logger.info("Stopping QueueConsumerWorker...")
        self.is_running = False
