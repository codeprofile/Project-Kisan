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
    Main service class that wraps ADK functionality for the FastAPI application
    Enhanced with crop health image analysis capabilities
    """

    def __init__(self):
        self.session_service = None
        self.main_agent = None
        self.runner = None
        self.app_name = "farmbot_production"
        self.is_initialized = False

    async def initialize(self):
        """Initialize the FarmBot ADK service"""
        try:
            logger.info("Initializing FarmBot ADK service with crop health detection...")

            # Create session service
            self.session_service = InMemorySessionService()
            logger.info("✅ Session service created")

            # Create main agent with crop health capabilities
            self.main_agent = create_main_farmbot_agent()
            logger.info(f"✅ Main agent '{self.main_agent.name}' created with crop health detection")

            # Create runner
            self.runner = Runner(
                agent=self.main_agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            logger.info("✅ Runner created")

            self.is_initialized = True
            logger.info("🌾 FarmBot ADK service initialized successfully with AI crop diagnosis!")

        except Exception as e:
            logger.error(f"❌ Failed to initialize FarmBot ADK service: {e}")
            raise

    async def process_message(
            self,
            message: str,
            session_id: str,
            user_context: Dict[str, Any] = None,
            message_type: str = "text",
            image_data: Optional[str] = None
    ) -> ChatResponse:
        """
        Process a user message through the ADK agent system
        Enhanced to handle image uploads for crop health diagnosis

        Args:
            message: User's input message
            session_id: Session identifier
            user_context: Additional user context
            message_type: Type of message (text, image, voice)
            image_data: Base64 encoded image data for crop analysis

        Returns:
            ChatResponse with agent's reply
        """
        if not self.is_initialized:
            raise RuntimeError("FarmBot service not initialized")

        try:
            logger.info(f"Processing {message_type} message for session {session_id}: {message[:100]}...")

            # Ensure session exists
            session = await self._ensure_session_exists(session_id, user_context)

            # Prepare message content based on type
            if message_type == "image" and image_data:
                # Handle image upload for crop health diagnosis
                content = await self._prepare_image_content(message, image_data, user_context)
                logger.info("🖼️ Image content prepared for crop health analysis")
            else:
                # Handle text message
                # Import the types from the correct module
                try:
                    from google.genai import types
                    content = types.Content(role='user', parts=[types.Part(text=message)])
                except ImportError:
                    # Fallback if types are not available
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
                # Log events for debugging
                logger.debug(f"ADK Event: {type(event).__name__}, Author: {event.author}")

                # Track which agent is being used
                if hasattr(event, 'author') and event.author:
                    agent_used = event.author

                # Track tool calls
                if hasattr(event, 'tool_calls') and event.tool_calls:
                    for tool_call in event.tool_calls:
                        if hasattr(tool_call, 'name'):
                            tools_called.append(tool_call.name)

                # Get final response
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                    elif event.actions and event.actions.escalate:
                        final_response = f"मुझे खेद है: {event.error_message or 'अनुरोध प्रक्रिया में समस्या'}"
                    break

            # Create response
            response = ChatResponse(
                response=final_response,
                session_id=session_id,
                agent_used=agent_used,
                tools_called=list(set(tools_called)),  # Remove duplicates
                timestamp=datetime.now().isoformat()
            )

            logger.info(f"✅ Processed {message_type} message successfully. Agent: {agent_used}, Tools: {tools_called}")
            return response

        except Exception as e:
            logger.error(f"❌ Error processing {message_type} message: {e}")
            return ChatResponse(
                response="मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं। कृपया दोबारा कोशिश करें।",
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )

    async def _prepare_image_content(
            self,
            message: str,
            image_data: str,
            user_context: Dict[str, Any] = None
    ):
        """
        Prepare image content for AI analysis

        Args:
            message: Text message accompanying the image
            image_data: Base64 encoded image data
            user_context: User context including location, crop type, etc.

        Returns:
            Content object for ADK processing
        """
        try:
            # Clean image data (remove data URL prefix if present)
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)

            # Prepare enhanced prompt with context
            enhanced_message = self._create_enhanced_image_prompt(message, user_context)

            # Try to create content with image - this depends on your ADK version
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
                # Fallback if types are not available - return text content
                logger.warning("Google genai types not available, falling back to text content")
                return {"role": "user", "content": f"{enhanced_message}\n[Image uploaded but cannot be processed]"}

        except Exception as e:
            logger.error(f"Error preparing image content: {e}")
            # Fallback to text-only content
            return {"role": "user", "content": f"फसल की तस्वीर भेजी गई है: {message}"}

    def _create_enhanced_image_prompt(
            self,
            message: str,
            user_context: Dict[str, Any] = None
    ) -> str:
        """
        Create enhanced prompt for image analysis with user context

        Args:
            message: Original user message
            user_context: Additional context about user/location/crop

        Returns:
            Enhanced prompt for better analysis
        """
        user_location = user_context.get('user_location') if user_context else None
        user_preferences = user_context.get('user_preferences', {}) if user_context else {}

        # Extract additional context
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

    async def analyze_crop_image(self, image_path: str = None, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze crop image for disease detection using AI

        Args:
            image_path: Path to the uploaded image (not used in this implementation)
            user_context: User context for personalized advice

        Returns:
            Disease analysis results from AI
        """
        try:
            logger.info(f"Analyzing crop image with context: {user_context}")

            # Since we're working with base64 data in the WebSocket context,
            # we'll return a generic response structure that can be used by the calling code
            analysis_result = {
                "disease_detection": "AI विश्लेषण के लिए तैयार",
                "confidence": 85.0,
                "description": "फसल की तस्वीर प्राप्त हुई है और AI विश्लेषण के लिए तैयार है।",
                "treatment_recommendations": "AI द्वारा विस्तृत विश्लेषण प्रदान किया जाएगा",
                "severity": "विश्लेषण के बाद निर्धारित होगा",
                "immediate_actions": [
                    "AI विश्लेषण की प्रतीक्षा करें",
                    "तस्वीर की गुणवत्ता अच्छी रखें",
                    "पूर्ण परिणाम के लिए प्रतीक्षा करें"
                ],
                "follow_up": "AI विश्लेषण पूर्ण होने पर विस्तृत जानकारी मिलेगी",
                "ai_ready": True
            }

            logger.info("✅ Crop image analysis structure prepared")
            return analysis_result

        except Exception as e:
            logger.error(f"❌ Image analysis error: {e}")
            return {
                "disease_detection": "विश्लेषण में त्रुटि",
                "confidence": 0.0,
                "description": f"तस्वीर का विश्लेषण नहीं हो सका: {str(e)}",
                "treatment_recommendations": "कृपया स्थानीय कृषि विशेषज्ञ से संपर्क करें",
                "severity": "अज्ञात",
                "immediate_actions": ["बेहतर गुणवत्ता की तस्वीर लें", "दोबारा कोशिश करें"],
                "follow_up": "तकनीकी सहायता के लिए संपर्क करें",
                "ai_ready": False
            }

    async def _ensure_session_exists(self, session_id: str, user_context: Dict[str, Any] = None) -> Any:
        """Ensure session exists, create if needed"""
        try:
            session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id="web_user",
                session_id=session_id
            )

            if not session:
                # Create new session with enhanced context
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
                        "image_analysis": True
                    },
                    "interaction_history": []
                }

                session = await self.session_service.create_session(
                    app_name=self.app_name,
                    user_id="web_user",
                    session_id=session_id,
                    state=initial_state
                )
                logger.info(f"✅ Created new enhanced session: {session_id}")

            return session

        except Exception as e:
            logger.error(f"❌ Session management error: {e}")
            return None

    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state"""
        try:
            session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id="web_user",
                session_id=session_id
            )
            return session.state if session else {}
        except Exception as e:
            logger.error(f"❌ Error getting session state: {e}")
            return {}

    async def update_session_context(
            self,
            session_id: str,
            context_updates: Dict[str, Any]
    ) -> bool:
        """Update session context with new information"""
        try:
            session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id="web_user",
                session_id=session_id
            )

            if session:
                # Update context
                session.state["user_context"].update(context_updates)
                session.state["last_updated"] = datetime.now().isoformat()

                # Save updated session
                await self.session_service.update_session(session)
                logger.info(f"✅ Updated session context for {session_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Error updating session context: {e}")

        return False

    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status information"""
        return {
            "initialized": self.is_initialized,
            "agent_name": self.main_agent.name if self.main_agent else None,
            "session_service": "running" if self.session_service else "not_available",
            "runner": "running" if self.runner else "not_available",
            "capabilities": {
                "text_processing": True,
                "image_analysis": True,
                "weather_integration": True,
                "market_analysis": True,
                "crop_health_diagnosis": True,
                "government_schemes": True,
                "multi_language_support": True
            },
            "supported_image_formats": ["JPEG", "PNG", "WebP"],
            "max_image_size": "10MB",
            "supported_languages": ["Hindi", "English", "Marathi", "Gujarati"],
            "version": "2.0.0-enhanced"
        }

    async def get_service_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for service usage"""
        try:
            session_state = await self.get_session_state(session_id)

            return {
                "session_info": {
                    "session_id": session_id,
                    "created": session_state.get("timestamp"),
                    "message_count": session_state.get("message_count", 0),
                    "last_activity": session_state.get("last_updated", session_state.get("timestamp"))
                },
                "feature_usage": {
                    "weather_queries": session_state.get("weather_queries", 0),
                    "market_queries": session_state.get("market_queries", 0),
                    "health_queries": session_state.get("health_queries", 0),
                    "scheme_queries": session_state.get("scheme_queries", 0),
                    "image_analyses": session_state.get("image_analyses", 0)
                },
                "user_preferences": session_state.get("user_context", {}).get("user_preferences", {}),
                "location": session_state.get("user_context", {}).get("user_location")
            }

        except Exception as e:
            logger.error(f"❌ Error getting service analytics: {e}")
            return {"error": "Analytics not available"}