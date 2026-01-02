## Frameworks used 
Backend:- FastAPI
Frontend:- REACT.js
Caching:- redis
Database:- PostgreSQL
Auth :- Firebase Auth
Data Analysis :- Pandas,Pytorch,numpy
AI/ML:- Pytorch

## Directory structure

# Root structure 
spotify-analysis-platform/
├── backend/                # FastAPI application
├── frontend/               # React.js (Vite) application
├── ml_service/             # Dedicated folder for heavy model logic (VGGish/Llama)
├── docker-compose.yml      # Orchestrates Postgres, Redis, Backend, Frontend
└── .env.example            # Environment variables template

# Backend structure
backend/
├── app/
│   ├── api/                # Route handlers (v1, v2)
│   │   ├── endpoints/      # Specific routes (auth, analysis, social, playlist)
│   │   └── router.py       # Main router entry point
│   ├── core/               # Global config (security, config.py, logging)
│   ├── db/                 # Database connection and session management
│   │   ├── base.py         # SQLAlchemy/SQLModel base
│   │   └── session.py
│   ├── models/             # Database Schemas (SQLAlchemy/SQLModel)
│   ├── schemas/            # Pydantic models for request/response validation
│   ├── services/           # CORE BUSINESS LOGIC (Github API calls, Analysis logic)
│   │   ├── spotify_svc.py
│   │   ├── analytics_svc.py
│   │   └── ai_agent.py     # LSTM coding analysis
│   ├── crud/               # Create, Read, Update, Delete helpers
│   ├── utils/              # Helpers (caching logic with Redis, Firebase helpers)
│   └── main.py             # App entry point
├── migrations/             # Alembic database migrations
├── tests/                  # Pytest suite
└── requirements.txt

# Frontend structure
frontend/
├── src/
│   ├── assets/             # Images, fonts, icons
│   ├── components/         # Shared UI components (Buttons, Modals, Cards)
│   ├── features/           # Modular features
│   │   ├── analytics/      # Monthly/Yearly wrap components & hooks
│   │   ├── community/      # Feed, sharing, social interactions
│   │   └── recommendations/ # Recommendation engine UI
│   ├── hooks/              # Custom React hooks (useAuth, useSpotify)
│   ├── services/           # API client (Axios/TanStack Query instances)
│   ├── store/              # State management (Zustand or Redux)
│   ├── pages/              # Main route pages
│   ├── App.tsx
│   └── main.tsx
├── public/
└── tailwind.config.js

## database 
![database design](spotify_database.png)
