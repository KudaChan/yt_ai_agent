import logging
import os
from typing import Dict, Any, List
import google.generativeai as genai
import asyncio

from app.agents.base_agent import BaseAgent
from app.kafka import SUMMARY_RESULTS, VALIDATED_SUMMARIES

logger = logging.getLogger(__name__)

class ValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Validation",
            input_topic=SUMMARY_RESULTS,
            output_topic=VALIDATED_SUMMARIES,
            group_id="validation_group"
        )
        # Initialize Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.error("GOOGLE_API_KEY not set, Gemini API will not work")
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Validate summary against transcript and key points"""
        job_id = message.get("job_id")
        transcript = message.get("transcript", "")
        key_points = message.get("key_points", [])
        summary = message.get("summary", "")
        title = message.get("title", "")
        
        logger.info(f"Validating summary for job {job_id}")
        
        try:
            # Validate summary
            validation_result = await self.validate_summary(transcript, key_points, summary, title)
            
            # If validation failed, adjust the summary
            if not validation_result["is_valid"]:
                adjusted_summary = await self.adjust_summary(transcript, key_points, summary, title, 
                                                           validation_result["issues"])
                summary = adjusted_summary
            
            return {
                "job_id": job_id,
                "video_id": message.get("video_id"),
                "video_url": message.get("video_url"),
                "title": title,
                "channel": message.get("channel", ""),
                "summary": summary,
                "key_points": key_points,
                "validation_result": validation_result,
                "status": "completed"  # Final status
            }
        except Exception as e:
            logger.error(f"Error validating summary for job {job_id}: {str(e)}")
            raise
    
    async def validate_summary(self, transcript: str, key_points: List[str], 
                              summary: str, title: str) -> Dict[str, Any]:
        """Validate summary against transcript and key points"""
        try:
            # Format key points as string
            key_points_text = "\n".join([f"- {point}" for point in key_points])
            
            # Create prompt for validation
            prompt = f"""
            Title: {title}
            
            Key Points:
            {key_points_text}
            
            Summary:
            {summary}
            
            Please validate if the summary accurately reflects the key points.
            Check for:
            1. Factual accuracy - Does the summary contain information not in the key points?
            2. Completeness - Does the summary cover all key points?
            3. Coherence - Is the summary well-structured and logical?
            
            Return your validation in this format:
            - is_valid: [true/false]
            - issues: [list of issues if any, or "None" if valid]
            """
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Add timeout handling
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Validation API call timed out for title: {title}")
                return {
                    "is_valid": True,  # Assume valid on timeout
                    "issues": ["Validation timed out, proceeding with original summary"]
                }
            
            # Parse validation result
            validation_text = response.text
            is_valid = "is_valid: true" in validation_text.lower()
            
            # Extract issues
            issues = []
            if not is_valid:
                issues_section = validation_text.split("issues:")[-1].strip()
                issues = [issue.strip().lstrip('- ') for issue in issues_section.split('\n') 
                         if issue.strip() and not issue.strip().lower() == "none"]
            
            return {
                "is_valid": is_valid,
                "issues": issues
            }
        except Exception as e:
            logger.error(f"Error validating summary: {str(e)}")
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"]
            }
    
    async def adjust_summary(self, transcript: str, key_points: List[str], 
                            summary: str, title: str, issues: List[str]) -> str:
        """Adjust summary based on validation issues"""
        try:
            # Format key points and issues as strings
            key_points_text = "\n".join([f"- {point}" for point in key_points])
            issues_text = "\n".join([f"- {issue}" for issue in issues])
            
            # Create prompt for summary adjustment
            prompt = f"""
            Title: {title}
            
            Key Points:
            {key_points_text}
            
            Current Summary:
            {summary}
            
            Issues with the current summary:
            {issues_text}
            
            Please rewrite the summary to address all the issues mentioned above.
            The new summary should be 3-5 paragraphs, coherent, and accurately reflect all key points.
            """
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            logger.error(f"Error adjusting summary: {str(e)}")
            return summary  # Return original summary if adjustment fails
