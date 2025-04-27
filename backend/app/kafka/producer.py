import json
import logging
import aiokafka
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        
    async def start(self):
        try:
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None
            )
            await self.producer.start()
            logger.info("Kafka producer started.")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
            
    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped.")
            
    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        try:
            await self.producer.send_and_wait(topic, message, key=key)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka topic {topic}: {e}")
            return False
