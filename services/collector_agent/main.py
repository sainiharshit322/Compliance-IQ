import asyncio
import logging
import signal
import sys
from dotenv import load_dotenv

from services.collector_agent.worker import QueueConsumerWorker

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("collector_agent")


async def main():
    logger.info("Initializing Evidence Collector Agent service...")
    worker = QueueConsumerWorker()

    loop = asyncio.get_running_loop()

    def shutdown_handler():
        logger.info("Received termination signal. Shutting down worker...")
        worker.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_handler)
        except NotImplementedError:
            # Signal handling not supported on Windows main loop in some contexts
            pass

    try:
        await worker.start()
    except Exception as ex:
        logger.error(f"Fatal error in Evidence Collector Agent: {ex}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
