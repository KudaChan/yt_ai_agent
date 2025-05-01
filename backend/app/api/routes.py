import datetime
import uuid
import os
import logging
from fastapi import APIRouter, HTTPException
from app.models.models import SummaryRequest
from app.kafka import KafkaManager
from app.storage.memory_storage import MemoryStorage

kafka_manager = KafkaManager()
storage = MemoryStorage()

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def root():
    return {
        "message": "YouTube Summarizer API is running!",
        "kafka_server": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "Not set"),
        "youtube_api_key": "Configured" if os.getenv("YOUTUBE_API_KEY") else "Not configured"
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

"""
Purpose: Submit a YouTube video URL for summarization
Use: Main entry point for users to request a video summary
Behavior: Processes the entire request synchronously
Returns: The complete summary result when processing is finished
Frontend: Will show a loading/processing state while waiting for the response
"""
@router.post("/api/v1/summarize")
async def request_summary(request: SummaryRequest):
    try:
        job_id = str(uuid.uuid4())

        message = {
            "job_id": job_id,
            "video_url": str(request.video_url),
            "language": request.language,
            "status": "processing",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Store initial job status
        storage.store_job(job_id, message)
       
        success = await kafka_manager.send_message(
            topic="video_summary_requests",
            message=message,
            key=job_id
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to queue summary request")
        
        return {
            "message": "Summary request submitted successfully",
            "job_id": job_id,
            "status": "processing",
            "video_url": str(request.video_url)
        }
    except Exception as e:
        logger.error(f"Error submitting summary request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@router.get("/api/v1/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a summary job"""
    job_data = storage.get_job(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job_id,
        "status": job_data.get("status", "unknown"),
        "video_url": job_data.get("video_url", ""),
        "timestamp": job_data.get("timestamp", "")
    }

@router.get("/api/v1/results/{job_id}")
async def get_job_results(job_id: str):
    """Get the results of a completed summary job"""
    job_data = storage.get_job(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job_data.get("status") != "completed":
        return {
            "job_id": job_id,
            "status": job_data.get("status", "unknown"),
            "message": "Job is still processing or has failed"
        }
    
    return {
        "job_id": job_id,
        "status": "completed",
        "video_url": job_data.get("video_url", ""),
        "title": job_data.get("title", ""),
        "channel": job_data.get("channel", ""),
        "summary": job_data.get("summary", ""),
        "error": job_data.get("error", ""),
        "key_points": job_data.get("key_points", []),
        "validation_result": job_data.get("validation_result", {}),
        "timestamp": job_data.get("timestamp", "")
    }

@router.get("/api/v1/debug/{job_id}")
async def debug_job_data(job_id: str):
    """Debug endpoint to get raw job data"""
    storage = MemoryStorage()
    
    job_data = storage.get_job(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job_id,
        "raw_data": job_data
    }
