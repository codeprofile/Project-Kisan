# ============================================================================
# WebSocket Connection Manager
# ============================================================================
from typing import List, Dict, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
from  datetime import datetime
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.user_sessions[session_id] = {
            "connected_at": datetime.now(),
            "interaction_count": 0,
            "last_activity": datetime.now(),
            "user_preferences": {},
            "user_location": None
        }


    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]


    async def send_message(self, message: dict, session_id: str):
        try:
            websocket = self.active_connections.get(session_id)
            if websocket:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                self.user_sessions[session_id]["last_activity"] = datetime.now()
        except Exception as e:
            print(f"Error sending enhanced message: {e}")

    async def send_market_analysis(self, data: dict, session_id: str):
        """Send market analysis results"""
        await self.send_message({
            "type": "market_analysis",
            "response": data.get("response", ""),
            "profitable_markets": data.get("profitable_markets"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)

    async def send_transport_calculation(self, data: dict, session_id: str):
        """Send transport calculation results"""
        await self.send_message({
            "type": "transport_calculation",
            "response": data.get("response", ""),
            "transport_analysis": data.get("transport_analysis"),
            "vehicle_type": data.get("vehicle_type"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)

    async def send_price_prediction(self, data: dict, session_id: str):
        """Send price prediction results"""
        await self.send_message({
            "type": "price_prediction",
            "response": data.get("response", ""),
            "predictions": data.get("predictions"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)

    async def send_spoilage_advice(self, data: dict, session_id: str):
        """Send spoilage prevention advice"""
        await self.send_message({
            "type": "spoilage_advice",
            "response": data.get("response", ""),
            "spoilage_advice": data.get("spoilage_advice"),
            "urgency": data.get("urgency", "medium"),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, session_id)

