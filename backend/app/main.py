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
    allow_origins=["*"],  # For development, allow all. You can restrict to ["http://localhost:5173"] later.
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
        
