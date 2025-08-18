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
from .google_adk_integration.mandi_db.database import get_db_session
from .google_adk_integration.mandi_db.models import MarketPrice
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
    # mandi_db_service = CoreMarketDataSyncService()
    # create_tables()
    # await mandi_db_service.sync_market_data()


async def get_market_preview_data():
    """Get real market data for homepage preview"""
    try:
        with get_db_session() as db:
            # Get latest prices for popular commodities
            popular_commodities = ['Onion', 'Tomato', 'Potato', 'Rice', 'Wheat']
            market_preview = []

            for commodity in popular_commodities:
                # Get latest price data for this commodity
                latest_prices = db.query(MarketPrice).filter(
                    and_(
                        MarketPrice.commodity.ilike(f"%{commodity}%"),
                        MarketPrice.arrival_date >= datetime.now() - timedelta(days=3)
                    )
                ).order_by(desc(MarketPrice.arrival_date)).limit(5).all()

                if latest_prices:
                    # Calculate average price and trend
                    avg_price = sum(p.modal_price for p in latest_prices) / len(latest_prices)

                    # Get price change from trend data
                    price_change = 0
                    trend = "stable"
                    if latest_prices[0].price_change:
                        price_change = latest_prices[0].price_change
                    if latest_prices[0].trend:
                        trend = latest_prices[0].trend

                    # Get best market location
                    best_market = max(latest_prices, key=lambda x: x.modal_price)
                    market_location = f"{best_market.market}, {best_market.district}"

                    # Map commodity names to Hindi
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

                # Stop after getting 3 commodities for preview
                if len(market_preview) >= 3:
                    break

            return market_preview

    except Exception as e:
        print(f"Error getting market preview: {e}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """ home page with new features"""
    # Get sample market data
    print(await get_market_preview_data())
    context = {
        "request": request,
        "page_title": "प्रोजेक्ट किसान - Enhanced AI Agricultural Assistant",
        "market_preview": await get_market_preview_data(),
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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=20
    )