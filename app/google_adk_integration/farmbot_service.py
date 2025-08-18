# app/google_adk_integration/farmbot_service.py
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


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
            logger.info("Initializing FarmBot ADK service...")

            # Create session service
            self.session_service = InMemorySessionService()
            logger.info("✅ Session service created")

            # Create main agent
            self.main_agent = create_main_farmbot_agent()
            logger.info(f"✅ Main agent '{self.main_agent.name}' created")

            # Create runner
            self.runner = Runner(
                agent=self.main_agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            logger.info("✅ Runner created")

            self.is_initialized = True
            logger.info("🌾 FarmBot ADK service initialized successfully!")

        except Exception as e:
            logger.error(f"❌ Failed to initialize FarmBot ADK service: {e}")
            raise

    async def process_message(
            self,
            message: str,
            session_id: str,
            user_context: Dict[str, Any] = None,
            message_type: str = "text"
    ) -> ChatResponse:
        """
        Process a user message through the ADK agent system

        Args:
            message: User's input message
            session_id: Session identifier
            user_context: Additional user context
            message_type: Type of message (text, voice, image)

        Returns:
            ChatResponse with agent's reply
        """
        print("There is the called !!!")
        if not self.is_initialized:
            raise RuntimeError("FarmBot service not initialized")

        try:
            logger.info(f"Processing message for session {session_id}: {message[:100]}...")

            # Ensure session exists
            session = await self._ensure_session_exists(session_id, user_context)
            print("here")
            # Prepare message content
            content = types.Content(role='user', parts=[types.Part(text=message)])
            print("there")
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
                tools_called=[],#list(set(tools_called)),  # Remove duplicates
                timestamp=datetime.now().isoformat()
            )
            print(f"response received is : {response} and {type(response)}")
            logger.info(f"✅ Processed message successfully. Agent: {agent_used}, Tools: {tools_called}")
            return response

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return ChatResponse(
                response="मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं। कृपया दोबारा कोशिश करें।",
                session_id=session_id,
                timestamp=datetime.now().isoformat()
            )

    async def analyze_crop_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze crop image for disease detection

        Args:
            image_path: Path to the uploaded image

        Returns:
            Disease analysis results
        """
        try:
            logger.info(f"Analyzing crop image: {image_path}")

            # In production, this would use Gemini Vision or custom ML models
            # For now, return enhanced mock analysis

            analysis = {
                "disease_name": "बैक्टीरियल ब्लाइट",
                "confidence": 94.5,
                "description": "पत्तियों पर दिखने वाले धब्बों से बैक्टीरियल ब्लाइट का संकेत मिल रहा है।",
                "treatment": "स्ट्रेप्टोमाइसिन 90% + टेट्रासाइक्लिन 10% का छिड़काव करें",
                "severity": "मध्यम",
                "preventive_measures": [
                    "खेत में जल निकासी की व्यवस्था सुधारें",
                    "संक्रमित पत्तियों को हटा दें",
                    "कॉपर सल्फेट का नियमित छिड़काव करें"
                ],
                "immediate_actions": [
                    "प्रभावित पत्तियों को तुरंत हटाएं",
                    "24 घंटे के अंदर फंगीसाइड का छिड़काव करें"
                ],
                "follow_up": "7 दिन बाद दोबारा जांच करें"
            }

            logger.info("✅ Image analysis completed")
            return analysis

        except Exception as e:
            logger.error(f"❌ Image analysis error: {e}")
            return {
                "disease_name": "पहचान में समस्या",
                "confidence": 0.0,
                "description": "छवि का विश्लेषण नहीं हो सका",
                "treatment": "कृपया स्थानीय कृषि विशेषज्ञ से संपर्क करें",
                "severity": "अज्ञात",
                "preventive_measures": ["बेहतर गुणवत्ता की तस्वीर लें"]
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
                # Create new session
                initial_state = {
                    "initialized": True,
                    "user_context": user_context or {},
                    "timestamp": datetime.now().isoformat(),
                    "message_count": 0
                }

                session = await self.session_service.create_session(
                    app_name=self.app_name,
                    user_id="web_user",
                    session_id=session_id,
                    state=initial_state
                )
                logger.info(f"✅ Created new session: {session_id}")

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

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "initialized": self.is_initialized,
            "agent_name": self.main_agent.name if self.main_agent else None,
            "session_service": "running" if self.session_service else "not_available",
            "runner": "running" if self.runner else "not_available"
        }