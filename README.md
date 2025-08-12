# Project-Kisan - Providing farmers with expert help on demand
Project Kisan is a voice-first, multilingual AI assistant for small-scale farmers. Powered by Google AI technologies and the Gemma model, it delivers crop disease diagnosis, real-time market insights, and government scheme guidance via natural voice in local languages, working even in low-network regions.

## Major challenges faced by Indian Farmers

<img width="560" height="314" alt="image" src="https://github.com/user-attachments/assets/fd2c8e2a-db7c-41b8-a9ba-a6374cca3932" />


## Solution 

<img width="556" height="316" alt="image" src="https://github.com/user-attachments/assets/ec892371-2ce8-4d82-a710-3808f5f001bb" />


## Application

<img width="1918" height="1011" alt="image" src="https://github.com/user-attachments/assets/733e89a2-6346-479e-9b8e-7cc296a610c6" />



## ✨ Features

- **🌱 Crop Disease Diagnosis** – Vision AI–powered photo-based detection with localized remedies.  
- **📈 Real-Time Market Intelligence** – Live mandi prices & crop trends.  
- **🏛 Government Scheme Navigator** – Eligibility checks & simplified explanations.  
- **🗣 Voice-First & Multilingual** – Supports as many languages as Google ADK enables.  
- **📶 Offline Support** – Cached responses via Gemma model for low-network zones.  


## 🏗 Tech Stack

- **Frontend:** Progressive Web App (PWA), WhatsApp Integration  
- **Backend:** FastAPI, Google Cloud Run, Cloud Storage  
- **AI & ML:** Google ADK, Gemma (offline fallback), Vision AI (for crop disease detection)  
- **Integrations:** Data.Gov(AgMarknet,eNam) (market prices), Weather APIs, Government Scheme APIs (Data.gov)

## 🛠 Getting Started

```bash
# Clone the repository
git clone (https://github.com/codeprofile/Project-Kisan.git)
cd Project-Kisan

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload







