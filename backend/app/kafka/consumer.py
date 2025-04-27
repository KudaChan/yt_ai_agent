import logging
from typing import Awaitable, Callable, Dict, Any
from aiokafka import AIOKafkaConsumer
import json
import asyncio


logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self,
                 bootstrap_servers: str, 
                 topic: str,
                 group_id: str, 
                 callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.callback = callback
        self.consumer = None
        self.task = None
        logger.info(f"KafkaConsumer initialized for topic {topic} with group {group_id}")

    async def start(self):
        """Create and start the consumer"""
        if self.consumer:
            logger.warning(f"Consumer for {self.topic} with group {self.group_id} already exists")
            return self.task

        logger.info(f"Creating consumer for topic {self.topic} with group ID {self.group_id}")
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True
        )

        # Start the consumer
        await self.consumer.start()
        logger.info(f"Consumer started for topic: {self.topic} with group ID: {self.group_id}")
        
        # Start consuming in a separate task
        self.task = asyncio.create_task(self._consume())
        return self.task

    async def _consume(self):
        """Internal method to consume messages"""
        try:
            logger.info(f"Starting to consume messages from topic {self.topic}")
            async for message in self.consumer:
                try:
                    logger.debug(f"Received message from topic {self.topic}: {message.value}")
                    value = message.value  # Already deserialized by consumer
                    await self.callback(value)
                except Exception as e:
                    logger.error(f"Error processing message from {self.topic}: {e}", exc_info=True)
        except asyncio.CancelledError:
            logger.info(f"Consumer task for {self.topic} was cancelled")
        except Exception as e:
            logger.error(f"Error in consumer for {self.topic}: {e}", exc_info=True)
    
    async def stop(self):
        """Stop the consumer"""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
            
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
            
        logger.info(f"Consumer for {self.topic} with group {self.group_id} stopped")
