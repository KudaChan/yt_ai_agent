import logging
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)

class MemoryStorage:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MemoryStorage, cls).__new__(cls)
                cls._instance.jobs = {}
        return cls._instance
    
    def store_job(self, job_id: str, data: Dict[str, Any]) -> None:
        """Store job data"""
        # Update existing job with new data
        if job_id in self.jobs:
            self.jobs[job_id].update(data)
        else:
            self.jobs[job_id] = data
        
        logger.info(f"Stored job {job_id} with status: {data.get('status', 'unknown')}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data"""
        return self.jobs.get(job_id)
    
    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all jobs"""
        return self.jobs
    
    def delete_job(self, job_id: str) -> bool:
        """Delete job data"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Deleted job {job_id}")
            return True
        return False
