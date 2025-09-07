# app/main.py - Updated with ElevenLabs Voice Integration
from operator import and_

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc

from .google_adk_integration.farmbot_service import FarmBotService
from .google_adk_integration.services.mandi_db_generation import CoreMarketDataSyncService
from .websocket_conn import ConnectionManager
from datetime import datetime, timedelta
import json
from fastapi.responses import HTMLResponse
from .google_adk_integration.mandi_db.database import get_db_session,create_tables
from .google_adk_integration.mandi_db.models import MarketPrice
import uvicorn
import os
import base64

app = FastAPI(title="Project Kisan",
              description="AI-Powered Agricultural Assistant with Voice & Real Crop Health Diagnosis")

# Mount static files and templates
templates = Jinja2Templates(directory="app/templates")

# Initialize services
farmbot_agent = FarmBotService()


@app.on_event("startup")
async def startup_event():
    """Initialize all services on startup"""
    try:
        await farmbot_agent.initialize()
        print("✅ FarmBot service initialized successfully")

        # Set API keys (replace with your actual keys)
        os.environ["GOOGLE_API_KEY"] = "PASTE-YOUR-API-KEY-HERE"
        os.environ["MANDI_API_KEY"] = "PASTE-YOUR-API-KEY-HERE"  # data-gov-in
        os.environ["WEATHER_API_KEY"] = "PASTE-YOUR-API-KEY-HERE"
        os.environ["ELEVENLABS_API_KEY"] = "PASTE-YOUR-API-KEY-HERE"

        print("🎙️ ElevenLabs voice service configured")
        # Optional: Initialize market data service
        # mandi_db_service = CoreMarketDataSyncService()
        # create_tables()
        # await mandi_db_service.sync_market_data()

    except Exception as e:
        print(f"❌ Startup error: {e}")


async def get_market_preview_data():
    """Get real market data for homepage preview (unchanged)"""
    try:
        with get_db_session() as db:
            popular_commodities = ['Onion', 'Tomato', 'Potato', 'Rice', 'Wheat']
            market_preview = []

            for commodity in popular_commodities:
                latest_prices = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity.ilike(f"%{commodity}%"),
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=3)
                    )
                ).order_by(desc(MarketPrice.arrival_date)).limit(5).all()

                if latest_prices:
                    avg_price = sum(p.modal_price for p in latest_prices) / len(latest_prices)
                    price_change = 0
                    trend = "stable"
                    if latest_prices[0].price_change:
                        price_change = latest_prices[0].price_change
                    if latest_prices[0].trend:
                        trend = latest_prices[0].trend

                    best_market = max(latest_prices, key=lambda x: x.modal_price)
                    market_location = f"{best_market.market}, {best_market.district}"

                    hindi_names = {
                        'Onion': 'प्याज',
                        'Tomato': 'टमाटर',
                        'Potato': 'आलू',
                        'Rice': 'चावल',
                        'Wheat': 'गेहूं'
                    }

                    market_preview.append({
                        "crop_name": hindi_names.get(commodity, commodity),
                        "current_price": round(avg_price, 0),
                        "price_change": round(price_change, 0),
                        "trend": trend,
                        "market_location": market_location[:30] + "..." if len(
                            market_location) > 30 else market_location,
                        "data_date": latest_prices[0].arrival_date.strftime("%d-%m-%Y")
                    })

                if len(market_preview) >= 3:
                    break

            return market_preview

    except Exception as e:
        print(f"Error getting market preview: {e}")
        return []


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with real AI features and voice"""
    try:
        market_data = await get_market_preview_data()
        print(f"Market preview data: {len(market_data) if market_data else 0} items")

        context = {
            "request": request,
            "page_title": "प्रोजेक्ट किसान - AI Agricultural Assistant with Voice",
            "market_preview": market_data,
            "enhanced_features_enabled": True,
            "websocket_enabled": True,
            "ai_crop_diagnosis": True,
            "voice_enabled": True,
            "version": "2.1 with ElevenLabs Voice"
        }
        return templates.TemplateResponse("home.html", context)

    except Exception as e:
        print(f"Home page error: {e}")
        context = {
            "request": request,
            "page_title": "प्रोजेक्ट किसान - AI Agricultural Assistant",
            "market_preview": [],
            "enhanced_features_enabled": True,
            "websocket_enabled": True,
            "ai_crop_diagnosis": True,
            "voice_enabled": True,
            "version": "2.1"
        }
        return templates.TemplateResponse("home.html", context)


conn_manager = ConnectionManager()


async def handle_default_query_with_voice(content: str, message_type: str, additional_data: dict, session_id: str):
    """Enhanced query handler with voice response"""
    try:
        print(f"Processing {message_type} query with voice: {content[:100]}...")

        # Get user context from session
        user_context = conn_manager.user_sessions.get(session_id, {})
        user_location = user_context.get("user_location")
        user_preferences = user_context.get("user_preferences", {})

        # Enhanced context for AI
        enhanced_context = {
            "user_location": user_location,
            "user_preferences": user_preferences,
            "session_data": user_context
        }

        # Process through main farmbot agent with voice
        if message_type == "image":
            image_data = additional_data.get("image_data")
            if not image_data:
                await conn_manager.send_message({
                    "type": "error",
                    "content": "तस्वीर प्राप्त नहीं हुई। कृपया दोबारा कोशिश करें।",
                    "session_id": session_id
                }, session_id)
                return

            # Process image with voice
            result = await farmbot_agent.process_message_with_voice(
                message=content,
                session_id=session_id,
                user_context=enhanced_context,
                message_type="image",
                image_data=image_data,
                include_voice=True,
                voice_language="hi"
            )

            # Send response with voice
            response_message = {
                "type": "response",
                "content": result["text_response"].replace("*", ""),
                "agent_used": result.get("agent_used"),
                "tools_called": result.get("tools_called"),
                "response_type": result.get("response_type", "crop_health"),
                "session_id": session_id,
                "timestamp": result["timestamp"]
            }

            # Add voice data if available
            if "voice_response" in result:
                response_message["voice_data"] = result["voice_response"]
                print("✅ Voice data included in response")
            elif "voice_error" in result:
                print(f"⚠️ Voice generation failed: {result['voice_error']}")

            await conn_manager.send_message(response_message, session_id)

        else:
            # Handle text queries with voice
            await conn_manager.send_message({
                "type": "thinking",
                "content": "विश्लेषण हो रहा है...",
                "session_id": session_id
            }, session_id)

            # Process text with voice
            result = await farmbot_agent.process_message_with_voice(
                message=content,
                session_id=session_id,
                user_context=enhanced_context,
                message_type="text",
                include_voice=True,
                voice_language=user_preferences.get("language", "hi")
            )

            # Send text response with voice
            response_message = {
                "type": "response",
                "content": result["text_response"].replace("*", ""),
                "agent_used": result.get("agent_used"),
                "tools_called": result.get("tools_called"),
                "response_type": result.get("response_type", "general"),
                "session_id": session_id,
                "timestamp": result["timestamp"]
            }

            # Add voice data if available
            if "voice_response" in result:
                response_message["voice_data"] = result["voice_response"]
                print("✅ Voice data included in text response")

            await conn_manager.send_message(response_message, session_id)

        # Update session statistics
        if session_id in conn_manager.user_sessions:
            if message_type == "image":
                conn_manager.user_sessions[session_id]["image_analyses"] = \
                    conn_manager.user_sessions[session_id].get("image_analyses", 0) + 1
            else:
                conn_manager.user_sessions[session_id]["text_queries"] = \
                    conn_manager.user_sessions[session_id].get("text_queries", 0) + 1

        print(f"Successfully processed {message_type} query with voice")

    except Exception as e:
        print(f"Query processing error: {e}")
        await conn_manager.send_message({
            "type": "error",
            "content": f"माफ करें, एक त्रुटि हुई है: {str(e)}। कृपया दोबारा कोशिश करें।",
            "session_id": session_id
        }, session_id)


@app.websocket("/ws/chat")
async def enhanced_websocket_chat_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with voice capabilities"""
    session_id = f"session_{int(datetime.now().timestamp())}"

    try:
        await conn_manager.connect(websocket, session_id)
        print(f"✅ WebSocket connected with voice: {session_id}")

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message_type = message_data.get("type", "text")
            content = message_data.get("content", "")
            user_location = message_data.get("user_location")
            user_preferences = message_data.get("user_preferences", {})
            additional_data = message_data.get("additional_data", {})

            # Update user session context
            if user_location:
                conn_manager.user_sessions[session_id]["user_location"] = user_location
                print(f"Updated location for {session_id}: {user_location}")

            if user_preferences:
                conn_manager.user_sessions[session_id]["user_preferences"] = user_preferences
                print(f"Updated preferences for {session_id}: {user_preferences}")

            conn_manager.user_sessions[session_id]["interaction_count"] += 1
            conn_manager.user_sessions[session_id]["last_activity"] = datetime.now().isoformat()

            # Process the query with voice
            await handle_default_query_with_voice(content, message_type, additional_data, session_id)

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {session_id}")
        conn_manager.disconnect(session_id)

    except Exception as e:
        print(f"❌ WebSocket error for {session_id}: {e}")
        conn_manager.disconnect(session_id)


@app.get("/api/service-status")
async def get_service_status():
    """Get status of all services including voice"""
    try:
        farmbot_status = farmbot_agent.get_service_status()

        return {
            "status": "operational",
            "services": {
                "farmbot_ai": farmbot_status,
                "websocket": "running",
                "market_data": "available" if await get_market_preview_data() else "limited",
                "voice_synthesis": "available" if farmbot_status.get("voice_service", {}).get(
                    "api_configured") else "not_configured"
            },
            "features": {
                "crop_diagnosis": farmbot_status.get("capabilities", {}).get("crop_health_diagnosis", False),
                "weather_forecasting": farmbot_status.get("capabilities", {}).get("weather_integration", False),
                "market_analysis": farmbot_status.get("capabilities", {}).get("market_analysis", False),
                "image_analysis": farmbot_status.get("capabilities", {}).get("image_analysis", False),
                "voice_synthesis": farmbot_status.get("capabilities", {}).get("voice_synthesis", False),
                "high_quality_voice": farmbot_status.get("capabilities", {}).get("high_quality_voice", False)
            },
            "ai_models": {
                "gemini_vision": "available" if os.getenv("GOOGLE_API_KEY") else "not_configured",
                "weather_api": "available" if os.getenv("WEATHER_API_KEY") else "not_configured",
                "elevenlabs_voice": "available" if os.getenv("ELEVENLABS_API_KEY") else "not_configured"
            },
            "voice_info": farmbot_status.get("voice_service", {}),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/generate-voice")
async def generate_voice_endpoint(
        text: str = Form(...),
        language: str = Form(default="hi"),
        voice_type: str = Form(default="hindi_male")
):
    """Direct voice generation endpoint for testing"""
    try:
        result = await farmbot_agent.generate_voice_only(
            text=text,
            language=language,
            voice_type=voice_type
        )

        if result["status"] == "success":
            return {
                "status": "success",
                "audio_data": result["audio_data"],
                "audio_format": result["audio_format"],
                "voice_id": result["voice_id"],
                "size_bytes": result["size_bytes"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {str(e)}")


@app.get("/api/session/{session_id}/analytics")
async def get_session_analytics(session_id: str):
    """Get analytics for a specific session"""
    try:
        analytics = await farmbot_agent.get_service_analytics(session_id)
        return analytics

    except Exception as e:
        return {
            "error": f"Analytics not available: {str(e)}",
            "session_id": session_id
        }


@app.post("/api/image-upload")
async def upload_image_endpoint(file: UploadFile = File(...)):
    """Direct image upload endpoint for testing"""
    try:
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')

        temp_session = f"temp_{int(datetime.now().timestamp())}"

        analysis = await farmbot_agent.analyze_crop_image(
            image_path=None,
            user_context={"upload_method": "direct_api"}
        )

        return {
            "status": "success",
            "filename": file.filename,
            "analysis": analysis,
            "session_id": temp_session
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=20
    )