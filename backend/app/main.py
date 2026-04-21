from firebase_admin import credentials,initialize_app
import json
import os
from fastapi import FastAPI

from app.api.router import api_router

        
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:8085"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

path = "./serviceAccountKey.json"
cred = credentials.Certificate(path)
initialize_app(cred)

app.include_router(api_router,prefix="/api/v1")

@app.get("/")
def home():
    return {"message":"Welcome to DevLegacy Backend"}
        
