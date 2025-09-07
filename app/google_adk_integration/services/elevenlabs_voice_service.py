# app/google_adk_integration/services/elevenlabs_voice_service.py
import httpx
import base64
import logging
from typing import Dict, Any, Optional
import os
import asyncio

logger = logging.getLogger(__name__)


class ElevenLabsVoiceService:
    """ElevenLabs Text-to-Speech service for high-quality Hindi voice"""

    def __init__(self):
        self.api_key = os.getenv("ELEVEN_LABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"

        # Hindi voice IDs (you can replace these with your preferred voices)
        self.voice_ids = {
            "hindi_male": "pMsXgVXv3BLzUgSXRplE",  # Adam - good for Hindi
            "hindi_female": "8FsOrsZSELg9otqX9nPu",  # Bella - good for Hindi
            "english_male": "pNInz6obpgDQGcFmaJgB",  # Adam
            "english_female": "21m00Tcm4TlvDq8ikWAM"  # Rachel
        }

        # Default voice settings optimized for Hindi
        self.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True
        }

    async def text_to_speech(
            self,
            text: str,
            voice_type: str = "hindi_male",
            language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Convert text to speech using ElevenLabs API

        Args:
            text (str): Text to convert to speech
            voice_type (str): Voice type (hindi_male, hindi_female, english_male, english_female)
            language (str): Language code (hi for Hindi, en for English)

        Returns:
            Dict containing audio data and metadata
        """
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "message": "ElevenLabs API key not configured"
                }

            # Select appropriate voice based on language and type
            if language.startswith("hi"):
                voice_id = self.voice_ids.get(f"hindi_{voice_type.split('_')[-1]}", self.voice_ids["hindi_male"])
            else:
                voice_id = self.voice_ids.get(voice_type, self.voice_ids["english_male"])

            # Prepare the request
            url = f"{self.base_url}/text-to-speech/{voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",  # Best model for Hindi
                "voice_settings": self.voice_settings
            }

            # Make the API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data, headers=headers)

                if response.status_code == 200:
                    # Convert audio to base64 for web transmission
                    audio_content = response.content
                    audio_base64 = base64.b64encode(audio_content).decode('utf-8')

                    return {
                        "status": "success",
                        "audio_data": audio_base64,
                        "audio_format": "mp3",
                        "voice_id": voice_id,
                        "text": text,
                        "language": language,
                        "size_bytes": len(audio_content)
                    }
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return {
                        "status": "error",
                        "message": f"Voice generation failed: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return {
                "status": "error",
                "message": f"Text-to-speech failed: {str(e)}"
            }

    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from ElevenLabs"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "API key not configured"}

            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    voices_data = response.json()
                    return {
                        "status": "success",
                        "voices": voices_data["voices"]
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to fetch voices: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return {
                "status": "error",
                "message": f"Voice list error: {str(e)}"
            }

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration"""
        return {
            "service_name": "ElevenLabs Voice Service",
            "api_configured": bool(self.api_key),
            "available_voices": list(self.voice_ids.keys()),
            "supported_languages": ["Hindi", "English", "Multilingual"],
            "audio_format": "MP3",
            "max_characters": 5000,  # ElevenLabs limit
            "features": [
                "High-quality Hindi TTS",
                "Multiple voice options",
                "Real-time generation",
                "Web-optimized audio"
            ]
        }

    async def generate_voice_for_farming_response(
            self,
            text: str,
            user_language: str = "hi",
            response_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Generate voice specifically optimized for farming responses

        Args:
            text (str): Farming advice text
            user_language (str): User's preferred language
            response_type (str): Type of response (crop_health, weather, market, etc.)
        """
        try:
            # Clean and optimize text for speech
            speech_text = self._optimize_text_for_speech(text, response_type)

            # Select appropriate voice based on response type
            if response_type == "crop_health":
                voice_type = "hindi_male"  # Authoritative for medical advice
            elif response_type == "weather":
                voice_type = "hindi_female"  # Calm for weather updates
            elif response_type == "market":
                voice_type = "hindi_male"  # Professional for market data
            else:
                voice_type = "hindi_male"  # Default

            # Generate voice
            result = await self.text_to_speech(
                text=speech_text,
                voice_type=voice_type,
                language=user_language
            )

            if result["status"] == "success":
                result["response_type"] = response_type
                result["optimized_text"] = speech_text

            return result

        except Exception as e:
            logger.error(f"Farming voice generation error: {e}")
            return {
                "status": "error",
                "message": f"Voice generation failed: {str(e)}"
            }

    def _optimize_text_for_speech(self, text: str, response_type: str) -> str:
        """Optimize text for better speech synthesis"""
        try:
            # Remove markdown formatting
            speech_text = text.replace("**", "").replace("*", "")
            speech_text = speech_text.replace("#", "").replace("`", "")

            # Replace technical symbols with words
            speech_text = speech_text.replace("₹", "रुपये ")
            speech_text = speech_text.replace("%", " प्रतिशत")
            speech_text = speech_text.replace("°C", " डिग्री सेल्सियस")
            speech_text = speech_text.replace("km", " किलोमीटर")
            speech_text = speech_text.replace("&", " और ")

            # Add pauses for better comprehension
            if response_type == "crop_health":
                speech_text = speech_text.replace("।", "। (pause) ")
                speech_text = speech_text.replace("तुरंत", " तुरंत (emphasis) ")
            elif response_type == "market":
                speech_text = speech_text.replace("कीमत", " (pause) कीमत")
                speech_text = speech_text.replace("बाज़ार", " (pause) बाज़ार")

            # Limit length for better performance
            if len(speech_text) > 1000:
                # Find good breaking point
                sentences = speech_text.split("।")
                truncated = ""
                for sentence in sentences:
                    if len(truncated + sentence) < 950:
                        truncated += sentence + "।"
                    else:
                        break
                speech_text = truncated + " और अधिक जानकारी के लिए पूछें।"

            return speech_text.strip()

        except Exception as e:
            logger.error(f"Text optimization error: {e}")
            return text  # Return original text if optimization fails