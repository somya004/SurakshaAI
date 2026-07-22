# 🦺 SurakshaAI – AI-Powered Industrial Safety Intelligence Platform

> **ET AI Hackathon 2026**
>
> **Theme:** AI for Industrial Safety & Zero-Harm Operations

---

# 📌 Overview

SurakshaAI is an AI-powered industrial safety platform designed to reduce workplace accidents by combining Machine Learning, Industrial IoT, Rule-Based Intelligence, and Real-Time Monitoring into a unified safety ecosystem.

The platform continuously analyzes worker safety, environmental conditions, equipment health, and industrial operations to identify potential hazards before accidents occur.

Our goal is to move industries from **reactive safety** to **predictive safety**.

---

# 🚀 Key Features

- 🤖 AI-Based Risk Prediction
- 📊 Real-Time Industrial Dashboard
- ⚠️ Compound Risk Engine
- 📈 ML Command Center
- 👷 Worker Safety Monitoring
- 🦺 PPE Compliance Tracking
- 🔥 Incident & Near-Miss Management
- 🏭 Zone-wise Risk Monitoring
- 📋 Permit to Work Tracking
- 🔧 Predictive Maintenance Insights
- 📉 Safety Analytics & Reports
- 📡 Industrial IoT Sensor Monitoring

---

# 🧠 AI Models

## 1. Risk Prediction Model

Predicts accident probability using multiple industrial parameters including:

- Temperature
- Gas Concentration
- Pressure
- Humidity
- Vibration
- Machine Condition
- Worker Experience
- Tool Wear
- Operational Parameters

Output:

- Risk Score
- Risk Level
- Safety Recommendations

---

## 2. Anomaly Detection Model

Detects abnormal sensor behaviour before failures occur.

Examples include:

- Sudden gas leakage
- Extreme temperature spikes
- Unusual vibration patterns
- Pressure abnormalities

---

# ⚙️ Technology Stack

## Backend

- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Uvicorn

---

## Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- Recharts

---

## Machine Learning

- Scikit-Learn
- Pandas
- NumPy
- Joblib

---

## Database

- SQLite

---

## Deployment

- Backend → Render
- Frontend → Vercel

---

# 📂 Project Structure

```
SurakshaAI
│
├── app/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── frontend/
│
├── scripts/
│
├── data/
│   ├── mock/
│   └── raw/
│
├── models_artifacts/
│
├── requirements.txt
└── README.md
```

---

# 🏗️ System Architecture

```
Industrial IoT Sensors
          │
          ▼
   Data Processing Layer
          │
          ▼
 Machine Learning Engine
          │
 ┌────────┴────────┐
 │                 │
 ▼                 ▼
Risk Prediction   Anomaly Detection
          │
          ▼
 Compound Risk Engine
          │
          ▼
 FastAPI Backend
          │
          ▼
 React + Vite Frontend
```

---

# 🔥 Core Modules

- Dashboard
- Worker Management
- Zone Monitoring
- Incident Management
- PPE Compliance
- Permit to Work
- Predictive Maintenance
- ML Command Center
- Safety Analytics

---

# 📊 ML Command Center

Provides centralized AI monitoring including:

- Model Status
- Prediction Statistics
- Risk Distribution
- Zone-wise Risk Analysis
- High-Risk Alerts
- Live Monitoring

---

# 📈 Dashboard

The dashboard provides:

- Total Workers
- Active Shifts
- Active Incidents
- High Risk Zones
- Safety Compliance
- Incident Trends
- Risk Distribution
- Recent Alerts

---

# 🔒 Safety Intelligence

SurakshaAI combines:

- AI Prediction
- Rule-Based Validation
- Historical Safety Records
- Sensor Intelligence
- Industrial Compliance

to generate accurate industrial safety recommendations.

---

# 🧪 Running Locally

## Clone Repository

```bash
git clone https://github.com/somya004/SurakshaAI.git
cd SurakshaAI
```

---

## Backend

Install dependencies

```bash
pip install -r requirements.txt
```

Run backend

```bash
uvicorn app.main:app --reload
```

Backend URL

```
http://localhost:8000
```

Swagger Docs

```
http://localhost:8000/docs
```

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend

```
http://localhost:5173
```

---

# 🌐 Deployment

## Backend

Render

```
https://surakshaai-1-ihsq.onrender.com
```

---

## Frontend

Hosted using Vercel

---

# 📌 API Documentation

Swagger UI

```
https://surakshaai-1-ihsq.onrender.com/docs
```

Health Check

```
https://surakshaai-1-ihsq.onrender.com/health
```

---

# 📊 Future Enhancements

- Live IoT Streaming
- Computer Vision PPE Detection
- Digital Twin Integration
- Predictive Maintenance using Time-Series Models
- LLM-Based Safety Assistant
- Automated Incident Investigation
- Mobile Application
- Multi-Plant Monitoring
- Edge AI Deployment

---

# 👨‍💻 Team

**SurakshaAI**

Developed for **ET AI Hackathon 2026**

---

# 📄 License

This project is developed for educational and hackathon purposes.

---

## ⭐ If you found this project useful, consider giving it a star!