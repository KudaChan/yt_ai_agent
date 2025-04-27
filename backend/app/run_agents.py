import asyncio
import logging
import signal
import sys
from app.agents.transcription_agent import TranscriptionAgent
from app.agents.keypoint_extraction_agent import KeypointExtractionAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.storage.memory_storage import MemoryStorage
from app.kafka import KafkaManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
storage = MemoryStorage()

async def run_agents():
    try:
        # Initialize Kafka first and wait for it to be ready
        kafka_manager = KafkaManager()
        await kafka_manager.initialize_kafka(max_retries=10, retry_delay=3)
        
        # Create agents
        transcription_agent = TranscriptionAgent()
        keypoint_extraction_agent = KeypointExtractionAgent()
        summary_agent = SummaryAgent()
        validation_agent = ValidationAgent()
        
        # Run agents
        await asyncio.gather(
            transcription_agent.run(),
            keypoint_extraction_agent.run(),
            summary_agent.run(),
            validation_agent.run()
        )
    except Exception as e:
        logger.error(f"Error running agents: {str(e)}")
        raise

def main():
    # Use new event loop to avoid deprecation warning
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Register signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))
    
    try:
        loop.run_until_complete(run_agents())
    except Exception as e:
        logger.error(f"Failed to run agents: {e}")
        sys.exit(1)
    finally:
        loop.close()
        logger.info("Successfully shutdown agents")

async def shutdown(signal, loop):
    """Shutdown gracefully"""
    logger.info(f"Received exit signal {signal.name}...")
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Shutdown complete")
    loop.stop()

if __name__ == "__main__":
    main()
