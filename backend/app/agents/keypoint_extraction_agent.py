import logging
import os
from typing import Dict, Any, List
import google.generativeai as genai

from app.agents.base_agent import BaseAgent
from app.kafka import TRANSCRIPTION_RESULTS, KEYPOINTS_RESULTS

logger = logging.getLogger(__name__)

class KeypointExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="KeypointExtraction",
            input_topic=TRANSCRIPTION_RESULTS,
            output_topic=KEYPOINTS_RESULTS,
            group_id="keypoint_extraction_group"
        )
        # Initialize Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.error("GOOGLE_API_KEY not set, Gemini API will not work")
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key points from transcript"""
        job_id = message.get("job_id")
        transcript = message.get("transcript", "")
        title = message.get("title", "")
        
        logger.info(f"Extracting key points for job {job_id}")
        
        try:
            # Extract key points using Gemini API
            key_points = await self.extract_key_points(transcript, title)
            
            return {
                "job_id": job_id,
                "video_id": message.get("video_id"),
                "video_url": message.get("video_url"),
                "title": title,
                "channel": message.get("channel", ""),
                "transcript": transcript,
                "key_points": key_points,
                "status": "keypoints_completed"
            }
        except Exception as e:
            logger.error(f"Error extracting key points for job {job_id}: {str(e)}")
            raise
    
    async def extract_key_points(self, transcript: str, title: str) -> List[str]:
        """Extract key points using Gemini API"""
        try:
            # Truncate transcript if too long
            max_length = 30000  # Adjust based on Gemini API limits
            if len(transcript) > max_length:
                transcript = transcript[:max_length] + "..."
            
            # Create prompt for key points
            prompt = f"""
            Title: {title}
            
            Transcript:
            {transcript}
            
            Please extract 5-7 key points from this video content.
            Format each point as a single sentence or short paragraph.
            Return ONLY the list of key points, with each point on a new line starting with a dash (-).
            """
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            
            # Parse response to extract key points
            key_points_text = response.text
            key_points = [point.strip().lstrip('- ') for point in key_points_text.split('\n') 
                         if point.strip() and point.strip().startswith('-')]
            
            return key_points
        except Exception as e:
            logger.error(f"Error extracting key points with Gemini API: {str(e)}")
            return [f"Failed to extract key points: {str(e)}"]
    
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
            
            # Check if the result indicates a failure
            if result.get("status") == "failed":
                # Add completed status for the frontend to recognize it's done
                result["status"] = "completed"
                
                # Send directly to the final VALIDATED_SUMMARIES topic
                from app.kafka import VALIDATED_SUMMARIES
                await self.kafka_manager.send_message(
                    topic=VALIDATED_SUMMARIES,
                    message=result,
                    key=job_id
                )
                logger.info(f"{self.name} sent error for job {job_id} directly to final topic")
            else:
                # Normal processing - send to regular output topic
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
                "original_message": message,
                "video_url": message.get("video_url", ""),
                "status": "completed"  # Mark as completed for frontend
            }
            from app.kafka import VALIDATED_SUMMARIES
            await self.kafka_manager.send_message(
                topic=VALIDATED_SUMMARIES,
                message=error_message,
                key=job_id
            )
