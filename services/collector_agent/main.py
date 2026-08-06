"""
ComplianceIQ - Evidence Collector Agent
Entry point for asynchronous queue-driven evidence collection worker.
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("collector_agent")

async def main():
    logger.info("Starting Evidence Collector Agent worker loop...")

if __name__ == "__main__":
    asyncio.run(main())
