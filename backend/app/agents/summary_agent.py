
import logging
import os
from typing import Dict, Any, List
import google.generativeai as genai

from app.agents.base_agent import BaseAgent
from app.kafka import KEYPOINTS_RESULTS, SUMMARY_RESULTS

logger = logging.getLogger(__name__)

class SummaryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Summary",
            input_topic=KEYPOINTS_RESULTS,  # Now takes input from keypoints
            output_topic=SUMMARY_RESULTS,
            group_id="summary_group"
        )
        # Initialize Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.error("GOOGLE_API_KEY not set, Gemini API will not work")
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary from key points"""
        job_id = message.get("job_id")
        key_points = message.get("key_points", [])
        title = message.get("title", "")
        transcript = message.get("transcript", "")  # Keep transcript for context
        
        logger.info(f"Generating summary for job {job_id}")
        
        try:
            # Generate summary using Gemini API and key points
            summary = await self.generate_summary(transcript, title, key_points)
            
            return {
                "job_id": job_id,
                "video_id": message.get("video_id"),
                "video_url": message.get("video_url"),
                "title": title,
                "channel": message.get("channel", ""),
                "transcript": transcript,
                "key_points": key_points,
                "summary": summary,
                "status": "summary_completed"
            }
        except Exception as e:
            logger.error(f"Error generating summary for job {job_id}: {str(e)}")
            raise
    
    async def generate_summary(self, transcript: str, title: str, key_points: List[str]) -> str:
        """Generate summary using Gemini API and key points"""
        try:
            # Format key points as string
            key_points_text = "\n".join([f"- {point}" for point in key_points])
            
            # Create prompt for summary
            prompt = f"""
            Title: {title}
            
            Key Points:
            {key_points_text}
            
            Please provide a concise summary of this video content in 3-5 paragraphs.
            Focus on the main points and key information provided in the key points above.
            The summary should be coherent, well-structured, and capture the essence of the video.
            """
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            logger.error(f"Error generating summary with Gemini API: {str(e)}")
            return f"Failed to generate summary: {str(e)}"
    
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

