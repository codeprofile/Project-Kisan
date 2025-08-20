# Project Kisan 🌾 - Providing farmers with expert help on demand

<div align="center">

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Try_Now-brightgreen?style=for-the-badge)](https://app-975609603775.us-central1.run.app/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Modern-green?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Google AI](https://img.shields.io/badge/Google_AI-Gemini-orange?style=for-the-badge&logo=google)](https://ai.google.dev)

</div>

Project Kisan is a voice-first, multilingual AI assistant for small-scale farmers. Powered by Google AI technologies and the Gemini model, it delivers crop disease diagnosis, real-time market insights, and government scheme guidance via natural voice in local languages, working even in low-network regions.

---

## 🎯 **Major Challenges Faced by Indian Farmers**

<div align="center">
<img width="560" height="314" alt="Challenges faced by Indian Farmers" src="https://github.com/user-attachments/assets/fd2c8e2a-db7c-41b8-a9ba-a6374cca3932" />
</div>

Indian farmers face multiple interconnected challenges that affect their productivity and income:
- **Limited access to expert agricultural advice**
- **Language barriers with technology solutions** 
- **Lack of real-time market and Weather information**
- **Difficulty in identifying crop diseases early**
- **Complex government scheme navigation**
- **Poor internet connectivity in rural areas**

---

## 💡 **Our Solution**

<div align="center">
<img width="556" height="316" alt="Project Kisan Solution" src="https://github.com/user-attachments/assets/ec892371-2ce8-4d82-a710-3808f5f001bb" />
</div>

Project Kisan addresses these challenges through:
- **AI-powered agricultural expertise** available 24/7
- **Voice-first interface** in multiple Indian languages
- **Real-time data integration** from government sources
- **Offline capabilities** for low-connectivity areas
- **Simplified access** to government schemes,weather and market data

---

## 🚀 **Live Application**

<div align="center">

### **[🌐 Try Project Kisan Now →](https://app-975609603775.us-central1.run.app/)**

*No installation required - works on any device with a browser*

</div>

### **📱 Application Preview**

https://github.com/user-attachments/assets/ad9f74b4-8086-4e68-955a-751b1118bd0b





---

## ✨ **Key Features**

<div align="center">

| Feature | Description | Technology |
|---------|-------------|------------|
| 🌱 **Crop Disease Diagnosis** | Vision AI–powered photo-based detection with localized remedies | Google Gemini Vision |
| 🌤️ **Real-Time Weather Information** | Real-Time and Weather Forecasting for 7 days | OpenWeatherMap API |
| 📈 **Real-Time Market Intelligence** | Live mandi prices & crop trends from government sources | AgMarkNet API |
| 🏛️ **Government Scheme Navigator** | Eligibility checks & simplified explanations | Data.gov.in APIs |
| 🗣️ **Voice-First & Multilingual** | Supports multiple languages as enabled by Google ADK | Speech Recognition |
| 📶 **Offline Support** | Cached responses via Gemini model for low-network zones | PWA + Service Workers |

</div>

### **🎬 Feature Showcase**

#### 🌱 **Crop Disease Diagnosis**
```
👨‍🌾 Farmer: *uploads photo of diseased crop*
🤖 AI: "मैं आपकी फसल की तस्वीर का विश्लेषण कर रहा हूं..."
🔬 AI: "टमाटर में 'अंगमारी रोग' (Late Blight) की पहचान हुई है"
💊 AI: "तुरंत Mancozeb 75% WP @ 2 ग्राम/लीटर का छिड़काव करें"
💰 AI: "अनुमानित लागत: ₹300-400 प्रति एकड़"
```

#### 🗣️ **Voice Interaction**
```
🎤 Farmer: "आज मौसम कैसा रहेगा?"
🌤️ AI: "आज का मौसम: 28°C, हल्की बादलों के साथ"
💧 AI: "70% बारिश की संभावना - सिंचाई की आवश्यकता नहीं"
🌾 AI: "फसल छिड़काव के लिए अच्छा दिन नहीं है"
```

#### 📊 **Market Intelligence**
```
💬 Farmer: "प्याज की कीमत क्या चल रही है?"
📈 AI: "आज प्याज का भाव: ₹2,500/क्विंटल (औसत)"
🏆 AI: "सबसे अच्छी मंडी: आज़ादपुर मार्केट - ₹2,800/क्विंटल"
📊 AI: "पिछले सप्ताह से 8% वृद्धि - बेचने का अच्छा समय!"
```

---

## 🏗️ **Tech Stack**

<div align="center">

| Layer | Technology | Purpose |
|-------|------------|---------|
| **🎨 Frontend** | Progressive Web App (PWA) | Mobile-first, offline-capable interface |
| **⚡ Backend** | FastAPI, Google Cloud Run, Cloud Storage | High-performance API with cloud scaling |
| **🧠 AI & ML** | Google ADK, Gemini, Vision AI | Intelligent conversations and image analysis |
| **🔗 Integrations** | AgMarkNet, eNAM, Weather APIs, Data.gov | Real-time agricultural data |

</div>

---

## 🔑 **API Configuration**

| Service | Environment Variable | Required | Get API Key | Purpose |
|---------|---------------------|----------|-------------|---------|
| 🤖 **Google AI** | `GOOGLE_API_KEY` | ✅ **Required** | [Get Key →](https://ai.google.dev/) | AI conversations & vision |
| 🌤️ **Weather API** | `WEATHER_API_KEY` | ✅ **Required** | [Get Key →](https://openweathermap.org/api) | Weather forecasting |
| 📊 **Data.gov.in** | `MANDI_API_KEY` | ⚠️ *Optional* | [Get Key →](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi) | Government market data |

### **Environment Setup**
```bash
# Create .env file
GOOGLE_API_KEY=your_google_ai_api_key_here
WEATHER_API_KEY=your_openweathermap_api_key
MANDI_API_KEY=your_data_gov_api_key  # Optional
```

---

## 🛠️ **Getting Started**

### **⚡ Quick Start**
```bash
# Clone the repository
git clone https://github.com/codeprofile/Project-Kisan.git
cd Project-Kisan

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (add your API keys)
cp .env.example .env

# Run locally
uvicorn app.main:app --reload
```



---

## 📁 **Project Structure**

```
Project-Kisan/
├── app/
│   ├── google_adk_integration/
│   │   ├── agents/              # AI agents for different domains
│   │   ├── tools/               # AI tool functions
│   │   ├── services/            # Business logic
│   │   └── farmbot_service.py   # Main AI service
│   ├── templates/
│   │   └── home.html           # Frontend interface
│   ├── main.py                 # FastAPI application
│   └── websocket_conn.py       # WebSocket connections
├── requirements.txt
└── README.md
```

---

## 🌐 **Useful Resources**

### **📚 Documentation**
- [Google ADK](https://google.github.io/adk-docs/streaming/custom-streaming-ws/#websocket-handling) - Agent Development Kit
Custom Audio Bidi-streaming app sample
  

### **🌾 Agricultural Data Sources**
- [AgMarkNet Portal](https://agmarknet.gov.in/) - Government market prices
- [eNAM Platform](https://enam.gov.in/) - National agriculture market
- [Data.gov.in](https://data.gov.in/) - Open government data
- [Weather API](https://openweathermap.org/) - Weather forecasting service

### **🛠️ Development Resources**
- [Google Cloud Run](https://cloud.google.com/run) - Deployment platform
- [WebSocket Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket) - Real-time communication
- [Speech Recognition API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) - Voice interface

---

<div align="center">

## 🌾 **Built with ❤️ for Indian Farmers**

[![GitHub stars](https://img.shields.io/github/stars/codeprofile/Project-Kisan?style=social)](https://github.com/codeprofile/Project-Kisan)
[![GitHub forks](https://img.shields.io/github/forks/codeprofile/Project-Kisan?style=social)](https://github.com/codeprofile/Project-Kisan)

**[⭐ Star this repository](https://github.com/codeprofile/Project-Kisan)** to support AI-powered agriculture!

*Transforming farming through artificial intelligence*

</div>
