import logging
import re
from typing import Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import os

from app.agents.base_agent import BaseAgent
from app.kafka import VIDEO_SUMMARY_REQUESTS, TRANSCRIPTION_RESULTS

logger = logging.getLogger(__name__)

class TranscriptionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TranscriptionAgent",
            input_topic=VIDEO_SUMMARY_REQUESTS,
            output_topic=TRANSCRIPTION_RESULTS,
            group_id="transcription_group"
        )
        logger.info("TranscriptionAgent initialized with input_topic=%s, output_topic=%s", 
                   VIDEO_SUMMARY_REQUESTS, TRANSCRIPTION_RESULTS)
        # We'll make YouTube API optional
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.use_youtube_api = False
        
        if self.youtube_api_key:
            try:
                # Test the API key with a simple request
                youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
                self.use_youtube_api = True
                logger.info("YouTube API initialized successfully")
            except Exception as e:
                logger.warning(f"YouTube API initialization failed: {str(e)}")
                logger.warning("Will proceed without YouTube API for video details")
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a video URL and extract transcript and metadata"""
        job_id = message.get("job_id")
        video_url = message.get("video_url")
        language = message.get("language", "en")
        
        logger.info(f"Processing video {video_url} for job {job_id}")
        
        try:
            # Extract video ID from URL
            video_id = self.extract_video_id(video_url)
            logger.debug(f"Extracted video ID: {video_id}")
            if not video_id:
                raise ValueError(f"Invalid YouTube URL: {video_url}")
            
            # Get video details
            logger.debug(f"Getting video details for {video_id}")
            video_details = self.get_video_details(video_id)
            
            # Get transcript
            logger.debug(f"Getting transcript for {video_id}")
            transcript = self.get_transcript(video_id, language)
            logger.debug(f"Transcript length: {len(transcript)}")
            
            result = {
                "job_id": job_id,
                "video_id": video_id,
                "video_url": video_url,
                "title": video_details.get("title", ""),
                "channel": video_details.get("channel", ""),
                "transcript": transcript,
                "language": language,
                "status": "transcription_completed"
            }
            logger.info(f"Successfully processed video {video_id}, returning result")
            return result
        except Exception as e:
            logger.error(f"Error processing video {video_url}: {str(e)}", exc_info=True)
            raise
    
    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)',
            r'(?:youtube\.com\/embed\/)([^&\n?]+)',
            r'(?:youtube\.com\/v\/)([^&\n?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get video details using YouTube API if available, otherwise extract from transcript"""
        if not self.use_youtube_api:
            logger.info(f"YouTube API not available, using video ID as title for {video_id}")
            return {
                "title": f"YouTube Video {video_id}",
                "channel": "Unknown Channel",
                "description": ""
            }
        
        try:
            youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            response = youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not response['items']:
                return {"title": f"YouTube Video {video_id}", "channel": "Unknown Channel"}
            
            snippet = response['items'][0]['snippet']
            return {
                "title": snippet.get('title', ''),
                "channel": snippet.get('channelTitle', ''),
                "description": snippet.get('description', '')
            }
        except Exception as e:
            logger.error(f"Error getting video details: {str(e)}")
            # Fallback to using video ID as title
            return {
                "title": f"YouTube Video {video_id}",
                "channel": "Unknown Channel",
                "description": ""
            }
    
    def get_transcript(self, video_id: str, language: str = "en") -> str:
        """Get video transcript"""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            full_transcript = " ".join([item['text'] for item in transcript_list])
            return full_transcript
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            raise ValueError(f"Could not retrieve transcript: {str(e)}")
