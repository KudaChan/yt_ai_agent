import os
import asyncio
import logging
import aiokafka
import json
import datetime
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaError
from typing import Callable, Optional, Any, Dict, Awaitable
from .consumer import KafkaConsumer
from .producer import KafkaProducer

# Main processing pipeline topics
VIDEO_SUMMARY_REQUESTS = "video_summary_requests"
TRANSCRIPTION_RESULTS = "transcription_results"
KEYPOINTS_RESULTS = "keypoints_results"
SUMMARY_RESULTS = "summary_results"
VALIDATED_SUMMARIES = "validated_summaries"

# Error and management topics
SUMMARY_ERRORS = "summary_errors"
AGENT_HEARTBEATS = "agent_heartbeats"

# List of all topics that need to be created
ALL_TOPICS = [
    VIDEO_SUMMARY_REQUESTS,
    TRANSCRIPTION_RESULTS,
    KEYPOINTS_RESULTS,
    SUMMARY_RESULTS,
    VALIDATED_SUMMARIES,
    SUMMARY_ERRORS,
    AGENT_HEARTBEATS
]

logger = logging.getLogger(__name__)

class KafkaManager:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumers = {}
        self.producer = None
        self.initialized = False
        self.admin_client = None
        logger.info(f"KafkaManager initialized with bootstrap servers: {self.bootstrap_servers}")

    async def create_topic(self):
        try:
            self.admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers
            )
            await self.admin_client.start()

            topic_list = [
                NewTopic(
                    name = topic, 
                    num_partitions=1, 
                    replication_factor=1
                )
                for topic in ALL_TOPICS
            ]

            await self.admin_client.create_topics(
                new_topics=topic_list, 
                validate_only=False,
                timeout_ms=10000
            )
            logger.info(f"Kafka topics created successfully: {ALL_TOPICS}")

        except KafkaError as e:
            logger.error(f"Failed to create Kafka topics: {e}")
        finally:
            if self.admin_client:
                await self.admin_client.close()
    
    async def start_producer(self):
        if not self.producer:
            self.producer = KafkaProducer(self.bootstrap_servers)
            await self.producer.start()
            logger.info("Kafka producer started successfully")

    async def stop_producer(self):
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")

    async def create_consumer(self, topic, group_id, callback):
        """Create a Kafka consumer for a topic"""
        if not self.initialized:
            logger.warning("Kafka manager not initialized. Initializing now...")
            await self.initialize_kafka()
            
        consumer_key = f"{topic}_{group_id}"
        if consumer_key in self.consumers:
            logger.warning(f"Consumer for {consumer_key} already exists")
            return self.consumers[consumer_key]["consumer"]
            
        logger.info(f"Creating consumer for topic {topic} with group {group_id}")
        consumer = KafkaConsumer(
            bootstrap_servers=self.bootstrap_servers,
            topic=topic,
            group_id=group_id,
            callback=callback
        )
        
        # Start the consumer and store the task
        task = await consumer.start()
        self.consumers[consumer_key] = {
            "consumer": consumer,
            "task": task
        }
        logger.info(f"Consumer created and started for {topic} with group {group_id}")
        return consumer

    async def shutdown(self):
        try:
            for consumer_key, consumer_data in self.consumers.items():
                if consumer_data["consumer"]:
                    await consumer_data["consumer"].stop()
                if consumer_data["task"]:
                    consumer_data["task"].cancel()
            await self.stop_producer()
            self.initialized = False
            logger.info("Kafka shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during Kafka shutdown: {e}")

    async def initialize_kafka(self, max_retries=5, retry_delay=5):
        """Initialize Kafka connections with retry logic"""
        if self.initialized:
            logger.info("Kafka already initialized")
            return
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Create topics first
                await self.create_topic()
                
                # Create producer
                await self.start_producer()
                
                # Make sure we have a consumer for validated_summaries
                self.add_consumer_handler("validated_summaries", self.handle_validated_summaries)
                
                self.initialized = True
                logger.info("Kafka initialized successfully")
                return
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to initialize Kafka (attempt {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    logger.error("Max retries reached. Failed to initialize Kafka.")
                    raise
                await asyncio.sleep(retry_delay)

    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        if not self.initialized:
            logger.warning("Kafka manager not initialized. Initializing now...")
            await self.initialize_kafka()
            
        if not self.producer:
            await self.start_producer()
        
        try:
            success = await self.producer.send_message(topic, message, key)
            return success
        except Exception as e:
            logger.error(f"Failed to send message to topic {topic}: {e}")
            return False

    async def handle_summary_results(self, message):
        """Handle summary results from the validation agent"""
        job_id = message.get("job_id")
        if not job_id:
            logger.error("Received summary result without job_id")
            return
        
        # Store the complete result
        from app.storage.memory_storage import MemoryStorage
        storage = MemoryStorage()
        storage.store_job(job_id, message)
        
        logger.info(f"Stored final summary result for job {job_id}")

    async def register_agent_consumer(self, agent_name, input_topic, group_id, callback):
        """Register a consumer for an agent with proper error handling"""
        try:
            if not self.initialized:
                logger.warning(f"Kafka manager not initialized when registering {agent_name}. Initializing now...")
                await self.initialize_kafka()
            
            consumer = await self.create_consumer(input_topic, group_id, callback)
            logger.info(f"Registered consumer for {agent_name} on topic {input_topic}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to register consumer for {agent_name}: {e}")
            # Send error to error topic
            error_msg = {
                "agent": agent_name,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
            await self.send_message(SUMMARY_ERRORS, error_msg)
            return None

    async def handle_validated_summaries(self, message):
        """Handle validated summaries from the validation agent"""
        job_id = message.get("job_id")
        if not job_id:
            logger.error("Received validated summary without job_id")
            return
        
        # Store the complete result
        from app.storage.memory_storage import MemoryStorage
        storage = MemoryStorage()
        
        # Ensure status is set to completed
        message["status"] = "completed"
        
        # Store the job data
        storage.store_job(job_id, message)
        
        logger.info(f"Stored final validated summary for job {job_id}")

    async def add_consumer_handler(self, topic, callback):
        """Add a consumer handler for a specific topic"""
        consumer_group = f"app-{topic}-group"
        logger.info(f"Adding consumer handler for topic {topic} with group {consumer_group}")
        
        try:
            consumer = await self.create_consumer(topic, consumer_group, callback)
            return consumer
        except Exception as e:
            logger.error(f"Failed to add consumer handler for topic {topic}: {e}")
            return None
