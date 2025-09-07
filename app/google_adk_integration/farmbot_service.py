# app/google_adk_integration/farmbot_service.py - Updated with ElevenLabs
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import base64

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from .config.models import ChatResponse
from .agents.main_agent import create_main_farmbot_agent
from .services.elevenlabs_voice_service import ElevenLabsVoiceService

# Configure logging
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger(__name__)


class FarmBotService:
    """
    Enhanced FarmBot service with ElevenLabs voice integration
    """

    def __init__(self):
        self.session_service = None
        self.main_agent = None
        self.runner = None
        self.voice_service = ElevenLabsVoiceService()
        self.app_name = "farmbot_production"
        self.is_initialized = False

    async def initialize(self):
        """Initialize the FarmBot ADK service with voice capabilities"""
        try:
            logger.info("Initializing FarmBot ADK service with ElevenLabs voice...")

            # Create session service
            self.session_service = InMemorySessionService()
            logger.info("✅ Session service created")

            # Create main agent with all capabilities
            self.main_agent = create_main_farmbot_agent()
            logger.info(f"✅ Main agent '{self.main_agent.name}' created")

            # Create runner
            self.runner = Runner(
                agent=self.main_agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            logger.info("✅ Runner created")

            # Test voice service
            voice_status = self.voice_service.get_service_status()
            if voice_status["api_configured"]:
                logger.info("✅ ElevenLabs voice service configured")
            else:
                logger.warning("⚠️ ElevenLabs API key not found - voice features will be limited")

            self.is_initialized = True
            logger.info("🌾 FarmBot service initialized successfully with voice capabilities!")

        except Exception as e:
            logger.error(f"❌ Failed to initialize FarmBot service: {e}")
            raise

    async def process_message_with_voice(
            self,
            message: str,
            session_id: str,
            user_context: Dict[str, Any] = None,
            message_type: str = "text",
            image_data: Optional[str] = None,
            include_voice: bool = True,
            voice_language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Process message and generate both text and voice response

        Returns:
            Dict containing both text response and audio data
        """
        if not self.is_initialized:
            raise RuntimeError("FarmBot service not initialized")

        try:
            logger.info(f"Processing {message_type} message with voice for session {session_id}")

            # Process message through ADK (same as before)
            chat_response = await self.process_message(
                message=message,
                session_id=session_id,
                user_context=user_context,
                message_type=message_type,
                image_data=image_data
            )

            # Determine response type for voice optimization
            response_type = self._determine_response_type(
                chat_response.agent_used,
                chat_response.tools_called
            )

            result = {
                "text_response": chat_response.response,
                "agent_used": chat_response.agent_used,
                "tools_called": chat_response.tools_called,
                "session_id": session_id,
                "timestamp": chat_response.timestamp,
                "response_type": response_type
            }

            # Generate voice if requested and service is available
            if include_voice and self.voice_service.get_service_status()["api_configured"]:
                logger.info(f"Generating voice for {response_type} response")

                voice_result = await self.voice_service.generate_voice_for_farming_response(
                    text=chat_response.response,
                    user_language=voice_language,
                    response_type=response_type
                )

                if voice_result["status"] == "success":
                    result["voice_response"] = {
                        "audio_data": voice_result["audio_data"],
                        "audio_format": voice_result["audio_format"],
                        "voice_id": voice_result["voice_id"],
                        "optimized_text": voice_result.get("optimized_text"),
                        "size_bytes": voice_result["size_bytes"]
                    }
                    logger.info("✅ Voice generated successfully")
                else:
                    logger.warning(f"Voice generation failed: {voice_result.get('message')}")
                    result["voice_error"] = voice_result.get("message")
            else:
                if not include_voice:
                    logger.info("Voice generation skipped (not requested)")
                else:
                    logger.warning("Voice generation skipped (API not configured)")

            return result

        except Exception as e:
            logger.error(f"❌ Error processing message with voice: {e}")
            return {
                "text_response": "मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं। कृपया दोबारा कोशिश करें।",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def process_message(
            self,
            message: str,
            session_id: str,
            user_context: Dict[str, Any] = None,
            message_type: str = "text",
            image_data: Optional[str] = None
    ) -> ChatResponse:
        """
        Original process_message method (unchanged for backward compatibility)
        """
        if not self.is_initialized:
            raise RuntimeError("FarmBot service not initialized")

        try:
            logger.info(f"Processing {message_type} message for session {session_id}: {message[:100]}...")

            # Ensure session exists
            session = await self._ensure_session_exists(session_id, user_context)

            # Prepare message content based on type
            if message_type == "image" and image_data:
                content = await self._prepare_image_content(message, image_data, user_context)
                logger.info("🖼️ Image content prepared for crop health analysis")
            else:
                try:
                    from google.genai import types
                    content = types.Content(role='user', parts=[types.Part(text=message)])
                except ImportError:
                    content = {"role": "user", "content": message}

            # Process through ADK runner
            final_response = "मैं अभी आपकी मदद करने में असमर्थ हूं।"
            agent_used = None
            tools_called = []

            async for event in self.runner.run_async(
                    user_id="web_user",
                    session_id=session_id,
                    new_message=content
            ):
                logger.debug(f"ADK Event: {type(event).__name__}, Author: {event.author}")

                if hasattr(event, 'author') and event.author:
                    agent_used = event.author

                if hasattr(event, 'tool_calls') and event.tool_calls:
                    for tool_call in event.tool_calls:
                        if hasattr(tool_call, 'name'):
                            tools_called.append(tool_call.name)

                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                    elif event.actions and event.actions.escalate:
                        final_response = f"मुझे खेद है: {event.error_message or 'अनुरोध प्रक्रिया में समस्या'}"
                    break

            response = ChatResponse(
                response=final_response,
                session_id=session_id,
                agent_used=agent_used,
                tools_called=list(set(tools_called)),
                timestamp=datetime.now().isoformat()
            )

            logger.info(f"✅ Processed {message_type} message successfully. Agent: {agent_used}")
            return response

        except Exception as e:
            logger.error(f"❌ Error processing {message_type} message: {e}")
            return ChatResponse(
                response="मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं। कृपया दोबारा कोशिश करें।",
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )

    def _determine_response_type(self, agent_used: str, tools_called: list) -> str:
        """Determine response type for voice optimization"""
        if not tools_called:
            return "general"

        tool_names = [tool.lower() for tool in tools_called]

        if any("crop" in tool or "health" in tool or "disease" in tool for tool in tool_names):
            return "crop_health"
        elif any("weather" in tool or "forecast" in tool for tool in tool_names):
            return "weather"
        elif any("market" in tool or "price" in tool for tool in tool_names):
            return "market"
        elif any("scheme" in tool or "government" in tool for tool in tool_names):
            return "schemes"
        else:
            return "general"

    async def generate_voice_only(
            self,
            text: str,
            language: str = "hi",
            voice_type: str = "hindi_male"
    ) -> Dict[str, Any]:
        """Generate voice for any text (utility method)"""
        try:
            return await self.voice_service.text_to_speech(
                text=text,
                voice_type=voice_type,
                language=language
            )
        except Exception as e:
            logger.error(f"Voice generation error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    # Rest of the methods remain the same...
    async def _prepare_image_content(self, message: str, image_data: str, user_context: Dict[str, Any] = None):
        """Prepare image content for AI analysis (unchanged)"""
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            enhanced_message = self._create_enhanced_image_prompt(message, user_context)

            try:
                from google.genai import types
                content = types.Content(
                    role='user',
                    parts=[
                        types.Part(text=enhanced_message),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/jpeg",
                                data=image_bytes
                            )
                        )
                    ]
                )
                return content
            except ImportError:
                logger.warning("Google genai types not available, falling back to text content")
                return {"role": "user", "content": f"{enhanced_message}\n[Image uploaded but cannot be processed]"}

        except Exception as e:
            logger.error(f"Error preparing image content: {e}")
            return {"role": "user", "content": f"फसल की तस्वीर भेजी गई है: {message}"}

    def _create_enhanced_image_prompt(self, message: str, user_context: Dict[str, Any] = None) -> str:
        """Create enhanced prompt for image analysis (unchanged)"""
        user_location = user_context.get('user_location') if user_context else None
        user_preferences = user_context.get('user_preferences', {}) if user_context else {}

        crop_preference = user_preferences.get('primary_crops', [])
        farming_scale = user_preferences.get('farming_scale', 'small')

        enhanced_prompt = f"""
        फसल की तस्वीर का विश्लेषण करने का अनुरोध:

        किसान का संदेश: {message}

        संदर्भ जानकारी:
        - स्थान: {user_location or 'भारत (स्थान अज्ञात)'}
        - मुख्य फसलें: {', '.join(crop_preference) if crop_preference else 'मिश्रित खेती'}
        - खेती का स्तर: {farming_scale}

        कृपया इस फसल की तस्वीर का विस्तृत विश्लेषण करें और:
        1. रोग/कीट की पहचान करें
        2. तत्काल करने योग्य उपाय बताएं  
        3. स्थानीय रूप से उपलब्ध उपचार सुझाएं
        4. लागत-प्रभावी समाधान दें

        विशेष ध्यान दें:
        - व्यावहारिक सुझाव दें जो किसान तुरंत अपना सके
        - स्थानीय बाजार में उपलब्ध दवाओं की जानकारी दें
        - किफायती विकल्प प्राथमिकता दें
        """
        return enhanced_prompt

    async def _ensure_session_exists(self, session_id: str, user_context: Dict[str, Any] = None):
        """Ensure session exists (unchanged)"""
        try:
            session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id="web_user",
                session_id=session_id
            )

            if not session:
                initial_state = {
                    "initialized": True,
                    "user_context": user_context or {},
                    "timestamp": datetime.now().isoformat(),
                    "message_count": 0,
                    "capabilities": {
                        "weather_forecasting": True,
                        "market_analysis": True,
                        "crop_health_diagnosis": True,
                        "government_schemes": True,
                        "image_analysis": True,
                        "voice_synthesis": True  # New capability
                    },
                    "interaction_history": []
                }

                session = await self.session_service.create_session(
                    app_name=self.app_name,
                    user_id="web_user",
                    session_id=session_id,
                    state=initial_state
                )
                logger.info(f"✅ Created new enhanced session with voice: {session_id}")

            return session

        except Exception as e:
            logger.error(f"❌ Session management error: {e}")
            return None

    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status (updated with voice info)"""
        voice_status = self.voice_service.get_service_status()

        return {
            "initialized": self.is_initialized,
            "agent_name": self.main_agent.name if self.main_agent else None,
            "session_service": "running" if self.session_service else "not_available",
            "runner": "running" if self.runner else "not_available",
            "voice_service": voice_status,
            "capabilities": {
                "text_processing": True,
                "image_analysis": True,
                "weather_integration": True,
                "market_analysis": True,
                "crop_health_diagnosis": True,
                "government_schemes": True,
                "multi_language_support": True,
                "voice_synthesis": voice_status["api_configured"],
                "high_quality_voice": voice_status["api_configured"]
            },
            "supported_image_formats": ["JPEG", "PNG", "WebP"],
            "max_image_size": "10MB",
            "supported_languages": ["Hindi", "English", "Marathi", "Gujarati"],
            "voice_features": voice_status.get("features", []),
            "version": "2.1.0-voice-enhanced"
        }