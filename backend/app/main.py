import logging
import datetime
from app.kafka import KafkaManager, VALIDATED_SUMMARIES
from fastapi import FastAPI, HTTPException
from app.api import routes
from typing import Optional
from app.storage.memory_storage import MemoryStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(title = "YouTube Summarizer API")

# Initialize Kafka manager
kafka_manager = KafkaManager()

# Initialize memory storage
storage = MemoryStorage()

app.include_router(routes.router)

@app.on_event("startup")
async def startup_event():
    try:
        await kafka_manager.initialize_kafka()
        
        # Register handlers for result topics
        await kafka_manager.create_consumer(
            topic=VALIDATED_SUMMARIES,
            group_id="api_consumer_group",
            callback=kafka_manager.handle_validated_summaries
        )
        
        print("✅ Kafka initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Kafka: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await kafka_manager.shutdown()
        print("✅ Kafka shutdown successfully.")
    except Exception as e:
        print(f"❌ Failed to shutdown Kafka: {e}")
