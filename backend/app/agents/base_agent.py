import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import datetime

from app.kafka import KafkaManager

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name:str, input_topic: str, output_topic: str, group_id: str):
        self.name = name
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.group_id = group_id
        self.kafka_manager = KafkaManager()
        self.consumer = None
        self.heartbeat_task = None
        logger.info(f"{self.name} initialized with input_topic={input_topic}, output_topic={output_topic}")

    async def initialize(self):
        """Initialize the agent"""
        logger.info(f"Initializing {self.name}")
        
        # Initialize Kafka
        await self.kafka_manager.initialize_kafka()
        
        # Create consumer for input topic
        logger.info(f"{self.name} creating consumer for topic {self.input_topic}")
        self.consumer = await self.kafka_manager.create_consumer(
            topic=self.input_topic,
            group_id=self.group_id,
            callback=self.process_message
        )
        
        logger.info(f"{self.name} initialized successfully")
        return True

    async def run(self):
        """Start the agent"""
        logger.info(f"Starting {self.name}")
        
        try:
            # Initialize Kafka
            await self.kafka_manager.initialize_kafka()
            
            # Create consumer for input topic
            logger.info(f"{self.name} creating consumer for topic {self.input_topic}")
            self.consumer = await self.kafka_manager.create_consumer(
                topic=self.input_topic,
                group_id=self.group_id,
                callback=self.process_message
            )
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
            
            logger.info(f"{self.name} started successfully")
            
            # Keep the agent running
            while True:
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info(f"{self.name} task was cancelled")
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def process_message(self, message: Dict[str, Any]):
        job_id = message.get("job_id")
        
        if not job_id:
            logger.error(f"{self.name} received message without job_id")
            return
        
        logger.info(f"{self.name} processing job {job_id}")
        
        try:
            result = await self.process(message)
            if "job_id" not in result:
                result["job_id"] = job_id
            await self.kafka_manager.send_message(
                topic=self.output_topic,
                message=result,
                key=job_id
            )
            logger.info(f"{self.name} completed job {job_id}")
        except Exception as e:
            logger.error(f"{self.name} failed to process job {job_id}: {str(e)}")
            error_message = {
                "job_id": job_id,
                "agent": self.name,
                "error": str(e),
                "original_message": message
            }
            await self.kafka_manager.send_message(
                topic="summary_errors",
                message=error_message,
                key=job_id
            )

    @abstractmethod
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the message and return the result
        """
        pass
        
    async def shutdown(self):
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
                
        await self.kafka_manager.shutdown()
        logger.info(f"{self.name} agent shutdown")

    async def send_heartbeat(self):
        while True:
            try:
                await self.kafka_manager.send_message(
                    topic="agent_heartbeats",
                    message={"agent": self.name, "status": "alive", "timestamp": str(datetime.datetime.now())},
                    key=self.name
                )
                logger.debug(f"{self.name} sent heartbeat")
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                logger.info(f"{self.name} heartbeat task cancelled")
                raise
            except Exception as e:
                logger.error(f"Error sending heartbeat for {self.name}: {e}")
                await asyncio.sleep(10)  # Still sleep on error to avoid tight loop
    
    async def start(self):
        await self.initialize()
        self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
        logger.info(f"{self.name} agent started")

    async def stop(self):
        await self.shutdown()
        logger.info(f"{self.name} agent stopped")
