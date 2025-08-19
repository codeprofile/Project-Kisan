import traceback

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from .google_adk_integration.farmbot_service import FarmBotService
from .websocket_conn import ConnectionManager
from datetime import datetime
import json
from fastapi.responses import HTMLResponse
import uvicorn
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()



app = FastAPI(title="Project Kisan",
              description="AI-Powered Agricultural Assistant.Providing farmers with expert help on demand")



# Mount static files and templates
templates = Jinja2Templates(directory="app/templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
farmbot_agent = FarmBotService()


@app.on_event("startup")
async def startup_event():
    await farmbot_agent.initialize()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """ home page with new features"""
    # Get sample market data


    sample_markets = [
        {"crop_name": "गेहूं", "current_price": 2150, "price_change": 50, "trend": "up",
         "market_location": "नई दिल्ली"},
        {"crop_name": "चावल", "current_price": 3200, "price_change": -30, "trend": "down",
         "market_location": "मुंबई"},
        {"crop_name": "टमाटर", "current_price": 45, "price_change": 8, "trend": "up", "market_location": "पुणे"}
    ]

    context = {
        "request": request,
        "page_title": "प्रोजेक्ट किसान - Enhanced AI Agricultural Assistant",
        "market_preview": sample_markets,
        "enhanced_features_enabled": True,
        "websocket_enabled": True,
        "version": "2.0 Enhanced"
    }
    return templates.TemplateResponse("home.html", context)

conn_manager = ConnectionManager()
async def handle_default_query(content: str, message_type: str, additional_data: dict, session_id: str):
    try:
        # Process through main farmbot agent
        image_data = additional_data.get("image_data") if message_type == "image" else None
        print("farmbot_agent is called")
        result = await farmbot_agent.process_message(content, message_type, image_data)
        print("result", result)
        # For analysis results, send structured data
        if message_type == "image":
            analysis_data = {
                "type": "analysis_result",
                "diagnosis": "बैक्टीरियल ब्लाइट",  # Would come from actual analysis
                "confidence": 94.5,
                "symptoms": "पत्तियों पर भूरे धब्बे, पौधे का मुरझाना",
                "treatment": "स्ट्रेप्टोमाइसिन का छिड़काव करें",
                "preventive_measures": [
                    "खेत में जल निकासी सुधारें",
                    "संक्रमित पत्तियों को हटाएं"
                ],
                "session_id": session_id
            }
            await conn_manager.send_message(analysis_data, session_id)
        else:
            # Regular text response
            await conn_manager.send_message({
                "type": "response",
                "content": result.response,
                "session_id": session_id
            }, session_id)

    except Exception as e:
        print(f"Query error: {e}")


@app.websocket("/ws/chat")
async def enhanced_websocket_chat_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with advanced market features"""
    session_id = f"session_{int(datetime.now().timestamp())}"
    print(session_id)
    await conn_manager.connect(websocket, session_id)
    print("Connected")
    try:
        while True:
            print("here we are ")
            # Receive message from frontend
            data = await websocket.receive_text()
            print("received data", data)
            message_data = json.loads(data)

            message_type = message_data.get("type", "text")
            content = message_data.get("content", "")
            user_location = message_data.get("user_location")
            user_preferences = message_data.get("user_preferences", {})
            additional_data = message_data.get("additional_data", {})

            # Update user session
            if user_location:
                conn_manager.user_sessions[session_id]["user_location"] = user_location
            if user_preferences:
                conn_manager.user_sessions[session_id]["user_preferences"] = user_preferences

            conn_manager.user_sessions[session_id]["interaction_count"] += 1


            await handle_default_query(content, message_type, additional_data, session_id)

    except WebSocketDisconnect:
        conn_manager.disconnect(session_id)
    except Exception as e:
        print(f"Enhanced WebSocket error: {e}")
        conn_manager.disconnect(session_id)
        traceback.print_exc()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=20
    )